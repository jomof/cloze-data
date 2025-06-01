# async_lint_optimized.py
import os
import yaml
import asyncio
import aiofiles
from python.grammar import clean_lint
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import sys
from threading import Lock

# Adjust concurrent I/O and CPU-bound tasks separately
MAX_CONCURRENT_READS = 200
MAX_CONCURRENT_LINT = 3  # tune to number of CPU cores

CLEAR_TO_EOL = "\u001b[K"
MOVE_UP = lambda n: f"\u001b[{n}A"
MOVE_DOWN = lambda n: f"\u001b[{n}B"
HIDE_CURSOR = "\u001b[?25l"
SHOW_CURSOR = "\u001b[?25h"
SAVE_CURSOR = "\u001b[s"
RESTORE_CURSOR = "\u001b[u"
CLEAR_DOWN = "\u001b[J" 

event_queue = queue.Queue()
current_reads = 0
current_processes = 0
current_writes = 0
log_message = ""
mru_size = 5  # Maximum size of the MRU list
mru = []
watcher_done_event = threading.Event()
counter_lock = Lock()
countdown = 0

def mru_push(mru_list: list, item) -> None:
    """
    Insert `item` at the front of `mru_list`, removing any existing occurrence.
    If len(mru_list) > max_size afterward, pop the last element.
    This mutates mru_list in place.
    """
    # Remove existing (if present)
    try:
        mru_list.remove(item)
    except ValueError:
        pass

    # Insert as most-recent at index 0
    mru_list.insert(0, item)

    # Trim the tail if we’ve exceeded max_size
    if len(mru_list) > mru_size:
        mru_list.pop()

def watcher_loop():
    """Runs in its own thread, redrawing all slots whenever an update is received."""
    global current_reads, current_processes, current_writes, log_message, mru_list
    while True:
        try:
            update = event_queue.get(timeout=0.1)

            if update == 'DONE':
                sys.stdout.write(CLEAR_DOWN)
                sys.stdout.flush()
                watcher_done_event.set()
                break
            if update == 'BEGIN_READ':
                current_reads += 1
            elif update == 'END_READ':
                current_reads -= 1
            elif update == 'BEGIN_PROCESS':
                current_processes += 1
            elif update == 'END_PROCESS':
                current_processes -= 1
            elif update == 'BEGIN_WRITE':
                current_writes += 1
            elif update == 'END_WRITE':
                current_writes -= 1
            elif update.startswith("LOG: "):
                if '❌' in update:  
                    sys.stdout.write(RESTORE_CURSOR)
                    sys.stdout.write(CLEAR_DOWN)
                    sys.stdout.write(update + "\n")  
                    sys.stdout.write(SAVE_CURSOR)
                    continue
                else:
                    log_message = update[5:]  # Strip "log: " prefix
                mru_push(mru, log_message)
                if len(mru) < mru_size:
                    continue
        except queue.Empty:
            continue
        # Redraw all slots
        sys.stdout.write(SAVE_CURSOR)
        copy = mru.copy()
        sorted(copy, key=lambda s: s[2:])
        for message in copy:
            sys.stdout.write(f"{message}{CLEAR_TO_EOL}\n")
        sys.stdout.write(f"Reading {current_reads} files" + CLEAR_TO_EOL + "\n")
        sys.stdout.write(f"Processing {current_processes} files" + CLEAR_TO_EOL + "\n")
        sys.stdout.write(f"Writing {current_writes} files" + CLEAR_TO_EOL + "\n")
        sys.stdout.write(f"{countdown} work items remaining" + CLEAR_TO_EOL + "\n")
        sys.stdout.write(RESTORE_CURSOR)
        sys.stdout.flush()

async def read_yaml(file_path, sem_read):
    async with sem_read:
        event_queue.put(f"BEGIN_READ")
        event_queue.put(f"LOG: 🔄 reading {os.path.basename(file_path)}")
        try:
            start = time.perf_counter()
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            data = yaml.load(content, Loader=yaml.CSafeLoader)
            elapsed = time.perf_counter() - start
        finally:
            event_queue.put(f"END_READ")
        return data, elapsed

async def write_yaml(file_path, data):
    # unchanged from previous
    event_queue.put(f"BEGIN_WRITE")
    event_queue.put(f"LOG: 🔄 writing {os.path.basename(file_path)}")
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        try:
            dump = yaml.dump(data, allow_unicode=True, sort_keys=False)
            await f.write(dump)
        finally:
            event_queue.put(f"END_WRITE")

async def lint_task(grammar_file, grammar, sem_lint, executor):
    async with sem_lint:
        event_queue.put("BEGIN_PROCESS")
        try:
            event_queue.put(f"LOG: 🔄 linting {os.path.basename(grammar_file)}")
            loop = asyncio.get_event_loop()
            start = time.perf_counter()
            cleaned = await loop.run_in_executor(executor, clean_lint, grammar)
            elapsed = time.perf_counter() - start
            return cleaned, elapsed
        finally:
            event_queue.put("END_PROCESS")

async def process_one(grammar_file, sem_read, sem_lint, executor, stats):
    try:
        # 1. Read file
        grammar, read_time = await read_yaml(grammar_file, sem_read)
        stats['total_read_time'] += read_time
        # 2. Lint in separate process
        cleaned, lint_time = await lint_task(grammar_file, grammar, sem_lint, executor)
        stats['total_lint_time'] += lint_time
        stats['count'] += 1
        # Optionally write back or drop
        # await write_yaml(grammar_file, cleaned)
        event_queue.put(f"LOG: ✅ finished {os.path.basename(grammar_file)} {read_time:.2f}s, lint {lint_time:.2f}s")
    except Exception as e:
        event_queue.put(f"LOG: ❌ error {os.path.basename(grammar_file)}: {str(e)}")
    finally:
        with counter_lock:
            global countdown
            countdown -= 1
            if countdown <= 0:
                event_queue.put('DONE')


async def main():
    global countdown
    sys.stdout.write(HIDE_CURSOR)
    try:
        workspace_root = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
        grammar_root = f"{workspace_root}/resources/processed/ai-cleaned-merge-grammars"

        all_files = [
            os.path.join(grammar_root, fname)
            for fname in os.listdir(grammar_root)
            if os.path.isfile(os.path.join(grammar_root, fname))
        ]
        total_files = len(all_files)
        countdown = total_files

        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()

        sem_read = asyncio.Semaphore(MAX_CONCURRENT_READS)
        sem_lint = asyncio.Semaphore(MAX_CONCURRENT_LINT)
        stats = {'count': 0, 'total_read_time': 0.0, 'total_lint_time': 0.0}

        start_all = time.perf_counter()
        with ThreadPoolExecutor() as executor:
            tasks = [asyncio.create_task(process_one(f, sem_read, sem_lint, executor, stats)) for f in all_files]
            for t in asyncio.as_completed(tasks):
                await t
            watcher_done_event.wait(timeout=2)
            total_elapsed = time.perf_counter() - start_all

            count = stats['count']
            avg_read = stats['total_read_time'] / count if count else 0
            avg_lint = stats['total_lint_time'] / count if count else 0
            print("\n=== Final Timing Statistics ===")
            print(f"Files total: {total_files}")
            print(f"Processed: {count}")
            print(f"Total elapsed: {total_elapsed:.2f}s")
            print(f"Total read time: {stats['total_read_time']:.2f}s (avg {avg_read:.2f}s)")
            print(f"Total lint time: {stats['total_lint_time']:.2f}s (avg {avg_lint:.2f}s)")
            sys.stdout.write(SHOW_CURSOR)
            sys.stdout.flush()
            executor.shutdown(wait=True, cancel_futures=True)
            print(f"Shutdown complete, all tasks finished.")
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()

if __name__ == '__main__':
    asyncio.run(main())
