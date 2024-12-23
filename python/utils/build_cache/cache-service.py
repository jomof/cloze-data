#!/usr/bin/env python3
# THIS IS service.py (modified for parallel processing, shm usage logging, and threaded garbage collection) --------
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

    # Read from wherever we are in shared memory
    key_bytes = shm.read(SHM_SIZE)

    # Find null-terminated key
    null_index = key_bytes.find(b'\0')
    if null_index == -1:
        return  # Wait for a full key to be written

    key = key_bytes[:null_index].decode('utf-8')

    action = key.split(":")[0]

    if action == "GET":
        _, key = key.split(":", 1)
        value = get_value(key)
        # Write response into shared memory
        write_response_to_shm(shm, value, shared_high_water_mark)
    elif action == "POST":
        _, key, value = key.split(":", 2)
        set_value(key, value)
        # No response needed for POST

def write_response_to_shm(shm, value, shared_high_water_mark):
    """
    Writes a response to shared memory.
    """
    # Go to the beginning of the shared memory
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
        shm.write(b'None\0')

        # Check and log shared memory usage
        with shared_high_water_mark.get_lock():
            if 4 > shared_high_water_mark.value:
                shared_high_water_mark.value = 4
                logging.info(f"New high shared memory usage: 4 bytes")

def get_value(key):
    """
    GET /cache/<key>
    Returns the stored value for <key>, or None if no file exists.
    Updates the file's modification time if it exists (to count as "most recently accessed").
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")
    if not os.path.exists(zip_path):
        return None

    # Touch the ZIP file to update its modification time (most recently accessed).
    os.utime(zip_path, None)

    try:
        # Acquire a shared lock (for reading)
        with open(zip_path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data_obj = read_data_from_zip(zip_path, ZIP_PASSWORD)
            fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock
        if data_obj is None:
            # Means we couldn't read or decode it
            return None

        # Return the stored value (the key we read is optional for verifying correctness)
        return data_obj["value"]
    except Exception as e:
        logging.error(f"Error reading from {zip_path}: {e}")
        return None

def set_value(key, value):
    """
    POST /cache/<key>
    Expects a JSON body with {"value": ...}.
    Stores the value in a password-protected ZIP with separate key.txt/value.txt files.
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")

    # Write data into the ZIP
    for i in range(10):
        try:
            # Acquire an exclusive lock (for writing)
            with open(zip_path, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                write_data_to_zip(zip_path, key, value, ZIP_PASSWORD)
                fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock
            # Touch the zip file
            os.utime(zip_path, None)
            break
        except Exception as e:
            logging.error(f"Error writing to {zip_path}: {e}")
            return

def write_data_to_zip(zip_path, key_str, value_str, password):
    """
    Stores the given key and value as two separate text files (key.txt, value.txt)
    inside the ZIP at `zip_path`. Overwrites any existing file at that path.
    """
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # For demonstration: writing files without real password-based encryption.
        # Standard library doesn't fully support password protection for writing.
        zf.writestr("key.txt", key_str)
        zf.writestr("value.txt", value_str)

def read_data_from_zip(zip_path, password):
    """
    Reads key.txt and value.txt from the ZIP and returns a dict {"key": ..., "value": ...}
    or None if there's an error (e.g. files missing).
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # The standard library only partially supports password for reading via ZipCrypto.
        zf.setpassword(password)
        try:
            key_data = zf.read("key.txt").decode("utf-8")
            value_data = zf.read("value.txt").decode("utf-8")
            return {"key": key_data, "value": value_data}
        except KeyError:
            return None

def garbage_collect():
    """
    Periodically performs garbage collection on the cache directory.
    """
    logging.info("Running garbage collection...")
    now = datetime.now()
    one_day_ago = now - timedelta(hours=24)

    try:
        all_files = [
            os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)
            if f.endswith('.zip')
        ]

        # Separate files into those to keep and those to potentially delete
        files_to_keep = []
        files_to_delete = []
        for file_path in all_files:
            last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if last_modified_time > one_day_ago:
                files_to_keep.append(file_path)
            else:
                files_to_delete.append(file_path)

        # If keeping a limited number of entries
        if MAX_ENTRIES > 0:
            if len(files_to_keep) >= MAX_ENTRIES:
                # Sort files to keep by modification time descending
                files_to_keep.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                # Move excess files to the delete list
                files_to_delete.extend(files_to_keep[MAX_ENTRIES:])
                files_to_keep = files_to_keep[:MAX_ENTRIES]

        # Delete files
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                logging.info(f"Garbage collected: {file_path}")
            except OSError as e:
                logging.error(f"Error removing {file_path}: {e}")
    except Exception as e:
        logging.error(f"Error during garbage collection: {e}")
    finally:
        logging.info("Garbage collection finished.")

def cleanup_shm():
    """
    Unmaps and removes the shared memory segment.
    """
    try:
        # Unmap the shared memory segment
        shm.close()
        # Remove the shared memory file (this is OS-specific)
        if os.path.exists(f"/dev/shm/{SHM_NAME}"):
            os.remove(f"/dev/shm/{SHM_NAME}")
        logging.info("Shared memory segment cleaned up.")
    except Exception as e:
        logging.error(f"Error cleaning up shared memory: {e}")

def signal_handler(signum, frame):
    """
    Handles SIGINT and SIGTERM signals for graceful shutdown.
    """
    logging.info(f"Signal {signum} received. Shutting down...")
    cleanup_shm()
    sys.exit(0)

def worker_process(shm_name, shm_size, request_queue, shared_high_water_mark):
    """
    Worker process function to handle requests.
    """
    # Each worker process will open the shared memory segment
    with open(f"/dev/shm/{shm_name}", "r+b") as f:
        with contextlib.closing(mmap.mmap(f.fileno(), shm_size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)) as shm:
            while True:
                handle_request(shm, request_queue, shared_high_water_mark)
                time.sleep(0.1)  # Throttle request handling

def run_garbage_collector(stop_event):
    """
    Thread function to run garbage collection periodically.
    """
    while not stop_event.is_set():
        garbage_collect()
        time.sleep(GC_INTERVAL)

if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create a request queue (not currently used but could be useful for more complex logic)
    request_queue = multiprocessing.Queue()

    # Create a shared value to track the highest shared memory usage
    shared_high_water_mark = multiprocessing.Value('i', 0)

    # Create and map the shared memory segment
    try:
        # Create a file of the desired size
        with open(f"/dev/shm/{SHM_NAME}", "w+b") as f:
            f.truncate(SHM_SIZE)

        # Start worker processes
        processes = []
        for _ in range(NUM_WORKERS):
            p = multiprocessing.Process(target=worker_process, args=(SHM_NAME, SHM_SIZE, request_queue, shared_high_water_mark))
            p.start()
            processes.append(p)
        
        # Create an event to stop the garbage collector thread
        stop_gc_event = threading.Event()

        # Start the garbage collector thread
        gc_thread = threading.Thread(target=run_garbage_collector, args=(stop_gc_event,))
        gc_thread.start()

        with open(f"/dev/shm/{SHM_NAME}", "r+b") as f:
            with contextlib.closing(mmap.mmap(f.fileno(), SHM_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)) as shm:
                # Keep the main process alive (for now)
                while True:
                    time.sleep(1)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        cleanup_shm()
        sys.exit(1)
    finally:
        # Stop the garbage collector thread
        stop_gc_event.set()
        gc_thread.join()