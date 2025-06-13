import asyncio
import inspect
import os
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from threading import Lock

import aiofiles
import yaml

from python.console import display

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

def str_presenter(dumper, data):
    # If the string has newline characters, use block style
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(str, str_presenter, Dumper=MyDumper)
yaml.add_representer(OrderedDict, dict_representer, Dumper=MyDumper)
yaml.add_constructor('tag:yaml.org,2002:map', dict_constructor, Loader=yaml.Loader)

def dump_yaml(data):
    return yaml.dump(data, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)

def dump_yaml_file(data, file):
    return yaml.dump(data, file, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)
        

class MapReduce:
    """
    Generic MapReduce framework with optional reduce (fold) functionality.
    As each result from map_func (or original object if skipped) is ready, it is passed to fold_func
    along with the current accumulator. Folding is guaranteed sequential and single-threaded by using
    an asyncio.Lock to serialize access.
    """
    def __init__(
        self,
        input_dir: str,

        deserialize_func=lambda raw: yaml.load(raw, Loader=yaml.CSafeLoader),

        preprocess_func=None,

        map_func_name: str = 'mapping',
        map_func = None,
        map_inproc = None,  

        fold_func_name: str = 'folding',
        fold_func=None,

        serialize_func=lambda raw: dump_yaml(raw),

        output_dir: str = None,
        initial_accumulator=None,
        temp_dir: str = None,
        max_threads: int = 4
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.deserialize_func = deserialize_func
        self.preprocess_func = preprocess_func
        if isinstance(map_func, dict):
            # Process dict to auto-detect async functions when in_proc not explicitly set
            self.map_func = {}
            for name, config in map_func.items():
                if isinstance(config, dict) and 'func' in config:
                    func = config['func']
                    # Validate: async functions cannot run out-of-process
                    if config.get('in_proc') is False and inspect.iscoroutinefunction(func):
                        raise ValueError(f"Async function '{name}' cannot run with in_proc=False. Async functions require in_proc=True.")
                    # Only auto-detect async if in_proc not explicitly specified
                    elif 'in_proc' not in config and inspect.iscoroutinefunction(func):
                        self.map_func[name] = {**config, 'in_proc': True}
                    else:
                        self.map_func[name] = config
                else:
                    self.map_func[name] = config
        elif map_func is not None:
            # Validate: async functions cannot run out-of-process
            if map_inproc is False and inspect.iscoroutinefunction(map_func):
                raise ValueError(f"Async function cannot run with in_proc=False. Async functions require in_proc=True.")
            # Determine in_proc: explicit value, or auto-detect async, or default False
            if map_inproc is not None:
                inproc_value = map_inproc
            elif inspect.iscoroutinefunction(map_func):
                inproc_value = True
            else:
                inproc_value = False
            self.map_func = { map_func_name: { 'func': map_func, 'in_proc': inproc_value } }
        else:
            self.map_func = { }

        self.serialize_func = serialize_func
        self.fold_func_name = fold_func_name
        self.fold_func = fold_func
        self.accumulator = initial_accumulator

        self.temp_dir = temp_dir or os.path.join(input_dir, '.temp')
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
        except FileNotFoundError:
            pass

        self.max_threads = max_threads
        self.max_io_threads = self.max_threads
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_io_threads, thread_name_prefix='MapReduceIOThread')
        self.process_executor = ProcessPoolExecutor(max_workers=self.max_threads)

        self.counter_lock = Lock()
        self.countdown = 0
        self.run_state = 'running'  # 'running' -> 'cancelling'
        self.shutdown_event = None  # will be initialized in run()

        # Lock to ensure fold is single-threaded
        self.fold_lock = None  # will be initialized in run()

        self.result = {
            "files-written": 0
         }

    async def _shutdown_executors(self):
        """Properly shutdown executors"""
        # Cancel futures and shutdown (don't wait initially)
            # Always clean up

        self.process_executor.shutdown(wait=False, cancel_futures=True)
        self.thread_executor.shutdown(wait=False, cancel_futures=True)

    async def process_one(self, input_file_path: str, output_file_path: str):
        basename = os.path.basename(input_file_path)
        original_obj = None
        result_item = None

        try:
            # Read the input file
            async with self.read_semaphore:
                async with aiofiles.open(input_file_path, "r", encoding="utf-8") as f:
                    original_content = await f.read()

                # Deserialize
                deserialized = self.deserialize_func(original_content)
                original_obj = deserialized  # Keep original for fold if preprocess returns None

            # Preprocess if applicable
            if self.preprocess_func:
                async with self.preprocess_semaphore:
                    with display.work(basename, 'preprocessing'):
                        deserialized = self.preprocess_func(deserialized, input_file_path)
                    if deserialized is None:
                        result_item = original_obj
                        # Skip map/write, but proceed to fold
                    
            # If preprocess did not skip, do map and write
            if result_item is None:
                if not self.map_func:
                    result_item = original_obj
                else:
                    async with self.map_semaphore:
                        processed = deserialized  # Start with deserialized object
                        for map_func_name in self.map_func:
                            map_inproc = self.map_func[map_func_name].get('in_proc', False)
                            map_func = self.map_func[map_func_name]['func']
                        
                            if processed:
                                with display.work(basename, map_func_name):
                                    try:
                                        if map_inproc:
                                            if inspect.iscoroutinefunction(map_func):
                                                processed = await map_func(processed, input_file_path)
                                            else:
                                                display.warn(f"Sync map function '{map_func_name}' will run in-process, which may block the event loop.")
                                                processed = map_func(processed, input_file_path)
                                        else:
                                            # Only check state before expensive executor work
                                            if self.run_state != 'running':
                                                return None
                                            processed = await asyncio.get_running_loop().run_in_executor(
                                                self.process_executor,
                                                map_func,
                                                processed,
                                                input_file_path)
                                    except Exception as e:
                                        display.error(f"{map_func_name} {basename}: {e}")
                                        raise

                    # Serialize the processed data and write to temp file
                    if processed is not None:
                        final_content = self.serialize_func(processed)
                        if final_content != original_content:
                            if self.input_dir == self.output_dir:
                                # Input is same as output, so we need to write to a temp file
                                with display.work(basename, 'replacing'):
                                    os.makedirs(self.temp_dir, exist_ok=True)
                                    tmp_path = os.path.join(self.temp_dir, f".{basename}.tmp")
                                    async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
                                        await f.write(final_content)
                                    # Replace output file
                                    try:
                                        os.remove(output_file_path)
                                    except FileNotFoundError:
                                        pass
                                    os.replace(tmp_path, output_file_path)

                                    self.result['files-written'] = self.result.get('files-written', 0) + 1
                            else:
                                if self.output_dir:
                                    raise ValueError("TODO support writing to different output directory")
                        result_item = processed
                    else:
                        result_item = original_obj

            # If fold_func is defined, do fold immediately, serialized by fold_lock
            if self.fold_func and result_item is not None:
                # Ensure only one fold at a time
                async with self.fold_lock:
                    with display.work(basename, self.fold_func_name):
                        self.accumulator = self.fold_func(self.accumulator, result_item)

            return result_item
        finally:
            # Update the countdown
            with self.counter_lock:
                self.countdown -= 1
                display.update_countdown(self.countdown)

    async def run(self):
        self.read_semaphore = asyncio.Semaphore(self.max_threads)
        self.preprocess_semaphore = asyncio.Semaphore(self.max_threads)
        self.map_semaphore = asyncio.Semaphore(self.max_threads)
        self.fold_lock = asyncio.Lock()

        display.start()

        # Gather input files
        if not os.path.isdir(self.input_dir):
            display.error('INIT_ERROR', f"Input directory not found: {self.input_dir}")
            all_input_files = []
            total = 0
        else:
            all_input_files = [os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir)
                                if os.path.isfile(os.path.join(self.input_dir, f))]
            total = len(all_input_files)

        with self.counter_lock:
            self.countdown = total
        display.update_countdown(self.countdown)

        if total == 0 and os.path.isdir(self.input_dir):
            display.warn('No files found to process')

        try:
            tasks = []
            for fpath in all_input_files:
                out_path = None
                if self.output_dir:
                    out_path = os.path.join(self.output_dir, os.path.basename(fpath))
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                task = asyncio.create_task(self.process_one(fpath, out_path))
                tasks.append(task)

            # Wait for all tasks to complete; folding happens inside process_one
            for fut in asyncio.as_completed(tasks):
                await fut
                    
            # Write the accumulator if we completed successfully
            if self.run_state == 'running' and self.fold_func and self.accumulator is not None:
                serialized_accumulator = self.serialize_func(self.accumulator)
                accumulator_output_dir = os.path.join(self.output_dir, 'summary')
                os.makedirs(accumulator_output_dir, exist_ok=True)
                accumulator_output_path = os.path.join(accumulator_output_dir, 'summary.json')
                async with aiofiles.open(accumulator_output_path, "w", encoding="utf-8") as f:
                    await f.write(serialized_accumulator)

            return self.result
            
        finally:
            await self._shutdown_executors()