# THIS IS client.py (modified) ---------------------------------------------------------------------------------------
import hashlib
import mmap
import contextlib
import os

# Name of the shared memory segment (must match the server)
SHM_NAME = "cache_shm"
# Maximum size of the shared memory segment (adjust as needed)
SHM_SIZE = 1024 * 1024 # 1 MB

def get_hash(func_name, *args):
    # Use MD5 to generate a unique hash combining function name and inputs
    combined_args = ":".join(map(str, args))
    return hashlib.md5(f"{func_name}:{combined_args}".encode()).hexdigest()

def memoize_to_disk(func, *args):
    """
    Memoize the result of 'func(*args)' using shared memory and a local file-based cache.
    """

    # Step 1: Create the cache key (MD5 hash).
    hash_key = get_hash(func.__name__, *args)
    
    # Step 2: Attempt to retrieve the memoized result from the cache using shared memory
    try:
        with open(f"/dev/shm/{SHM_NAME}", "r+b") as f:  # Open in read-write mode
            with contextlib.closing(mmap.mmap(f.fileno(), SHM_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)) as shm:
                # Send request to server via shared memory
                send_request_to_shm(shm, "GET", hash_key)
                
                # Read response from shared memory
                value = read_response_from_shm(shm)
                if value is not None and value != "None":
                    return value
    except FileNotFoundError:
        print("Shared memory segment not found. Is the service running?")

    # Step 3: Compute the result if not found in cache
    result = func(*args)

    # Step 4: Store in the cache using shared memory
    try:
        with open(f"/dev/shm/{SHM_NAME}", "r+b") as f:  # Open in read-write mode
            with contextlib.closing(mmap.mmap(f.fileno(), SHM_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)) as shm:
                # Send request to server via shared memory
                send_request_to_shm(shm, "POST", hash_key, result)
    except FileNotFoundError:
        print("Shared memory segment not found. Is the service running?")

    return result

def send_request_to_shm(shm, action, key, value=None):
    """
    Sends a request to the shared memory segment.
    """
    shm.seek(0)
    if action == "GET":
        request_str = f"GET:{key}\0"
    elif action == "POST":
        request_str = f"POST:{key}:{value}\0"
    shm.write(request_str.encode('utf-8'))

def read_response_from_shm(shm):
    """
    Reads a response from shared memory.
    """
    shm.seek(0)
    response_bytes = shm.read()
    # Find the null terminator
    end = response_bytes.find(b'\0')
    if end != -1:
        response_str = response_bytes[:end].decode('utf-8')
        if response_str == "None":
            return None
        return response_str
    else:
        return None