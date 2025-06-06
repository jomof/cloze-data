import os
import sys
import asyncio
import queue
import time
import threading
import traceback  # Keep for now, though error messages are also event-driven
import inspect
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from threading import Lock
import aiofiles  
import signal
import yaml
from collections import OrderedDict

class ConsoleDisplay:
    """
    Handles interactive console display for operations, progress, and statistics.

    The caller should use begin(), finish(), and error() to report work items with a type tag.
    ConsoleDisplay maintains a list of items and shows active or recently finished ones,
    and summarizes how many of each type are active, as well as total accumulated time per type.
    """
    CLEAR_TO_EOL    = "\u001b[K"
    MOVE_UP         = staticmethod(lambda n: f"\u001b[{n}A")
    MOVE_DOWN       = staticmethod(lambda n: f"\u001b[{n}B")
    HIDE_CURSOR     = "\u001b[?25l"
    SHOW_CURSOR     = "\u001b[?25h"
    SAVE_CURSOR     = "\u001b[s"
    RESTORE_CURSOR  = "\u001b[u"
    CLEAR_DOWN      = "\u001b[J"

    DEFAULT_REFRESH_INTERVAL = 0.2
    SCAVENGING_INTERVAL      = 5.0   # seconds, how often to remove old items
    SCAVENGING_AGE_LIMIT     = 15.0  # seconds, remove finished/error items older than this

    def __init__(self, window_size: int = 5, refresh_interval: float = None):
        self.window_size     = window_size
        self.refresh_interval = refresh_interval or self.DEFAULT_REFRESH_INTERVAL

        # Track global start time for total wall clock
        self.start_time = None

        # event_queue holds dicts: {'type': 'BEGIN'|'FINISH'|'ERROR'|'COUNTDOWN_UPDATE',
        #                          'slot_key': str, 'text': str, 'item_type': str, 'time': float,
        #                          'value': int (for COUNTDOWN_UPDATE)}
        self.event_queue = queue.Queue()
        # items maps slot_key to { 'text': str, 'time': float (start or finish), 'status': 'active'|'complete'|'error', 'item_type': str }
        self.items = {}
        # Track the order in which item_types first appear
        self.type_order = []
        # Track all slot_keys seen in BEGIN
        self.known_keys = set()
        # Track all slot_keys that have been closed (FINISH/ERROR)
        self.closed_keys = {}
        # Countdown if needed by caller
        self.countdown = 0

        # Summary counts and times of completed/error items by type
        self.summary_counts = {}  # e.g. { 'Reading': 3, 'Mapping': 5, … }
        self.summary_times  = {}  # e.g. { 'Reading': 12.7, 'Mapping': 5.3, … }

        self.watcher_thread      = None
        self.watch_done_event    = threading.Event()
        self.last_scavenge_time  = time.monotonic()
        self.final_summary_lines = []
        self.final_message = None
        
    def _scavenge_items(self):
        """Remove finished/error items older than SCAVENGING_AGE_LIMIT."""
        now = time.monotonic()
        to_remove = [
            key for key, v in self.items.items()
            if v['status'] in ['complete', 'error'] and (now - v['time']) > self.SCAVENGING_AGE_LIMIT
        ]
        for key in to_remove:
            del self.items[key]

    def _apply_event(self, event: dict):
        ev_type   = event.get('type')
        slot_key  = event.get('slot_key')
        text      = event.get('text', '')
        ts        = event.get('time', time.monotonic())
        item_type = event.get('item_type', 'Unknown')

        # Handle countdown updates separately
        if ev_type == 'COUNTDOWN_UPDATE':
            self.countdown = event.get('value', self.countdown)
            return

        # Only process BEGIN, FINISH, ERROR
        if ev_type not in ['BEGIN', 'FINISH', 'ERROR']:
            return

        # BEGIN event: record a new active item
        if ev_type == 'BEGIN':
            # Track new types in order
            if item_type not in self.type_order:
                self.type_order.append(item_type)
            # Record known key
            self.known_keys.add(slot_key)
            # Create or update item as active, store start time
            self.items[slot_key] = {
                'text': text,
                'time': ts,
                'status': 'active',
                'item_type': item_type
            }
            return

        # FINISH or ERROR: update existing or create
        # Determine the previous entry for this slot_key
        prev_entry = self.items.get(slot_key, {})
        prev_type  = prev_entry.get('item_type', item_type)
        start_ts   = prev_entry.get('time', ts)   # fallback to ts if missing
        elapsed    = ts - start_ts

        # Accumulate elapsed time for that type
        self.summary_times[prev_type] = self.summary_times.get(prev_type, 0.0) + elapsed

        # Update summary counts
        status = 'complete' if ev_type == 'FINISH' else 'error'
        self.summary_counts[prev_type] = self.summary_counts.get(prev_type, 0) + 1

        # Overwrite or update the item so the display can show final text
        self.items[slot_key] = {
            'text': text,
            'time': ts,
            'status': status,
            'item_type': prev_type
        }

    def _drain_all_events(self):
        """Drain all queued events except 'DONE'."""
        while True:
            try:
                extra = self.event_queue.get_nowait()
            except queue.Empty:
                break

            if isinstance(extra, dict):
                self._apply_event(extra)
            elif isinstance(extra, str) and extra == 'DONE':
                # Put 'DONE' back and stop draining
                self.event_queue.put('DONE')
                return

    def _do_redraw(self):
        """
        Redraw the console window: 
        - Show up to `window_size` lines of active/finished items (newest first).
        - Then show per-type counts of currently active items.
        - Finally show countdown if set.
        """
        lines       = [self.SAVE_CURSOR]
        clear_to_eol = self.CLEAR_TO_EOL
        now         = time.monotonic()

        # Build lists: active items (newest first), finished items (newest first)
        active_items   = []
        finished_items = []
        type_counts    = {t: 0 for t in self.type_order}

        for v in self.items.values():
            display_text = v['text']
            status       = v['status']
            msg_time     = v['time']
            item_type    = v.get('item_type', 'Unknown')

            if status == 'active':
                # count active types
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
                elapsed = now - msg_time
                line = f"  {display_text}"
                if elapsed > 1.0:
                    line += f" ({elapsed:.1f}s)"
                line += clear_to_eol + "\n"
                active_items.append((msg_time, line))
            else:
                line = f"  {display_text}"
                line += clear_to_eol + "\n"
                finished_items.append((msg_time, line))

        # Sort by time descending (newest first)
        active_items.sort(key=lambda x: x[0], reverse=True)
        finished_items.sort(key=lambda x: x[0], reverse=True)

        # Select up to window_size: prioritize active, then finished
        final_lines = []
        slots = self.window_size

        for _, line in active_items[:slots]:
            final_lines.append(line)
        slots -= len(final_lines)

        if slots > 0:
            for _, line in finished_items[:slots]:
                final_lines.append(line)
            slots -= len(finished_items[:slots])

        # If fewer than window_size, pad with blank lines
        for _ in range(max(0, self.window_size - len(final_lines))):
            final_lines.append(f"  {clear_to_eol}\n")

        # Display items first
        lines.extend(final_lines)

        # Display summary of active counts by type, in order of first arrival
        for t in self.type_order:
            count = type_counts.get(t, 0)
            lines.append(f"{t}: {count} active{clear_to_eol}\n")

        # Display countdown if set
        lines.append(f"{self.countdown} work items remaining{clear_to_eol}\n")

        # Final message if set
        if self.final_message:
            lines.append(f"{self.final_message}{clear_to_eol}\n")

        lines.append(self.CLEAR_DOWN)  # Clear below cursor

        lines.append(self.RESTORE_CURSOR)
        sys.stdout.write('\r')
        sys.stdout.write(''.join(lines))
        sys.stdout.flush()

    def _watcher_loop(self):
        """
        Thread loop that:
        - Periodically scavenges old items.
        - Processes incoming events (BEGIN, FINISH, ERROR, COUNTDOWN_UPDATE).
        - Redraws at least every refresh_interval seconds.
        - When receiving 'DONE', drains remaining events, does a final redraw, and prints summary.
        """
        refresh_interval = self.refresh_interval
        half_interval    = refresh_interval / 2.0
        last_redraw      = time.monotonic() - refresh_interval

        while True:
            now = time.monotonic()

            # Periodically scavenge old finished/error items
            if now - self.last_scavenge_time >= self.SCAVENGING_INTERVAL:
                self._scavenge_items()
                self.last_scavenge_time = now

            try:
                event = self.event_queue.get(timeout=half_interval)
            except queue.Empty:
                # If no event, maybe redraw if it's time
                if now - last_redraw >= refresh_interval:
                    self._do_redraw()
                    last_redraw = now
                continue

            # If 'DONE' sentinel, break out after final summary
            if isinstance(event, str) and event == 'DONE':
                # Drain remaining events (except DONE)
                self._drain_all_events()
                # Final redraw of active/finished window
                self._do_redraw()
                # Clear below cursor for summary
                sys.stdout.write(self.CLEAR_DOWN)

                # Print formatted per-type summary
                for t in self.type_order:
                    count = self.summary_counts.get(t, 0)
                    total = self.summary_times.get(t, 0.0)
                    type_label = f'{t}:'
                    sys.stdout.write(f"{type_label:<20} {count} items, {total:.1f}s\n")

                # Print total wall clock time
                total_wall_time = now - self.start_time if self.start_time is not None else 0.0
                sys.stdout.write(f"{'Total time:':<20} {total_wall_time:.1f}s\n")

                # Any additional final_summary_lines
                for line in self.final_summary_lines:
                    sys.stdout.write(line)
                sys.stdout.flush()
                self.watch_done_event.set()
                break

            # Otherwise, it's a dict event: apply it and drain any others
            if isinstance(event, dict):
                self._apply_event(event)
                self._drain_all_events()

            # Possibly redraw if enough time has elapsed
            if now - last_redraw >= refresh_interval:
                self._do_redraw()
                last_redraw = now

    def start(self):
        """Begin the watcher thread and hide the cursor."""
        # Record the start time when watcher begins
        self.start_time = time.monotonic()
        sys.stdout.write(self.HIDE_CURSOR)
        sys.stdout.flush()
        self.watch_done_event.clear()
        self.watcher_thread = threading.Thread(target=self._watcher_loop, daemon=True)
        self.watcher_thread.start()

    def stop(self):
        """
        Signal the watcher thread to finish by enqueuing 'DONE', then wait for it.
        Finally, restore the cursor.
        """
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.event_queue.put('DONE')
            # Wait up to a short timeout for the watcher to clean up
            self.watch_done_event.wait(timeout=max(self.refresh_interval * 2, 1.0))
        sys.stdout.write(self.SHOW_CURSOR)
        sys.stdout.flush()

    def _caller_file_line(self, n):
        stack = inspect.stack()
        # [0] is this frame, [1] is _debug_print_caller_message caller, [2] is the original caller
        caller_frame_info = stack[n+1]
        filename = os.path.basename(caller_frame_info.filename)
        lineno   = caller_frame_info.lineno
        return f"{filename}:{lineno}"

    def _debug_print_caller_message(self, message: str):
        """
        Print a debug message including the filename and line number of the caller.
        """
        caller = self._caller_file_line(2)
        print(f"\n❌ {caller}: {message}")
        traceback.print_stack()
        sys.exit(1)


    def begin(self, slot_key: str, message: str, item_type: str):
        """Mark a work item as started with a given type."""
        if slot_key in self.known_keys:
            self._debug_print_caller_message(
                f"BEGIN called for slot_key '{slot_key}' which is already begun."
            )
            return
        if slot_key in self.closed_keys:
            self._debug_print_caller_message(
                f"BEGIN called for closed slot_key '{slot_key}' (original class at {self.closed_keys[slot_key]})."
            )
            return
        # Record the event
        self.known_keys.add(slot_key)
        self.event_queue.put({
            'type': 'BEGIN',
            'slot_key': slot_key,
            'text': f'🔄 {message}',
            'item_type': item_type,
            'time': time.monotonic()
        })

    def finish(self, slot_key: str, message: str):
        """Mark a work item as completed."""
        if slot_key not in self.known_keys:
            self._debug_print_caller_message(
                f"FINISH called for unknown slot_key '{slot_key}'."
            )
            return
        if slot_key in self.closed_keys.keys():
            self._debug_print_caller_message(
                f"FINISH called for closed slot_key '{slot_key}' (original class at {self.closed_keys[slot_key]})."
            )
            return
        self.closed_keys[slot_key] = "1" # self._caller_file_line(1)
        self.event_queue.put({
            'type': 'FINISH',
            'slot_key': slot_key,
            'text': f'✅ {message}',
            # No need to pass item_type here; _apply_event will read existing type
            'time': time.monotonic()
        })

    def error(self, slot_key: str, message: str):
        """Mark a work item as errored."""        
        if slot_key not in self.known_keys:
            # Unknown key: just write the error immediately to stdout
            sys.stdout.write(f'❌ {message}\n')
            return        
        if slot_key in self.closed_keys.keys():
            self._debug_print_caller_message(
                f"ERROR called for closed slot_key '{slot_key}'."
            )
            return
        self._debug_print_caller_message(f"\n❌ {message}")
        self.closed_keys[slot_key] = self._caller_file_line(1)
        self.event_queue.put({
            'type': 'ERROR',
            'slot_key': slot_key,
            'text': f'❌ {message}',
            'time': time.monotonic()
        })

    def warn(self, message: str):
        """Print a warning immediately (not tied to any slot)."""
        sys.stdout.write(f'⚠️ {message}\n')

    def update_countdown(self, count: int):
        """Update the countdown of remaining work items."""
        self.event_queue.put({
            'type': 'COUNTDOWN_UPDATE',
            'value': count,
            'time': time.monotonic()
        })

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
        map_inproc: bool = False,  

        fold_func_name: str = 'folding',
        fold_func=None,

        serialize_func=lambda raw: dump_yaml(raw),

        output_dir: str = None,
        initial_accumulator=None,
        temp_dir: str = None,
        max_threads: int = 4,
        window_size: int = None,  # Passed to ConsoleDisplay
        refresh_interval: float = None  # Passed to ConsoleDisplay
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.deserialize_func = deserialize_func
        self.preprocess_func = preprocess_func
        self.map_func_name = map_func_name
        self.map_inproc = map_inproc  
        self.map_func = map_func
        self.serialize_func = serialize_func
        self.fold_func_name = fold_func_name
        self.fold_func = fold_func
        self.accumulator = initial_accumulator

        # Initialize ConsoleDisplay (assumed available)
        self.display = ConsoleDisplay(window_size=window_size or max_threads, refresh_interval=refresh_interval)

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
        self.run_state = 'running'

        # Lock to ensure fold is single-threaded
        self.fold_lock = None  # will be initialized in run()

        def sigint_handler(signum, frame):
            if self.run_state == 'running':
                self.run_state = 'cancelling'
                SAVE_CURSOR     = "\u001b[s"
                RESTORE_CURSOR  = "\u001b[u"
                CLEAR_DOWN      = "\u001b[J"
                sys.stdout.write("\r")
                sys.stdout.write(SAVE_CURSOR)
                sys.stdout.write(CLEAR_DOWN)
                sys.stdout.write(RESTORE_CURSOR)
                sys.stdout.flush()
                self.display.final_message = f"⚠️ cancelling remaining tasks. Press ctrl-c again to exit."
                self.process_executor.shutdown(wait=False, cancel_futures=True)
                self.thread_executor.shutdown(wait=False, cancel_futures=True)
                self.process_executor.shutdown(wait=True, cancel_futures=True)
                self.thread_executor.shutdown(wait=True, cancel_futures=True)
            sys.exit(1)
        signal.signal(signal.SIGINT, sigint_handler)

    async def process_one(self, input_file_path: str, output_file_path: str):
        basename = os.path.basename(input_file_path)
        original_obj = None
        result_item = None

        try:
            # Read the input file
            async with self.read_semaphore:
                if self.run_state != 'running':
                    return None
                async with aiofiles.open(input_file_path, "r", encoding="utf-8") as f:
                    raw = await f.read()

                # Deserialize the raw data
                deserialized = self.deserialize_func(raw)
                original_obj = deserialized  # Keep original for fold if preprocess returns None

            # Preprocess if applicable
            if self.preprocess_func:
                async with self.preprocess_semaphore:
                    self.display.begin(f"PREPROCESS:{basename}", f'preprocessing {basename}', 'preprocessing')
                    deserialized = self.preprocess_func(deserialized, input_file_path)
                    self.display.finish(f"PREPROCESS:{basename}", f'finished preprocessing {basename}')
                    if deserialized is None:
                        result_item = original_obj
                        # Skip map/write, but proceed to fold
                    
            # If preprocess did not skip, do map and write
            if result_item is None:
                if not self.map_func:
                    result_item = original_obj
                else:
                    # Process the data (map)
                    async with self.map_semaphore:
                        if self.run_state != 'running':
                            return None
                        self.display.begin(f"MAP:{basename}", f'{self.map_func_name} {basename}', self.map_func_name)
                        if self.map_inproc:
                            processed = self.map_func(deserialized, input_file_path)
                        else:
                            processed = await asyncio.get_running_loop().run_in_executor(
                                self.process_executor,
                                self.map_func,
                                deserialized,
                                input_file_path)
                        self.display.finish(f"MAP:{basename}", f'finished {self.map_func_name} {basename}')

                    # Serialize the processed data and write to temp file
                    final_str = self.serialize_func(processed)
                    os.makedirs(self.temp_dir, exist_ok=True)
                    tmp_path = os.path.join(self.temp_dir, f".{basename}.tmp")
                    async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
                        await f.write(final_str)
                    # Replace output file
                    try:
                        os.remove(output_file_path)
                    except FileNotFoundError:
                        pass
                    os.replace(tmp_path, output_file_path)
                    result_item = processed

            # If fold_func is defined, do fold immediately, serialized by fold_lock
            if self.fold_func and result_item is not None:
                # Ensure only one fold at a time
                async with self.fold_lock:
                    self.display.begin(f"FOLD:{basename}", f'{self.fold_func_name} {basename}', self.fold_func_name)
                    self.accumulator = self.fold_func(self.accumulator, result_item)
                    self.display.finish(f"FOLD:{basename}", f'finished {self.fold_func_name} {basename}')

            return result_item

        finally:
            # Update the countdown
            with self.counter_lock:
                self.countdown -= 1
                self.display.update_countdown(self.countdown)

    async def run(self):
        self.read_semaphore = asyncio.Semaphore(self.max_threads)
        self.preprocess_semaphore = asyncio.Semaphore(self.max_threads)
        self.map_semaphore = asyncio.Semaphore(self.max_threads)
        self.fold_lock = asyncio.Lock()
        # ex = None

        # def my_exception_handler(loop, context):
        #     nonlocal ex
        #     ex = context.get("exception")

        # asyncio.get_event_loop().set_exception_handler(my_exception_handler)

        self.display.start()

        # Gather input files
        if not os.path.isdir(self.input_dir):
            self.display.error('INIT_ERROR', f"Input directory not found: {self.input_dir}")
            all_input_files = []
            total = 0
        else:
            all_input_files = [os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir)
                                if os.path.isfile(os.path.join(self.input_dir, f))]
            total = len(all_input_files)

        with self.counter_lock:
            self.countdown = total
        self.display.update_countdown(self.countdown)

        if total == 0 and os.path.isdir(self.input_dir):
            self.display.warn('No files found to process')

        try:
            tasks = []
            for fpath in all_input_files:
                out_path = None
                if self.output_dir:
                    out_path = os.path.join(self.output_dir, os.path.basename(fpath))
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                tasks.append(asyncio.create_task(self.process_one(fpath, out_path)))

            # Wait for all tasks to complete; folding happens inside process_one
            for fut in asyncio.as_completed(tasks):
                try:
                    await fut
                except Exception as ex:
                    if ex:
                        raise ex
                    
            # Write the accumulator
            if self.fold_func and self.accumulator is not None:
                serialized_accumulator = self.serialize_func(self.accumulator)
                accumulator_output_dir = os.path.join(self.output_dir, 'summary')
                os.makedirs(accumulator_output_dir, exist_ok=True)
                accumulator_output_path = os.path.join(accumulator_output_dir, 'summary.json')
                async with aiofiles.open(accumulator_output_path, "w", encoding="utf-8") as f:
                    await f.write(serialized_accumulator)

        finally:
            self.process_executor.shutdown(wait=False, cancel_futures=True)
            self.thread_executor.shutdown(wait=False, cancel_futures=True)
            self.display.stop()

