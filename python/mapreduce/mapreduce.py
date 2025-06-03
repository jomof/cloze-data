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
    - Concurrency management via separate semaphores:
        • sem_read      for limiting concurrent file reads
        • sem_cpu       for limiting concurrent CPU-bound tasks (managed by ThreadPoolExecutor)
        • sem_map       for limiting concurrent map_func calls
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
        max_concurrent_reads: int = 5,
        max_concurrent_cpu: int = 2,
        max_concurrent_map: int = 5,
        mru_size: int = 5  # Now applies to displayed_messages_info
    ):
        self.input_dir        = input_dir
        self.output_dir       = output_dir
        self.map_func         = map_func
        self.deserialize_func = deserialize_func
        self.serialize_func   = serialize_func

        self.temp_dir = temp_dir or os.path.join(input_dir, '.temp')
        os.makedirs(self.temp_dir, exist_ok=True)

        self.max_concurrent_reads = max_concurrent_reads
        self.sem_read = None
        self.max_concurrent_cpu = max_concurrent_cpu
        self.sem_cpu = None 
        self.max_concurrent_map = max_concurrent_map
        self.sem_map = None

        self.event_queue = queue.Queue()
        
        self.active_events_count = {
            'READ': 0,
            'CPU': 0,
            'MAP': 0,
            'WRITE': 0
        }
        self.displayed_messages_info = OrderedDict()
        self.mru_size = mru_size

        self.counter_lock = Lock()
        self.watch_done_event = threading.Event()
        self.countdown = 0

        self.stats = {
            'count': 0,
            'total_read_time': 0.0,
            'total_deserialize_time': 0.0,
            'total_map_time': 0.0,
            'total_serialize_time': 0.0,
            'total_write_time': 0.0
        }

        self.refresh_interval = self.DEFAULT_REFRESH_INTERVAL
        self.last_scavenge_time = time.monotonic()

    def _create_event(self, message_key: str, text: str, status: str, 
                      op_type: str = None, scope: str = None, is_error: bool = None) -> dict:
        """
        Helper function to create a standardized event dictionary.
        """
        if is_error is None:
            is_error = (status == 'error')
        
        event = {
            'time': time.monotonic(),
            'message_key': message_key,
            'text': text,
            'status': status,
            'is_error': is_error
        }
        if op_type:
            event['op_type'] = op_type
        if scope:
            event['scope'] = scope
        return event

    def _scavenge_completed_messages(self):
        """Remove old completed or error messages from the display queue."""
        now = time.monotonic()
        keys_to_remove = []
        for key, info in list(self.displayed_messages_info.items()): 
            if info.get('status') in ['complete', 'error']:
                if (now - info.get('time', now)) > self.SCAVENGING_AGE_LIMIT:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key in self.displayed_messages_info: 
                del self.displayed_messages_info[key]

    def _apply_event(self, event: dict):
        """
        Update counters and displayed messages based on an event dictionary.
        """
        current_time = event.get('time', time.monotonic()) 

        op_type = event.get('op_type')
        scope = event.get('scope')
        message_key = event.get('message_key')
        text = event.get('text')
        status = event.get('status') 
        is_error = event.get('is_error', False)

        if op_type and scope and op_type in self.active_events_count:
            if scope == 'BEGIN':
                self.active_events_count[op_type] += 1
            elif scope == 'END':
                self.active_events_count[op_type] -= 1
                if self.active_events_count[op_type] < 0:
                    pass 

        if message_key and text:
            if is_error:
                sys.stdout.write(f"{text}{self.CLEAR_TO_EOL}\n")
                status = 'error' 
            
            self.displayed_messages_info[message_key] = {
                'text': text, 
                'time': current_time, 
                'status': status     
            }
            self.displayed_messages_info.move_to_end(message_key, last=False)

            while len(self.displayed_messages_info) > self.mru_size:
                self.displayed_messages_info.popitem(last=True)

    def _do_redraw(self):
        """Draw the current status lines to stdout in one batched write."""
        lines = [self.SAVE_CURSOR]
        clear_to_eol = self.CLEAR_TO_EOL
        now = time.monotonic() 

        messages_to_display = list(self.displayed_messages_info.values())
        messages_to_display.reverse() 

        num_messages_shown = 0
        for item_info in messages_to_display:
            display_text = item_info['text'] 
            message_time = item_info['time']
            status = item_info.get('status')

            if status == 'active':
                elapsed = now - message_time
                if elapsed > 1.0:
                    display_text += f" ({elapsed:.1f}s)" 
            
            lines.append(f"  {display_text}{clear_to_eol}\n")
            num_messages_shown += 1
        
        for _ in range(max(0, self.mru_size - num_messages_shown)):
            lines.append(f"  {clear_to_eol}\n")

        reads = self.active_events_count['READ']
        procs = self.active_events_count['CPU']
        maps  = self.active_events_count['MAP']
        writes = self.active_events_count['WRITE']
        countdown = self.countdown 

        lines.append(f"Reading   {reads} files{clear_to_eol}\n")
        lines.append(f"CPU tasks {procs} active{clear_to_eol}\n")
        lines.append(f"Map calls {maps} active{clear_to_eol}\n")
        lines.append(f"Writing   {writes} files{clear_to_eol}\n")
        lines.append(f"{countdown} work items remaining{clear_to_eol}\n")
        lines.append(self.RESTORE_CURSOR)

        sys.stdout.write(''.join(lines))

    def watcher_loop(self):
        """Runs on a separate thread, updating console on events with throttled redraws."""
        refresh_interval = self.refresh_interval 
        half_interval = refresh_interval / 2.0 
        last_redraw = time.monotonic() - refresh_interval

        while True:
            now_loop = time.monotonic() # Renamed to avoid conflict with 'now' in _do_redraw if called from here

            if now_loop - self.last_scavenge_time >= self.SCAVENGING_INTERVAL:
                self._scavenge_completed_messages()
                self.last_scavenge_time = now_loop

            try:
                event = self.event_queue.get(timeout=half_interval)
            except queue.Empty: 
                if now_loop - last_redraw >= refresh_interval:
                    self._do_redraw()
                    last_redraw = now_loop
                continue 

            if isinstance(event, str) and event == 'DONE':
                self._do_redraw() 
                sys.stdout.write(self.CLEAR_DOWN) 
                self.watch_done_event.set() 
                break 

            if isinstance(event, dict):
                 self._apply_event(event)

            while True:
                try:
                    extra_event = self.event_queue.get_nowait()
                    if isinstance(extra_event, str) and extra_event == 'DONE':
                        self._do_redraw() 
                        sys.stdout.write(self.CLEAR_DOWN)
                        self.watch_done_event.set()
                        return 

                    if isinstance(extra_event, dict):
                        self._apply_event(extra_event)

                except queue.Empty:
                    break 

            if now_loop - last_redraw >= refresh_interval:
                self._do_redraw()
                last_redraw = now_loop
        
    async def read_file(self, file_path: str):
        basename = os.path.basename(file_path)
        message_key = f'READ:{basename}'
        
        raw_content = None
        elapsed = 0
        async with self.sem_read: 
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'🔄 reading {basename}', status='active',
                op_type='READ', scope='BEGIN'
            ))
            try:
                start = time.perf_counter()
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = await f.read()
                elapsed = time.perf_counter() - start
                self.event_queue.put(self._create_event(
                    message_key=message_key, text=f'✅ read {basename}', status='complete',
                    op_type='READ', scope='END'
                ))
            except Exception as e:
                elapsed = time.perf_counter() - start 
                self.event_queue.put(self._create_event(
                    message_key=message_key, text=f'❌ error reading {basename}: {type(e).__name__}', 
                    status='error', op_type='READ', scope='END' 
                ))
                raise 
        return raw_content, elapsed

    async def write_file(self, file_path: str, raw_content: str):
        basename = os.path.basename(file_path)
        message_key = f'WRITE:{basename}'
        
        tmp_path = os.path.join(self.temp_dir, f".{basename}.tmp")
        elapsed = 0
        
        self.event_queue.put(self._create_event(
            message_key=message_key, text=f'🔄 writing {basename}', status='active',
            op_type='WRITE', scope='BEGIN'
        ))
        try:
            start = time.perf_counter()
            async with aiofiles.open(tmp_path, 'w', encoding='utf-8') as tmp_f:
                await tmp_f.write(raw_content)
            await asyncio.to_thread(os.replace, tmp_path, file_path)
            elapsed = time.perf_counter() - start
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'✅ wrote {basename}', status='complete',
                op_type='WRITE', scope='END'
            ))
        except Exception as e:
            elapsed = time.perf_counter() - start if 'start' in locals() else 0
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'❌ error writing {basename}: {type(e).__name__}', 
                status='error', op_type='WRITE', scope='END' 
            ))
            raise
        finally:
            if os.path.exists(tmp_path):
                try:
                    await asyncio.to_thread(os.remove, tmp_path)
                except Exception:
                    pass 
            return elapsed 

    # Original CPU-bound methods (now private, called by wrappers)
    def _cpu_bound_deserialize(self, raw_content: str):
        start_d = time.perf_counter()
        deserialized = self.deserialize_func(raw_content)
        dt = time.perf_counter() - start_d
        return deserialized, dt

    def _cpu_bound_serialize(self, processed_obj):
        start_s = time.perf_counter()
        final_str = self.serialize_func(processed_obj)
        st = time.perf_counter() - start_s
        return final_str, st

    # Wrapper methods for execution in ThreadPoolExecutor, handling their own events
    def _execute_cpu_bound_deserialize_wrapper(self, raw_content: str, input_basename: str):
        message_key = f'CPU_DESERIALIZE:{input_basename}'
        self.event_queue.put(self._create_event(
            message_key=message_key, text=f'🔄 deserializing {input_basename}', status='active',
            op_type='CPU', scope='BEGIN'
        ))
        try:
            deserialized, dt = self._cpu_bound_deserialize(raw_content)
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'✅ deserialized {input_basename}', status='complete',
                op_type='CPU', scope='END'
            ))
            return deserialized, dt
        except Exception as e:
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'❌ error deserializing {input_basename}: {type(e).__name__}', status='error',
                op_type='CPU', scope='END' # Still send END for counter
            ))
            raise # Re-raise to be caught by process_one's main try-except

    def _execute_cpu_bound_serialize_wrapper(self, processed_obj, output_basename: str):
        message_key = f'CPU_SERIALIZE:{output_basename}'
        self.event_queue.put(self._create_event(
            message_key=message_key, text=f'🔄 serializing {output_basename}', status='active',
            op_type='CPU', scope='BEGIN'
        ))
        try:
            final_str, st = self._cpu_bound_serialize(processed_obj)
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'✅ serialized {output_basename}', status='complete',
                op_type='CPU', scope='END'
            ))
            return final_str, st
        except Exception as e:
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'❌ error serializing {output_basename}: {type(e).__name__}', status='error',
                op_type='CPU', scope='END' # Still send END for counter
            ))
            raise

    def _execute_sync_map_func_wrapper(self, deserialized, input_file_path: str, output_basename: str):
        message_key = f'MAP:{output_basename}' # Corrected: This was key_map before, which is not defined here.
        map_type_str = "sync map" 
        self.event_queue.put(self._create_event(
            message_key=message_key, text=f'🔄 {map_type_str} {output_basename}', status='active', # Corrected: Use message_key
            op_type='MAP', scope='BEGIN'
        ))
        try:
            start_m = time.perf_counter()
            # Call the original user-provided synchronous map_func
            processed_obj = self.map_func(deserialized, input_file_path)
            mpt = time.perf_counter() - start_m
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'✅ finished map {output_basename}', status='complete', 
                op_type='MAP', scope='END'
            ))
            return processed_obj, mpt
        except Exception as e:
            self.event_queue.put(self._create_event(
                message_key=message_key, text=f'❌ error in map {output_basename}: {type(e).__name__}', status='error',
                op_type='MAP', scope='END' # Still send END for counter
            ))
            raise


    async def process_one(self, input_file_path: str, output_file_path: str, executor: ThreadPoolExecutor):
        input_basename = os.path.basename(input_file_path)
        output_basename = os.path.basename(output_file_path) 
        
        try:
            # Read (handles its own BEGIN/END events internally)
            raw_content, read_time = await self.read_file(input_file_path)
            self.stats['total_read_time'] += read_time

            # Deserialize (uses wrapper for events)
            deserialized, dt = await asyncio.get_event_loop().run_in_executor(
                executor, self._execute_cpu_bound_deserialize_wrapper, raw_content, input_basename
            )
            self.stats['total_deserialize_time'] += dt

            # Map
            processed_obj = None
            mpt = 0 # Initialize map processing time

            if inspect.iscoroutinefunction(self.map_func):
                # Async map_func: events are handled here, after semaphore
                key_map_async = f'MAP:{output_basename}' # Use a distinct variable name for clarity
                map_type_str = "async map"
                async with self.sem_map: 
                    self.event_queue.put(self._create_event(
                        message_key=key_map_async, text=f'🔄 {map_type_str} {output_basename}', status='active',
                        op_type='MAP', scope='BEGIN'
                    ))
                    start_m = time.perf_counter()
                    processed_obj = await self.map_func(deserialized, input_file_path)
                    mpt = time.perf_counter() - start_m
                    self.event_queue.put(self._create_event(
                        message_key=key_map_async, text=f'✅ finished map {output_basename}', status='complete', 
                        op_type='MAP', scope='END'
                    ))
            else:
                # Sync map_func: uses wrapper for events, semaphore acquired before calling executor
                async with self.sem_map:
                    # The wrapper _execute_sync_map_func_wrapper will handle BEGIN/END events
                    processed_obj, mpt = await asyncio.get_event_loop().run_in_executor(
                        executor, self._execute_sync_map_func_wrapper, deserialized, input_file_path, output_basename
                    )
            self.stats['total_map_time'] += mpt
            
            # Serialize (uses wrapper for events)
            final_str, st = await asyncio.get_event_loop().run_in_executor(
                executor, self._execute_cpu_bound_serialize_wrapper, processed_obj, output_basename
            )
            self.stats['total_serialize_time'] += st

            # Write (handles its own BEGIN/END events internally)
            write_time = await self.write_file(output_file_path, final_str)
            self.stats['total_write_time'] += write_time

            self.stats['count'] += 1
            self.event_queue.put(self._create_event(
                message_key=f'FINISH:{input_basename}', 
                text=f'✅ processed {input_basename}', 
                status='complete'
            ))

        except Exception as e:
            # General error for the whole process_one if something fails outside specific wrappers
            # or if wrappers re-raise.
            self.event_queue.put(self._create_event(
                message_key=f'ERROR_PROCESS:{input_basename}', 
                text=f'❌ error processing {input_basename}: {type(e).__name__}',
                status='error', is_error=True # Ensure it's printed immediately
            ))
            # No re-raise here, allow run() to count it as an attempted task.
            # The error is logged. If re-raised, asyncio.as_completed would catch it.
            # For now, let's log and continue with other files.
        finally:
            with self.counter_lock:
                self.countdown -= 1

    async def run(self):
        """Execute the full workflow: spawn watcher, dispatch tasks, report stats."""
        self.sem_read = asyncio.Semaphore(self.max_concurrent_reads)
        self.sem_cpu  = asyncio.Semaphore(self.max_concurrent_cpu) 
        self.sem_map  = asyncio.Semaphore(self.max_concurrent_map)

        sys.stdout.write(self.HIDE_CURSOR)
        try:
            all_input_files = []
            if os.path.isdir(self.input_dir):
                all_input_files = [
                    os.path.join(self.input_dir, fname)
                    for fname in os.listdir(self.input_dir)
                    if os.path.isfile(os.path.join(self.input_dir, fname))
                ]
            else:
                self.event_queue.put(self._create_event(
                    message_key='INIT_ERROR',
                    text=f'❌ Input directory not found: {self.input_dir}',
                    status='error'
                ))

            total_files = len(all_input_files)
            self.countdown = total_files

            if total_files == 0 and not os.path.isdir(self.input_dir) : 
                 pass 
            elif total_files == 0:
                self.event_queue.put(self._create_event(
                    message_key='NO_FILES',
                    text='ℹ️ No files found to process.',
                    status='log'
                ))

            watcher_thread = threading.Thread(target=self.watcher_loop, daemon=True)
            watcher_thread.start()
            
            if total_files == 0: 
                self.event_queue.put('DONE')
                self.watch_done_event.wait() 
                
                sys.stdout.write(f"Files total:               {total_files}\n")
                sys.stdout.write(f"Processed (successfully):  {self.stats['count']}\n")
                sys.stdout.write(f"Attempted to process:      0\n") 
                sys.stdout.write(f"Total elapsed:             0.00s\n")
                return 

            start_all = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=self.max_concurrent_cpu) as executor: 
                tasks = []
                for fpath in all_input_files:
                    out_path = os.path.join(self.output_dir, os.path.basename(fpath))
                    os.makedirs(os.path.dirname(out_path), exist_ok=True) 
                    tasks.append(
                        # Create task for process_one, which now uses wrappers for executor calls
                        asyncio.create_task(
                            self.process_one(fpath, out_path, executor)
                        )
                    )
                
                processed_tasks_count = 0 
                # Wait for all tasks to complete. Exceptions in process_one are handled there
                # and should not propagate here to stop the as_completed loop,
                # allowing all files to be attempted.
                for task_future in asyncio.as_completed(tasks):
                    try:
                        await task_future # Await to ensure task completion and catch unexpected errors
                    except Exception:
                        # This should ideally not be reached if process_one handles its exceptions.
                        # If it is, it means an unhandled error occurred in process_one's structure.
                        # The error would have been logged by process_one's general catch-all.
                        pass 
                    finally:
                        processed_tasks_count +=1


            self.event_queue.put('DONE') 
            self.watch_done_event.wait() 

            total_elapsed = time.perf_counter() - start_all
            count = self.stats['count'] 
            avg_read = (self.stats['total_read_time'] / count) if count else 0
            avg_deserialize = (self.stats['total_deserialize_time'] / count) if count else 0
            avg_map = (self.stats['total_map_time'] / count) if count else 0
            avg_serialize = (self.stats['total_serialize_time'] / count) if count else 0
            avg_write = (self.stats['total_write_time'] / count) if count else 0

            sys.stdout.write(f"Files total:               {total_files}\n")
            sys.stdout.write(f"Processed (successfully):  {count}\n") 
            sys.stdout.write(f"Attempted to process:      {processed_tasks_count}\n") 
            sys.stdout.write(f"Total elapsed:             {total_elapsed:.2f}s\n")
            if count > 0: 
                sys.stdout.write(
                    f"Read I/O total:            {self.stats['total_read_time']:.2f}s  (avg {avg_read:.2f}s)\n"
                )
                sys.stdout.write(
                    f"Deserialize total:         {self.stats['total_deserialize_time']:.2f}s  (avg {avg_deserialize:.2f}s)\n"
                )
                sys.stdout.write(
                    f"Map total:                 {self.stats['total_map_time']:.2f}s  (avg {avg_map:.2f}s)\n"
                )
                sys.stdout.write(
                    f"Serialize total:           {self.stats['total_serialize_time']:.2f}s  (avg {avg_serialize:.2f}s)\n"
                )
                sys.stdout.write(
                    f"Write I/O total:           {self.stats['total_write_time']:.2f}s  (avg {avg_write:.2f}s)\n"
                )

        finally:
            sys.stdout.write(self.SHOW_CURSOR)
