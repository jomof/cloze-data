#!/usr/bin/env python3
"""
Service script with parallel processing, shared memory usage logging,
and threaded garbage collection. Child processes ignore SIGINT and SIGTERM,
so only the main process handles these signals for graceful shutdown.
"""
import os
import zipfile
import mmap
import contextlib
import time
import signal
import sys
import multiprocessing
import fcntl
import logging
import threading
from datetime import datetime, timedelta

# Directory where our cached data will be stored as .zip
CACHE_DIR = '/workspaces/cloze-data/cache_data'
os.makedirs(CACHE_DIR, exist_ok=True)

# How many results to keep (-1 for unlimited)
MAX_ENTRIES = 1000

# Plaintext password (for demonstration only, not secure)
ZIP_PASSWORD = b"plaintext-password"

# Name of the shared memory segment
SHM_NAME = "cache_shm"
# Maximum size of the shared memory segment (adjust as needed)
SHM_SIZE = 1024 * 1024  # 1 MB

# Number of worker processes
NUM_WORKERS = multiprocessing.cpu_count()

# Garbage collection interval in seconds
GC_INTERVAL = 3600  # 1 hour

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(process)d - %(message)s')

def handle_request(shm, request_queue, shared_high_water_mark):
    """
    Handles a single request from the shared memory segment.
    Reads the request from shared memory, processes it, and writes the response back.
    """
    # Read from the beginning of shared memory
    shm.seek(0)
    key_bytes = shm.read(SHM_SIZE)

    # Find null-terminated key
    null_index = key_bytes.find(b'\0')
    if null_index == -1:
        return  # Wait for a full key to be written

    key = key_bytes[:null_index].decode('utf-8')
    action = key.split(":")[0]

    if action == "GET":
        _, get_key = key.split(":", 1)
        value = get_value(get_key)
        write_response_to_shm(shm, value, shared_high_water_mark)
    elif action == "POST":
        _, post_key, val = key.split(":", 2)
        set_value(post_key, val)
        # No response needed for POST

def write_response_to_shm(shm, value, shared_high_water_mark):
    """
    Writes a response to shared memory.
    """
    shm.seek(0)
    # Clear previous data
    shm.write(b'\0' * SHM_SIZE)
    shm.seek(0)
    if value is not None:
        response_bytes = value.encode('utf-8')
        response_len = len(response_bytes)
        if response_len + 1 > shm.size():
            logging.error("Error: Response exceeds shared memory capacity")
            return
        shm.write(response_bytes)
        shm.write(b'\0')

        # Check and log shared memory usage
        with shared_high_water_mark.get_lock():
            if response_len > shared_high_water_mark.value:
                shared_high_water_mark.value = response_len
                logging.info(f"New high shared memory usage: {response_len} bytes")
    else:
        # If there's no value, store 'None'
        shm.write(b'None\0')

def get_value(key):
    """
    GET /cache/<key>
    Returns the stored value for <key>, or None if no file exists.
    Updates the file's modification time if it exists (to count as "most recently accessed").
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")
    if not os.path.exists(zip_path):
        return None

    # Touch the ZIP file to update its modification time
    os.utime(zip_path, None)

    try:
        # Acquire a shared lock (read-only)
        with open(zip_path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data_obj = read_data_from_zip(zip_path, ZIP_PASSWORD)
            fcntl.flock(f, fcntl.LOCK_UN)  # Release lock
        if data_obj is None:
            return None
        return data_obj["value"]
    except Exception as e:
        logging.error(f"Error reading from {zip_path}: {e}")
        return None

def set_value(key, value):
    """
    POST /cache/<key>
    Stores the value in a password-protected ZIP with separate key.txt/value.txt files.
    Overwrites any existing file at that path.
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")
    for _ in range(10):
        try:
            # Acquire exclusive lock (for writing)
            with open(zip_path, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                write_data_to_zip(zip_path, key, value, ZIP_PASSWORD)
                fcntl.flock(f, fcntl.LOCK_UN)  # Release lock
            # Touch the ZIP file to update its mod time
            os.utime(zip_path, None)
            break
        except Exception as e:
            logging.error(f"Error writing to {zip_path}: {e}")
            return

def write_data_to_zip(zip_path, key_str, value_str, password):
    """
    Writes key.txt and value.txt into the specified ZIP file.
    This overwrites any existing content.
    """
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Standard library doesn't fully support password-based encryption for writing.
        zf.writestr("key.txt", key_str)
        zf.writestr("value.txt", value_str)

def read_data_from_zip(zip_path, password):
    """
    Reads key.txt and value.txt from the ZIP and returns {"key": ..., "value": ...}
    or None if something is missing or fails.
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # ZipCrypto password support is limited in the standard library
        zf.setpassword(password)
        try:
            key_data = zf.read("key.txt").decode("utf-8")
            value_data = zf.read("value.txt").decode("utf-8")
            return {"key": key_data, "value": value_data}
        except KeyError:
            return None

def garbage_collect():
    """
    1. Sorts all .zip files in descending order by modification time.
    2. Keeps the first MAX_ENTRIES (if MAX_ENTRIES > 0).
    3. Deletes the rest.
    4. Additionally removes any file older than 24 hours from the kept subset.
    5. Logs how many files were deleted.
    """
    logging.info("Running garbage collection...")
    now = datetime.now()
    one_day_ago = now - timedelta(hours=24)

    try:
        all_files = [
            os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)
            if f.endswith('.zip')
        ]
        # Sort files by modification time descending (newest first)
        all_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

        # Always keep top MAX_ENTRIES files by mod time, ignoring the 24-hour limit (for now)
        if MAX_ENTRIES > 0:
            files_to_keep = all_files[:MAX_ENTRIES]
            files_to_delete = all_files[MAX_ENTRIES:]
        else:
            # If MAX_ENTRIES == -1, keep all for now
            files_to_keep = all_files
            files_to_delete = []

        # Now enforce the 24-hour rule on the "kept" files:
        final_keep = []
        for f in files_to_keep:
            if datetime.fromtimestamp(os.path.getmtime(f)) < one_day_ago:
                # If it's older than a day, delete it as well
                files_to_delete.append(f)
            else:
                final_keep.append(f)

        # Actually delete the files we've flagged
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                logging.info(f"Garbage collected: {file_path}")
                deleted_count += 1
            except OSError as e:
                logging.error(f"Error removing {file_path}: {e}")

        logging.info(f"{deleted_count} files were deleted during garbage collection.")

    except Exception as e:
        logging.error(f"Error during garbage collection: {e}")
    finally:
        logging.info("Garbage collection finished.")

def run_garbage_collector(stop_event):
    """
    Thread function to run garbage collection periodically.
    """
    while not stop_event.is_set():
        garbage_collect()
        time.sleep(GC_INTERVAL)

def cleanup_shm():
    """
    Removes the shared memory segment in the main process.
    """
    try:
        # If you have a global 'shm' object in main, you could shm.close() here too.
        # Remove the shared memory file
        if os.path.exists(f"/dev/shm/{SHM_NAME}"):
            os.remove(f"/dev/shm/{SHM_NAME}")
        logging.info("Shared memory segment cleaned up.")
    except Exception as e:
        logging.error(f"Error cleaning up shared memory: {e}")

def signal_handler(signum, frame):
    """
    Handles SIGINT and SIGTERM signals (main process only) for graceful shutdown.
    """
    logging.info(f"Signal {signum} received. Shutting down...")
    cleanup_shm()
    sys.exit(0)

def worker_process(shm_name, shm_size, request_queue, shared_high_water_mark):
    """
    Worker process: ignores SIGINT/SIGTERM, so only main handles them.
    """
    # Disable signal handlers in this child
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    # Open the shared memory segment
    with open(f"/dev/shm/{shm_name}", "r+b") as f:
        with contextlib.closing(mmap.mmap(f.fileno(), shm_size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)) as shm:
            while True:
                handle_request(shm, request_queue, shared_high_water_mark)
                time.sleep(0.1)  # Throttle request handling

if __name__ == '__main__':
    # Register signal handlers in main only
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    request_queue = multiprocessing.Queue()
    shared_high_water_mark = multiprocessing.Value('i', 0)

    try:
        # Create the shared memory file
        with open(f"/dev/shm/{SHM_NAME}", "w+b") as f:
            f.truncate(SHM_SIZE)

        # Start worker processes (children ignore signals)
        processes = []
        for _ in range(NUM_WORKERS):
            p = multiprocessing.Process(
                target=worker_process,
                args=(SHM_NAME, SHM_SIZE, request_queue, shared_high_water_mark)
            )
            p.start()
            processes.append(p)

        # Garbage collector thread
        stop_gc_event = threading.Event()
        gc_thread = threading.Thread(target=run_garbage_collector, args=(stop_gc_event,))
        gc_thread.start()

        # Keep the main process alive
        while True:
            time.sleep(1)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        cleanup_shm()
        sys.exit(1)
    finally:
        # Stop GC thread
        stop_gc_event.set()
        gc_thread.join()
