import os
import asyncio
import aiofiles
import queue
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from python.grammar import clean_lint
import yaml
import json

class MapReduce:
    """
    Generic MapReduce framework for:
    - Reading files (raw content)
    - Delegating to a user-provided `process_func` (taking raw content)
    - Writing files (raw content)
    - Concurrency management
    - Statistics tracking
    - Console output (progress)
    """
    CLEAR_TO_EOL = "\u001b[K"
    MOVE_UP = staticmethod(lambda n: f"\u001b[{n}A")
    MOVE_DOWN = staticmethod(lambda n: f"\u001b[{n}B")
    HIDE_CURSOR = "\u001b[?25l"
    SHOW_CURSOR = "\u001b[?25h"
    SAVE_CURSOR = "\u001b[s"
    RESTORE_CURSOR = "\u001b[u"
    CLEAR_DOWN = "\u001b[J"

    def __init__(self, input_dir, output_dir, process_func, temp_dir=None, max_concurrent_reads=5, mru_size=5):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.process_func = process_func  # callable: (raw_content: str, file_path: str) -> processed_content: str
        self.temp_dir = temp_dir or os.path.join(input_dir, '.temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.max_concurrent_reads = max_concurrent_reads

        # Event queue and watcher state
        self.event_queue = queue.Queue()
        self.current_reads = 0
        self.current_processes = 0
        self.current_writes = 0
        self.log_message = ""
        self.mru_size = mru_size
        self.mru = []
        self.counter_lock = Lock()
        self.watch_done_event = threading.Event()
        self.countdown = 0

        # Stats
        self.stats = {'count': 0, 'total_read_time': 0.0, 'total_process_time': 0.0}

    def mru_push(self, item):
        """Update MRU with new log message."""
        try:
            self.mru.remove(item)
        except ValueError:
            pass
        self.mru.insert(0, item)
        if len(self.mru) > self.mru_size:
            self.mru.pop()

    def watcher_loop(self):
        """Runs on a separate thread, updating console on events."""
        while True:
            try:
                update = self.event_queue.get(timeout=0.1)

                if update == 'DONE':
                    sys.stdout.write(self.CLEAR_DOWN)
                    self.watch_done_event.set()
                    break
                if update == 'BEGIN_READ':
                    self.current_reads += 1
                elif update == 'END_READ':
                    self.current_reads -= 1
                elif update == 'BEGIN_PROCESS':
                    self.current_processes += 1
                elif update == 'END_PROCESS':
                    self.current_processes -= 1
                elif update == 'BEGIN_WRITE':
                    self.current_writes += 1
                elif update == 'END_WRITE':
                    self.current_writes -= 1
                elif update.startswith("LOG: "):
                    message = update[5:]
                    if '❌' in update:
                        sys.stdout.write(f"{message}{self.CLEAR_TO_EOL}\n")
                    else:
                        self.log_message = message
                        self.mru_push(message)
                        if len(self.mru) < self.mru_size:
                            continue
            except queue.Empty:
                continue

            # Redraw status lines
            sys.stdout.write(self.SAVE_CURSOR)
            copy = self.mru.copy()
            for msg in copy:
                sys.stdout.write(f"  {msg}{self.CLEAR_TO_EOL}\n")
            sys.stdout.write(f"Reading {self.current_reads} files{self.CLEAR_TO_EOL}\n")
            sys.stdout.write(f"Processing {self.current_processes} files{self.CLEAR_TO_EOL}\n")
            sys.stdout.write(f"Writing {self.current_writes} file{self.CLEAR_TO_EOL}s\n")
            sys.stdout.write(f"{self.countdown} work items remaining{self.CLEAR_TO_EOL}\n")
            sys.stdout.write(self.RESTORE_CURSOR)

    async def read_file(self, file_path, sem_read):
        """Read a file's raw text asynchronously with a semaphore."""
        async with sem_read:
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

    async def write_file(self, file_path, raw_content):
        """Write raw text via a temp file and atomic replace."""
        self.event_queue.put('BEGIN_WRITE')
        self.event_queue.put(f"LOG: 🔄 writing {os.path.basename(file_path)}")
        basename = os.path.basename(file_path)
        tmp_path = os.path.join(self.temp_dir, f".{basename}.tmp")
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

    async def process_task(self, file_path, raw_content, executor):
        """Invoke the user-provided process_func in an executor."""
        self.event_queue.put('BEGIN_PROCESS')
        try:
            base_name = os.path.basename(file_path)
            self.event_queue.put(f"LOG: 🔄 processing {base_name}")
            loop = asyncio.get_event_loop()
            start = time.perf_counter()
            result = await loop.run_in_executor(executor, self.process_func, raw_content, file_path)
            elapsed = time.perf_counter() - start
            return result, elapsed
        finally:
            self.event_queue.put('END_PROCESS')

    async def process_one(self, input_file_path, output_file_path, sem_read, executor):
        """Read -> process -> write for a single file, updating stats."""
        try:
            raw_content, read_time = await self.read_file(input_file_path, sem_read)
            self.stats['total_read_time'] += read_time

            processed_content, proc_time = await self.process_task(input_file_path, raw_content, executor)
            self.stats['total_process_time'] += proc_time
            self.stats['count'] += 1

            await self.write_file(output_file_path, processed_content)
            self.event_queue.put(f"LOG: ✅ finished {os.path.basename(input_file_path)} read {read_time:.2f}s, proc {proc_time:.2f}s")
        except Exception as e:
            self.event_queue.put(f"LOG: ❌ error {os.path.basename(input_file_path)}: {str(e)}")
            raise
        finally:
            with self.counter_lock:
                self.countdown -= 1

    async def run(self):
        """Execute the full workflow: spawn watcher, dispatch tasks, report stats."""
        sys.stdout.write(self.HIDE_CURSOR)
        try:
            all_files = [
                os.path.join(self.input_dir, fname)
                for fname in os.listdir(self.input_dir)
                if os.path.isfile(os.path.join(self.input_dir, fname))
            ]
            total_files = len(all_files)
            self.countdown = total_files

            watcher_thread = threading.Thread(target=self.watcher_loop, daemon=True)
            watcher_thread.start()

            sem_read = asyncio.Semaphore(self.max_concurrent_reads)
            start_all = time.perf_counter()

            with ThreadPoolExecutor() as executor:
                tasks = [asyncio.create_task(
                    self.process_one(
                        f, 
                        os.path.join(self.output_dir, os.path.basename(f)), 
                        sem_read, 
                        executor)) for f in all_files]
                for t in asyncio.as_completed(tasks):
                    await t
                self.event_queue.put('DONE')
                self.watch_done_event.wait()

            total_elapsed = time.perf_counter() - start_all
            count = self.stats['count']
            avg_read = self.stats['total_read_time'] / count if count else 0
            avg_proc = self.stats['total_process_time'] / count if count else 0

            sys.stdout.write(f"Files total: {total_files}\n")
            sys.stdout.write(f"Processed: {count}\n")
            sys.stdout.write(f"Total elapsed: {total_elapsed:.2f}s\n")
            sys.stdout.write(f"Total read time: {self.stats['total_read_time']:.2f}s (avg {avg_read:.2f}s)\n")
            sys.stdout.write(f"Total process time: {self.stats['total_process_time']:.2f}s (avg {avg_proc:.2f}s)\n")
        finally:
            sys.stdout.write(self.SHOW_CURSOR)



def my_business_logic(raw_content, file_path):
    parsed = yaml.load(raw_content, Loader=yaml.CSafeLoader)
    cleaned = clean_lint(parsed, file_path)
    return json.dumps(cleaned, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY', '')
    grammar_root = os.path.join(workspace_root, 'resources', 'processed', 'ai-cleaned-merge-grammars')
    mr = MapReduce(
        input_dir=grammar_root,
        output_dir=grammar_root,
        process_func=my_business_logic,
        temp_dir=os.path.join(workspace_root, '.temp'),
        max_concurrent_reads=5
    )
    asyncio.run(mr.run())
