# async_lint_optimized.py
import os
import yaml
import asyncio
import aiofiles
from python.grammar import clean_lint
import queue
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import sys
from threading import Lock
import json 

MAX_CONCURRENT_READS = 5 # os.cpu_count() or 1

CLEAR_TO_EOL = "\u001b[K"
MOVE_UP = lambda n: f"\u001b[{n}A"
MOVE_DOWN = lambda n: f"\u001b[{n}B"
HIDE_CURSOR = "\u001b[?25l"
SHOW_CURSOR = "\u001b[?25h"
SAVE_CURSOR = "\u001b[s"
RESTORE_CURSOR = "\u001b[u"
CLEAR_DOWN = "\u001b[J" 

temp_dir = '/workspaces/cloze-data/.temp'
os.mkdir(temp_dir) if not os.path.exists(temp_dir) else None

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
                    sys.stdout.write(f"{update[5:]}{CLEAR_TO_EOL}\n")  
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
            sys.stdout.write(f"  {message}{CLEAR_TO_EOL}\n")
        sys.stdout.write(f"Reading {current_reads} files{CLEAR_TO_EOL}\n")
        sys.stdout.write(f"Processing {current_processes} files{CLEAR_TO_EOL}\n")
        sys.stdout.write(f"Writing {current_writes} file{CLEAR_TO_EOL}s\n")
        sys.stdout.write(f"{countdown} work items remaining{CLEAR_TO_EOL}\n")
        sys.stdout.write(RESTORE_CURSOR)


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
    """
    Write `data` (as JSON/YAML) to a temp‐file and then atomically replace `file_path`.
    """
    event_queue.put("BEGIN_WRITE")
    event_queue.put(f"LOG: 🔄 writing {os.path.basename(file_path)}")

    # 1) Decide on a temp path in the same directory, so that os.replace() will be atomic.
    basename = os.path.basename(file_path)
      # Use a specific temp directory
    tmp_path = os.path.join(temp_dir, f".{basename}.tmp")

    try:
        # 2) Open temp file for writing
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as tmp_f:
            dump = json.dumps(data, ensure_ascii=False, indent=4)
            if "grammar_point" not in dump:
                raise ValueError("Dumped content looks wrong, missing 'grammar_point' key")

            # (Optional) log for debugging
            await tmp_f.write(dump)

        # 3) Once the write is fully closed, atomically replace the old file.
        #    os.replace() will overwrite the destination if it exists.
        #    If you’re on Windows, os.replace works like a “force”‐rename.
        await asyncio.to_thread(os.replace, tmp_path, file_path)

    finally:
        # If something went wrong *before* the replace, you might want to clean up
        # the leftover tmp file. If the replace already succeeded, tmp_path no longer exists.
        if os.path.exists(tmp_path):
            try:
                await asyncio.to_thread(os.remove, tmp_path)
            except Exception:
                pass

        event_queue.put("END_WRITE")

async def lint_task(grammar_file, grammar, executor):
    event_queue.put("BEGIN_PROCESS")
    try:
        base_name = os.path.basename(grammar_file)
        event_queue.put(f"LOG: 🔄 linting {base_name}")
        loop = asyncio.get_event_loop()
        start = time.perf_counter()
        cleaned = await loop.run_in_executor(executor, clean_lint, grammar, grammar_file)
        elapsed = time.perf_counter() - start
        return cleaned, elapsed
    finally:
        event_queue.put("END_PROCESS")

async def process_one(grammar_file, sem_read, executor, stats):
    try:
        # 1. Read file
        grammar, read_time = await read_yaml(grammar_file, sem_read)
        stats['total_read_time'] += read_time
        # 2. Lint
        cleaned, lint_time = await lint_task(grammar_file, grammar, executor)
        stats['total_lint_time'] += lint_time
        stats['count'] += 1
        # 3. Write back
        await write_yaml(grammar_file, cleaned)
        event_queue.put(f"LOG: ✅ finished {os.path.basename(grammar_file)} {read_time:.2f}s, lint {lint_time:.2f}s")
    except Exception as e:
        event_queue.put(f"LOG: ❌ error {os.path.basename(grammar_file)}: {str(e)}")
        raise e
    finally:
        with counter_lock:
            global countdown
            countdown -= 1

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
        stats = {'count': 0, 'total_read_time': 0.0, 'total_lint_time': 0.0}

        start_all = time.perf_counter()
        with ThreadPoolExecutor() as executor:
            tasks = [asyncio.create_task(process_one(f, sem_read, executor, stats)) for f in all_files]
            for t in asyncio.as_completed(tasks):
                await t
            event_queue.put('DONE')
            watcher_done_event.wait()
        total_elapsed = time.perf_counter() - start_all

        count = stats['count']
        avg_read = stats['total_read_time'] / count if count else 0
        avg_lint = stats['total_lint_time'] / count if count else 0
        sys.stdout.write(f"Files total: {total_files}\n")
        sys.stdout.write(f"Processed: {count}\n")
        sys.stdout.write(f"Total elapsed: {total_elapsed:.2f}s\n")
        sys.stdout.write(f"Total read time: {stats['total_read_time']:.2f}s (avg {avg_read:.2f}s)\n")
        sys.stdout.write(f"Total lint time: {stats['total_lint_time']:.2f}s (avg {avg_lint:.2f}s)\n")
    finally:
        sys.stdout.write(SHOW_CURSOR)


if __name__ == '__main__':
    asyncio.run(main())
