#!/usr/bin/env python3
"""
Unix domain socket-based client that sends GET/POST requests to the server
for memoizing results on disk.
"""

import hashlib
import time
import socket
import struct

SOCKET_PATH = '/dev/shm/cloze.sock'

def get_hash(func_name, *args):
    combined_args = ":".join(map(str, args))
    return hashlib.md5(f"{func_name}:{combined_args}".encode()).hexdigest()

def memoize_to_disk(func, *args):
    """
    1. Generate a cache key
    2. GET from server
    3. If 'None', compute result, POST to server
    4. Return result
    """
    hash_key = get_hash(func.__name__, *args)
    response = do_socket_request(f"GET:{hash_key}").strip()
    if response != "None":
        # print("Cache hit")
        return response

    # print("Cache miss")
    result = func(*args)
    _ = do_socket_request(f"POST:{hash_key}:{result}")
    return result

def do_socket_request(request_str: str) -> str:
    """
    Sends `request_str` with a 4-byte length prefix, then waits for
    a length-prefixed response from the server.
    """
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCKET_PATH)
        send_length_prefixed(s, request_str)
        response = recv_length_prefixed(s)
    return response

def send_length_prefixed(sock: socket.socket, data_str: str):
    """
    Pack 4-byte length + UTF-8 encoded data, send to server.
    """
    encoded = data_str.encode('utf-8')
    length_prefix = struct.pack('!I', len(encoded))
    sock.sendall(length_prefix + encoded)

def recv_length_prefixed(sock: socket.socket) -> str:
    """
    Reads a 4-byte length, then reads exactly that many bytes,
    returns as a UTF-8 decoded string.
    """
    length_data = recv_until_complete(sock, 4)
    if len(length_data) < 4:
        return "ERROR: incomplete length data"
    msg_length = struct.unpack('!I', length_data)[0]

    raw_data = recv_until_complete(sock, msg_length)
    if len(raw_data) < msg_length:
        return "ERROR: incomplete message data"

    return raw_data.decode('utf-8', errors='replace')

def recv_until_complete(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Reads exactly num_bytes from the socket, looping until completed or EOF.
    """
    chunks = []
    bytes_recd = 0
    while bytes_recd < num_bytes:
        chunk = sock.recv(min(num_bytes - bytes_recd, 4096))
        if not chunk:
            break
        chunks.append(chunk)
        bytes_recd += len(chunk)
    return b''.join(chunks)

if __name__ == "__main__":
    def slow_add(a, b):
        time.sleep(0.5)  # simulate expensive operation
        return str(a + b)

    print("First call (should miss):", memoize_to_disk(slow_add, 10, 20))
    print("Second call (should hit):", memoize_to_disk(slow_add, 10, 20))