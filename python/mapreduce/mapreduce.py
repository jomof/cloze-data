import os
import sys
import asyncio
import aiofiles
import queue
import time
import threading
import traceback
import inspect
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

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
        • sem_cpu       for limiting concurrent CPU-bound tasks
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

    # Default redraw interval (in seconds). You can override by setting self.refresh_interval.
    DEFAULT_REFRESH_INTERVAL = 0.2

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
        mru_size: int = 5
    ):
        self.input_dir        = input_dir
        self.output_dir       = output_dir
        self.map_func         = map_func
        self.deserialize_func = deserialize_func
        self.serialize_func   = serialize_func

        self.temp_dir = temp_dir or os.path.join(input_dir, '.temp')
        os.makedirs(self.temp_dir, exist_ok=True)

        # Placeholder for semaphores; to be created in run()
        self.max_concurrent_reads = max_concurrent_reads
        self.sem_read = None
        self.max_concurrent_cpu = max_concurrent_cpu
        self.sem_cpu = None
        self.max_concurrent_map = max_concurrent_map
        self.sem_map = None

        # Event queue and watcher state
        self.event_queue       = queue.Queue()
        self.current_reads     = 0
        self.current_processes = 0
        self.current_maps      = 0
        self.current_writes    = 0
        self.log_message       = ""
        self.mru_size          = mru_size
        self.mru               = []
        self.counter_lock      = Lock()
        self.watch_done_event  = threading.Event()
        self.countdown         = 0

        # Stats
        self.stats = {
            'count': 0,
            'total_read_time': 0.0,
            'total_deserialize_time': 0.0,
            'total_map_time': 0.0,
            'total_serialize_time': 0.0,
            'total_write_time': 0.0
        }

        # Redraw interval (override if desired)
        self.refresh_interval = self.DEFAULT_REFRESH_INTERVAL

    def mru_push(self, item):
        """Update MRU with new log message."""
        try:
            self.mru.remove(item)
        except ValueError:
            pass
        self.mru.insert(0, item)
        if len(self.mru) > self.mru_size:
            self.mru.pop()

    def _apply_event(self, event):
        """Update counters or print log based on a single event string."""
        if event == 'BEGIN_READ':
            self.current_reads += 1
        elif event == 'END_READ':
            self.current_reads -= 1
        elif event == 'BEGIN_CPU':
            self.current_processes += 1
        elif event == 'END_CPU':
            self.current_processes -= 1
        elif event == 'BEGIN_MAP':
            self.current_maps += 1
        elif event == 'END_MAP':
            self.current_maps -= 1
        elif event == 'BEGIN_WRITE':
            self.current_writes += 1
        elif event == 'END_WRITE':
            self.current_writes -= 1
        elif event.startswith("LOG: "):
            message = event[5:]
            if '❌' in event:
                sys.stdout.write(f"{message}{self.CLEAR_TO_EOL}\n")
            else:
                self.log_message = message
                self.mru_push(message)
                return 'LOG'
        return None

    def _do_redraw(self):
        """Draw the current status lines to stdout in one batched write."""
        # Build all lines first, then write once to reduce syscalls.
        lines = []
        lines.append(self.SAVE_CURSOR)

        # Use local references for speed
        clear_to_eol = self.CLEAR_TO_EOL
        reads = self.current_reads
        procs = self.current_processes
        maps = self.current_maps
        writes = self.current_writes
        countdown = self.countdown

        # MRU: display most recent messages up to mru_size
        for msg in self.mru:
            lines.append(f"  {msg}{clear_to_eol}\n")
        lines.append(f"Reading   {reads} files{clear_to_eol}\n")
        lines.append(f"CPU tasks {procs} active{clear_to_eol}\n")
        lines.append(f"Map calls {maps} active{clear_to_eol}\n")
        lines.append(f"Writing   {writes} files{clear_to_eol}\n")
        lines.append(f"{countdown} work items remaining{clear_to_eol}\n")
        lines.append(self.RESTORE_CURSOR)

        sys.stdout.write(''.join(lines))

    def watcher_loop(self):
        """Runs on a separate thread, updating console on events with throttled redraws."""
        # Determine desired interval between redraws
        refresh_interval = getattr(self, 'refresh_interval', self.DEFAULT_REFRESH_INTERVAL)
        half_interval = refresh_interval / 2
        last_redraw = time.monotonic() - refresh_interval

        while True:
            # 1) Wait for at least one event (or timeout)
            try:
                update = self.event_queue.get(timeout=half_interval)
            except queue.Empty:
                now = time.monotonic()
                if now - last_redraw >= refresh_interval:
                    self._do_redraw()
                    last_redraw = now
                continue

            # 2) Handle DONE
            if update == 'DONE':
                sys.stdout.write(self.CLEAR_DOWN)
                self.watch_done_event.set()
                break

            # 3) Apply the first event
            first_log = self._apply_event(update)
            if first_log == 'LOG' and len(self.mru) < self.mru_size:
                # Drain remaining events without redrawing
                while True:
                    try:
                        self.event_queue.get_nowait()
                    except queue.Empty:
                        break
                continue

            # 4) Drain extra events and apply each
            while True:
                try:
                    extra = self.event_queue.get_nowait()
                except queue.Empty:
                    break

                if extra == 'DONE':
                    sys.stdout.write(self.CLEAR_DOWN)
                    self.watch_done_event.set()
                    return
                self._apply_event(extra)

            # 5) Redraw if enough time has elapsed
            now = time.monotonic()
            if now - last_redraw >= refresh_interval:
                self._do_redraw()
                last_redraw = now

    async def read_file(self, file_path: str):
        """Read a file's raw text asynchronously under sem_read."""
        async with self.sem_read:
            self.event_queue.put('BEGIN_READ')
            self.event_queue.put(f"LOG: 🔄 reading {os.path.basename(file_path)}")
            try:
                start = time.perf_counter()
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = await f.read()
                elapsed = time.perf_counter() - start
            finally:
                self.event_queue.put('END_READ')
            return raw_content, elapsed

    async def write_file(self, file_path: str, raw_content: str):
        """Write raw text via a temp file and atomic replace."""
        self.event_queue.put('BEGIN_WRITE')
        self.event_queue.put(f"LOG: 🔄 writing {os.path.basename(file_path)}")
        basename = os.path.basename(file_path)
        tmp_path = os.path.join(self.temp_dir, f".{basename}.tmp")
        start = time.perf_counter()
        try:
            async with aiofiles.open(tmp_path, 'w', encoding='utf-8') as tmp_f:
                await tmp_f.write(raw_content)
            await asyncio.to_thread(os.replace, tmp_path, file_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    await asyncio.to_thread(os.remove, tmp_path)
                except Exception:
                    pass
            self.event_queue.put('END_WRITE')
            return time.perf_counter() - start

    def cpu_bound_deserialize(self, raw_content: str):
        start_d = time.perf_counter()
        deserialized = self.deserialize_func(raw_content)
        dt = time.perf_counter() - start_d
        return deserialized, dt

    def cpu_bound_serialize(self, processed_obj):
        start_s = time.perf_counter()
        final_str = self.serialize_func(processed_obj)
        st = time.perf_counter() - start_s
        return final_str, st

    async def process_one(self, input_file_path: str, output_file_path: str, executor: ThreadPoolExecutor):
        """
        Read → deserialize → map (sync or async, with sem_map) → serialize → write, updating stats.
        """
        try:
            # Read
            raw_content, read_time = await self.read_file(input_file_path)
            self.stats['total_read_time'] += read_time

            # Deserialize under CPU semaphore
            self.event_queue.put('BEGIN_CPU')
            deserialized, dt = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: self.cpu_bound_deserialize(raw_content)
            )
            self.event_queue.put('END_CPU')
            self.stats['total_deserialize_time'] += dt

            # Map phase (hybrid: sync or async)
            self.event_queue.put('BEGIN_MAP')
            start_m = time.perf_counter()
            if inspect.iscoroutinefunction(self.map_func):
                # Async map_func: limit concurrency via self.sem_map
                async with self.sem_map:
                    processed_obj = await self.map_func(deserialized, input_file_path)
            else:
                # Sync map_func: run in executor under sem_map
                async with self.sem_map:
                    processed_obj = await asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: self.map_func(deserialized, input_file_path)
                    )
            mpt = time.perf_counter() - start_m
            self.event_queue.put('END_MAP')
            self.stats['total_map_time'] += mpt

            # Serialize under CPU semaphore
            self.event_queue.put('BEGIN_CPU')
            final_str, st = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: self.cpu_bound_serialize(processed_obj)
            )
            self.event_queue.put('END_CPU')
            self.stats['total_serialize_time'] += st

            # Write
            write_time = await self.write_file(output_file_path, final_str)
            self.stats['total_write_time'] += write_time

            self.stats['count'] += 1
            self.event_queue.put(
                f"LOG: ✅ finished {os.path.basename(input_file_path)}"
            )

        except Exception as e:
            traceback.print_exc()
            self.event_queue.put(
                f"LOG: ❌ error {os.path.basename(input_file_path)}: {type(e).__name__}: {e}"
            )
            raise
        finally:
            with self.counter_lock:
                self.countdown -= 1

    async def run(self):
        """Execute the full workflow: spawn watcher, dispatch tasks, report stats."""
        # Create semaphores bound to current loop
        self.sem_read = asyncio.Semaphore(self.max_concurrent_reads)
        self.sem_cpu  = asyncio.Semaphore(self.max_concurrent_cpu)
        self.sem_map  = asyncio.Semaphore(self.max_concurrent_map)

        sys.stdout.write(self.HIDE_CURSOR)
        try:
            all_files = [
                os.path.join(self.input_dir, fname)
                for fname in os.listdir(self.input_dir)
                if os.path.isfile(os.path.join(self.input_dir, fname))
            ]
            total_files = len(all_files)
            self.countdown = total_files

            if total_files == 0:
                self.event_queue.put('DONE')
                self.watch_done_event.wait()
                return

            watcher_thread = threading.Thread(target=self.watcher_loop, daemon=True)
            watcher_thread.start()

            start_all = time.perf_counter()

            with ThreadPoolExecutor() as executor:
                tasks = []
                for fpath in all_files:
                    out_path = os.path.join(self.output_dir, os.path.basename(fpath))
                    tasks.append(
                        asyncio.create_task(
                            self.process_one(fpath, out_path, executor)
                        )
                    )
                for t in asyncio.as_completed(tasks):
                    await t

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
            sys.stdout.write(f"Processed:                 {count}\n")
            sys.stdout.write(f"Total elapsed:             {total_elapsed:.2f}s\n")
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


# if __name__ == '__main__':
#     import yaml
#     import json
#     from python.grammar import clean_lint

#     # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
#     workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
#     grammar_root   = os.path.join(
#         workspace_root,
#         'resources', 'processed', 'ai-cleaned-merge-grammars'
#     )

#     if not os.path.isdir(grammar_root):
#         print(f"ERROR: “{grammar_root}” is not a directory.")
#         sys.exit(1)

#     def deserialize_yaml(raw: str):
#         return yaml.load(raw, Loader=yaml.CSafeLoader)

#     def serialize_json(obj):
#         return json.dumps(obj, ensure_ascii=False, indent=4)

#     async def lint_logic(parsed_obj, file_path):
#         # return parsed_obj
#         return clean_lint(parsed_obj, file_path)

#     mr = MapReduce(
#         input_dir            = grammar_root,
#         output_dir           = grammar_root,
#         map_func             = lint_logic,        # or a sync function
#         deserialize_func     = deserialize_yaml,
#         serialize_func       = serialize_json,
#         temp_dir             = os.path.join(workspace_root, '.temp'),
#         max_concurrent_reads = 3,
#         max_concurrent_cpu   = 2,
#         max_concurrent_map   = 2
#     )

#     asyncio.run(mr.run())
