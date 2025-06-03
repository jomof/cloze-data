import os
import sys
import asyncio
import aiofiles
import queue
import time
import threading
import traceback # Keep for now, though error messages are also event-driven
import inspect
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from collections import OrderedDict # Ensure this import is present

class MapReduce:
    """
    Generic MapReduce framework for:
    - Reading files (raw content)
    - Deserializing (e.g. yaml.load)
    - Delegating to a user-provided `map_func` (may be CPU or I/O bound, sync or async)
    - Serializing (e.g. json.dumps)
    - Writing files (raw content)
    - Concurrency management:
        • Main ThreadPoolExecutor for synchronous CPU-bound tasks (deserialize, serialize, sync map)
        • Separate IO ThreadPoolExecutor for blocking file system operations in write_file
        • Asyncio for asynchronous tasks (read, async map)
    - Statistics tracking
    - Console output (progress)
    """
    CLEAR_TO_EOL   = "\u001b[K"
    MOVE_UP        = staticmethod(lambda n: f"\u001b[{n}A")
    MOVE_DOWN      = staticmethod(lambda n: f"\u001b[{n}B")
    HIDE_CURSOR    = "\u001b[?25l"
    SHOW_CURSOR    = "\u001b[?25h"
    SAVE_CURSOR    = "\u001b[s"
    RESTORE_CURSOR = "\u001b[u"
    CLEAR_DOWN     = "\u001b[J"

    DEFAULT_REFRESH_INTERVAL = 0.2
    SCAVENGING_INTERVAL = 5.0  # seconds, how often to check for old messages
    SCAVENGING_AGE_LIMIT = 15.0 # seconds, remove completed/error messages older than this

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        map_func,
        deserialize_func,
        serialize_func,
        temp_dir: str = None,
        max_threads: int = 4, # For CPU-bound tasks and sync map
        max_io_threads: int = 2, # For blocking I/O in write_file
        window_size: int = 5 
    ):
        self.input_dir        = input_dir
        self.output_dir       = output_dir
        
        self.original_map_func = map_func
        _original_deserialize_func = deserialize_func 
        _original_serialize_func = serialize_func   

        self.map_func = self._wrap_user_func(
            self.original_map_func, 
            op_name_for_key='MAP', 
            op_type_for_event='MAP', 
            action_verb='mapping'
        )
        self.deserialize_func = self._wrap_user_func(
            _original_deserialize_func, 
            op_name_for_key='CPU_DESERIALIZE', 
            op_type_for_event='CPU', 
            action_verb='deserializing'
        )
        self.serialize_func = self._wrap_user_func(
            _original_serialize_func, 
            op_name_for_key='CPU_SERIALIZE', 
            op_type_for_event='CPU', 
            action_verb='serializing'
        )

        self.temp_dir = temp_dir or os.path.join(input_dir, '.temp')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.max_threads = max_threads 
        self.max_io_threads = max_io_threads
        # Create a separate executor for I/O bound sync operations in write_file
        self.io_executor = ThreadPoolExecutor(max_workers=self.max_io_threads, thread_name_prefix='MapReduceIOThread')
        
        self.event_queue = queue.Queue()
        
        self.active_events_count = {
            'READ': 0, 'CPU': 0, 'MAP': 0, 'WRITE': 0
        }
        self.tracked_operations = OrderedDict() 
        self.window_size = window_size 

        self.counter_lock = Lock()
        self.watch_done_event = threading.Event()
        self.countdown = 0

        self.stats = {
            'count': 0, 'total_read_time': 0.0, 'total_deserialize_time': 0.0,
            'total_map_time': 0.0, 'total_serialize_time': 0.0, 'total_write_time': 0.0
        }

        self.refresh_interval = self.DEFAULT_REFRESH_INTERVAL
        self.last_scavenge_time = time.monotonic()

    def _wrap_user_func(self, original_func_to_wrap, op_name_for_key: str, op_type_for_event: str, action_verb: str):
        is_original_async = inspect.iscoroutinefunction(original_func_to_wrap)

        if is_original_async:
            async def async_wrapped_func(identifier, *args, **kwargs):
                message_key = f"{op_name_for_key}:{identifier}"
                self.event_queue.put(self._create_event(
                    message_key=message_key, text=f'🔄 {action_verb} {identifier}', status='active',
                    op_type=op_type_for_event, scope='BEGIN'
                ))
                start_time = time.perf_counter()
                result, elapsed_time = None, 0
                try:
                    result = await original_func_to_wrap(*args, **kwargs)
                    elapsed_time = time.perf_counter() - start_time
                    self.event_queue.put(self._create_event(
                        message_key=message_key, text=f'✅ {action_verb} finished for {identifier}', status='complete',
                        op_type=op_type_for_event, scope='END'
                    ))
                except Exception as e:
                    elapsed_time = time.perf_counter() - start_time
                    self.event_queue.put(self._create_event(
                        message_key=message_key, text=f'❌ error {action_verb} {identifier}: {type(e).__name__}', status='error',
                        op_type=op_type_for_event, scope='END'
                    ))
                    raise
                return result, elapsed_time
            return async_wrapped_func
        else: 
            def sync_wrapped_func(identifier, *args, **kwargs):
                message_key = f"{op_name_for_key}:{identifier}"
                self.event_queue.put(self._create_event(
                    message_key=message_key, text=f'🔄 {action_verb} {identifier}', status='active',
                    op_type=op_type_for_event, scope='BEGIN'
                ))
                start_time = time.perf_counter()
                result, elapsed_time = None, 0
                try:
                    result = original_func_to_wrap(*args, **kwargs)
                    elapsed_time = time.perf_counter() - start_time
                    self.event_queue.put(self._create_event(
                        message_key=message_key, text=f'✅ {action_verb} finished for {identifier}', status='complete',
                        op_type=op_type_for_event, scope='END'
                    ))
                except Exception as e:
                    elapsed_time = time.perf_counter() - start_time
                    self.event_queue.put(self._create_event(
                        message_key=message_key, text=f'❌ error {action_verb} {identifier}: {type(e).__name__}', status='error',
                        op_type=op_type_for_event, scope='END'
                    ))
                    raise
                return result, elapsed_time
            return sync_wrapped_func

    def _create_event(self, message_key: str, text: str, status: str, 
                      op_type: str = None, scope: str = None, is_error: bool = None) -> dict:
        if is_error is None: is_error = (status == 'error')
        event = {'time': time.monotonic(), 'message_key': message_key, 'text': text, 'status': status, 'is_error': is_error}
        if op_type: event['op_type'] = op_type
        if scope: event['scope'] = scope
        return event

    def _scavenge_tracked_operations(self): 
        now = time.monotonic()
        keys_to_remove = [
            k for k, v in list(self.tracked_operations.items()) 
            if v.get('status') in ['complete', 'error'] and (now - v.get('time', now)) > self.SCAVENGING_AGE_LIMIT]
        for key in keys_to_remove:
            if key in self.tracked_operations: del self.tracked_operations[key] 

    def _apply_event(self, event: dict):
        current_time = event.get('time', time.monotonic()) 
        op_type, scope = event.get('op_type'), event.get('scope')
        message_key, text, status = event.get('message_key'), event.get('text'), event.get('status')
        is_error = event.get('is_error', False)

        if op_type and scope and op_type in self.active_events_count:
            self.active_events_count[op_type] += 1 if scope == 'BEGIN' else -1
            if self.active_events_count[op_type] < 0: self.active_events_count[op_type] = 0

        if message_key and text:
            if is_error:
                sys.stdout.write(f"{text}{self.CLEAR_TO_EOL}\n")
                status = 'error' 
            self.tracked_operations[message_key] = {'text': text, 'time': current_time, 'status': status} 
            self.tracked_operations.move_to_end(message_key, last=False) 
            
            while len(self.tracked_operations) > self.window_size: 
                key_of_lru_finished_or_error = None
                for k, v_info in reversed(list(self.tracked_operations.items())): 
                    if v_info['status'] in ['complete', 'error']:
                        key_of_lru_finished_or_error = k
                        break 
                
                if key_of_lru_finished_or_error:
                    del self.tracked_operations[key_of_lru_finished_or_error] 
                else:
                    self.tracked_operations.popitem(last=True) 

    def _do_redraw(self):
        lines = [self.SAVE_CURSOR]
        clear_to_eol, now = self.CLEAR_TO_EOL, time.monotonic()
        
        all_items_oldest_updated_first = list(reversed(list(self.tracked_operations.values())))

        candidate_finished_lines = []
        candidate_active_lines = []

        for item_info in all_items_oldest_updated_first: 
            display_text = item_info['text']
            msg_time = item_info['time']
            status = item_info.get('status')
            line_to_add = f"  {display_text}" 

            if status == 'active':
                elapsed = now - msg_time
                if elapsed > 1.0: line_to_add += f" ({elapsed:.1f}s)"
                line_to_add += clear_to_eol + "\n"
                candidate_active_lines.append(line_to_add) 
            elif status in ['complete', 'error']:
                line_to_add += clear_to_eol + "\n"
                candidate_finished_lines.append(line_to_add) 

        final_display_lines_for_area = []
        slots_available = self.window_size

        active_lines_to_show = candidate_active_lines[:slots_available]
        
        slots_for_finished_at_top = slots_available - len(active_lines_to_show)
        
        finished_lines_to_display_at_top = []
        if slots_for_finished_at_top > 0:
            finished_lines_to_display_at_top = candidate_finished_lines[:slots_for_finished_at_top]
        
        final_display_lines_for_area.extend(finished_lines_to_display_at_top)
        final_display_lines_for_area.extend(active_lines_to_show)
        
        lines.extend(final_display_lines_for_area)
        
        num_messages_actually_shown = len(final_display_lines_for_area)
        for _ in range(max(0, self.window_size - num_messages_actually_shown)):
            lines.append(f"  {clear_to_eol}\n")

        lines.extend([
            f"Reading   {self.active_events_count['READ']} files{clear_to_eol}\n",
            f"CPU tasks {self.active_events_count['CPU']} active{clear_to_eol}\n",
            f"Map calls {self.active_events_count['MAP']} active{clear_to_eol}\n",
            f"Writing   {self.active_events_count['WRITE']} files{clear_to_eol}\n",
            f"{self.countdown} work items remaining{clear_to_eol}\n",
            self.RESTORE_CURSOR])
        sys.stdout.write(''.join(lines))

    def watcher_loop(self):
        refresh_interval, half_interval = self.refresh_interval, self.refresh_interval / 2.0
        last_redraw = time.monotonic() - refresh_interval
        while True:
            now = time.monotonic()
            if now - self.last_scavenge_time >= self.SCAVENGING_INTERVAL:
                self._scavenge_tracked_operations(); self.last_scavenge_time = now 
            try: event = self.event_queue.get(timeout=half_interval)
            except queue.Empty:
                if now - last_redraw >= refresh_interval: self._do_redraw(); last_redraw = now
                continue
            if isinstance(event, str) and event == 'DONE':
                self._do_redraw(); sys.stdout.write(self.CLEAR_DOWN); self.watch_done_event.set(); break
            if isinstance(event, dict): self._apply_event(event)
            while True: 
                try: extra_event = self.event_queue.get_nowait()
                except queue.Empty: break
                if isinstance(extra_event, str) and extra_event == 'DONE':
                    self._do_redraw(); sys.stdout.write(self.CLEAR_DOWN); self.watch_done_event.set(); return
                if isinstance(extra_event, dict): self._apply_event(extra_event)
            if now - last_redraw >= refresh_interval: self._do_redraw(); last_redraw = now
        
    async def read_file(self, file_path: str): 
        basename = os.path.basename(file_path)
        message_key = f'READ:{basename}'
        raw_content, elapsed = None, 0
        self.event_queue.put(self._create_event(message_key, f'🔄 reading {basename}', 'active', 'READ', 'BEGIN'))
        try:
            start = time.perf_counter()
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f: raw_content = await f.read()
            elapsed = time.perf_counter() - start
            self.event_queue.put(self._create_event(message_key, f'✅ read {basename}', 'complete', 'READ', 'END'))
        except Exception as e:
            elapsed = time.perf_counter() - start if 'start' in locals() else 0
            self.event_queue.put(self._create_event(message_key, f'❌ error reading {basename}: {type(e).__name__}', 'error', 'READ', 'END'))
            raise 
        return raw_content, elapsed

    async def write_file(self, file_path: str, raw_content: str): 
        basename = os.path.basename(file_path)
        message_key = f'WRITE:{basename}'
        tmp_path = os.path.join(self.temp_dir, f".{basename}.tmp")
        elapsed = 0
        self.event_queue.put(self._create_event(message_key, f'🔄 writing {basename}', 'active', 'WRITE', 'BEGIN'))
        try:
            start = time.perf_counter()
            async with aiofiles.open(tmp_path, 'w', encoding='utf-8') as tmp_f: await tmp_f.write(raw_content)
            # Use the dedicated IO executor for os.replace
            await asyncio.get_event_loop().run_in_executor(self.io_executor, os.replace, tmp_path, file_path)
            elapsed = time.perf_counter() - start
            self.event_queue.put(self._create_event(message_key, f'✅ wrote {basename}', 'complete', 'WRITE', 'END'))
        except Exception as e:
            elapsed = time.perf_counter() - start if 'start' in locals() else 0
            self.event_queue.put(self._create_event(message_key, f'❌ error writing {basename}: {type(e).__name__}', 'error', 'WRITE', 'END'))
            raise
        finally:
            if os.path.exists(tmp_path):
                try: 
                    # Use the dedicated IO executor for os.remove
                    await asyncio.get_event_loop().run_in_executor(self.io_executor, os.remove, tmp_path)
                except Exception: pass 
        return elapsed 

    async def _execute_map_operation(self, deserialized, input_file_path: str, output_basename: str, executor: ThreadPoolExecutor):
        # executor here is the main ThreadPoolExecutor for CPU/sync map tasks
        processed_obj, mpt = None, 0
        if inspect.iscoroutinefunction(self.original_map_func): 
            processed_obj, mpt = await self.map_func(output_basename, deserialized, input_file_path)
        else:
            processed_obj, mpt = await asyncio.get_event_loop().run_in_executor(
                executor, self.map_func, output_basename, deserialized, input_file_path)
        return processed_obj, mpt

    async def process_one(self, input_file_path: str, output_file_path: str, executor: ThreadPoolExecutor):
        input_basename = os.path.basename(input_file_path)
        output_basename = os.path.basename(output_file_path) 
        try:
            raw_content, read_time = await self.read_file(input_file_path)
            self.stats['total_read_time'] += read_time

            deserialized_obj, dt = await asyncio.get_event_loop().run_in_executor(
                executor, self.deserialize_func, input_basename, raw_content)
            self.stats['total_deserialize_time'] += dt
            
            processed_obj, mpt = await self._execute_map_operation(
                deserialized_obj, input_file_path, output_basename, executor)
            self.stats['total_map_time'] += mpt
            
            final_str, st = await asyncio.get_event_loop().run_in_executor(
                executor, self.serialize_func, output_basename, processed_obj)
            self.stats['total_serialize_time'] += st

            write_time = await self.write_file(output_file_path, final_str)
            self.stats['total_write_time'] += write_time

            self.stats['count'] += 1
            self.event_queue.put(self._create_event(
                f'FINISH:{input_basename}', f'✅ processed {input_basename}', 'complete'))
        except Exception as e:
            self.event_queue.put(self._create_event(
                f'ERROR_PROCESS:{input_basename}', f'❌ error processing {input_basename}: {type(e).__name__}','error', is_error=True))
        finally:
            with self.counter_lock: self.countdown -= 1

    async def run(self):
        sys.stdout.write(self.HIDE_CURSOR)
        # Main executor for CPU-bound tasks and sync map
        # IO executor is created in __init__ and shut down in finally
        main_executor = ThreadPoolExecutor(max_workers=self.max_threads, thread_name_prefix='MapReduceMainThread')
        try:
            all_input_files = [
                os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir)
                if os.path.isfile(os.path.join(self.input_dir, f))
            ] if os.path.isdir(self.input_dir) else []

            if not os.path.isdir(self.input_dir):
                self.event_queue.put(self._create_event('INIT_ERROR', f'❌ Input directory not found: {self.input_dir}', 'error'))
            
            total_files = len(all_input_files)
            self.countdown = total_files

            if total_files == 0 and os.path.isdir(self.input_dir):
                 self.event_queue.put(self._create_event('NO_FILES', 'ℹ️ No files found to process.', 'log'))

            watcher_thread = threading.Thread(target=self.watcher_loop, daemon=True); watcher_thread.start()
            
            if not all_input_files : 
                self.event_queue.put('DONE'); self.watch_done_event.wait()
                sys.stdout.write(f"Files total:               {total_files}\n")
                sys.stdout.write(f"Processed (successfully):  {self.stats['count']}\n")
                sys.stdout.write(f"Attempted to process:      0\n")
                sys.stdout.write(f"Total elapsed:             0.00s\n")
                return

            start_all = time.perf_counter()
            
            tasks = []
            for fpath in all_input_files: 
                out_path = os.path.join(self.output_dir, os.path.basename(fpath))
                os.makedirs(os.path.dirname(out_path), exist_ok=True) 
                # Pass the main_executor to process_one
                tasks.append(asyncio.create_task(self.process_one(fpath, out_path, main_executor)))
            
            processed_tasks_count = 0
            for task_future in asyncio.as_completed(tasks):
                try: await task_future 
                except Exception: pass 
                finally: processed_tasks_count +=1

            self.event_queue.put('DONE'); self.watch_done_event.wait()
            total_elapsed = time.perf_counter() - start_all
            count = self.stats['count']
            sys.stdout.write(f"Files total:               {total_files}\n")
            sys.stdout.write(f"Processed (successfully):  {count}\n")
            sys.stdout.write(f"Attempted to process:      {processed_tasks_count}\n")
            sys.stdout.write(f"Total elapsed:             {total_elapsed:.2f}s\n")
            if count > 0:
                for op_name_stat in ['read', 'deserialize', 'map', 'serialize', 'write']:
                    total_time_stat = self.stats[f'total_{op_name_stat}_time']
                    avg_time_stat = (total_time_stat / count) if count else 0
                    sys.stdout.write(f"{op_name_stat.capitalize():<12} total: {total_time_stat:>10.2f}s  (avg {avg_time_stat:.2f}s)\n")
        finally:
            # Shut down both executors
            if 'main_executor' in locals() and main_executor: # Check if it was created
                main_executor.shutdown(wait=True)
            if hasattr(self, 'io_executor') and self.io_executor: # Check if it was created
                self.io_executor.shutdown(wait=True)
            sys.stdout.write(self.SHOW_CURSOR)
