#!/usr/bin/env python3

import hashlib
import time
import socket
import struct
import base64

SOCKET_PATH = '/dev/shm/cloze.sock'

class CacheError(Exception):
    pass

def get_hash(func_name, *args):
    combined_args = ":".join(map(str, args))
    return hashlib.md5(f"{func_name}:{combined_args}".encode()).hexdigest()

def memoize_to_disk(caller_id, func, *args):
    hash_key = get_hash(func.__name__, *args)
    response = do_socket_request(f"GET:{hash_key}:{caller_id}").strip()
    
    if response.startswith("ERROR"):
        raise CacheError(f"Server error during GET: {response}")
        
    if response != "None":
        decoded_response = base64.b64decode(response.encode()).decode()
        print("Cache hit")
        return decoded_response
        
    print("Cache miss")
    result = func(*args)
    encoded_result = base64.b64encode(str(result).encode()).decode()
    response = do_socket_request(f"POST:{hash_key}:{encoded_result}:{caller_id}")
    
    if response.strip() != "OK":
        raise CacheError(f"Server error during POST: {response}")
        
    return result

def do_socket_request(request_str: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCKET_PATH)
        send_length_prefixed(s, request_str)
        response = recv_length_prefixed(s)
    return response

def send_length_prefixed(sock: socket.socket, data_str: str):
    encoded = data_str.encode('utf-8')
    length_prefix = struct.pack('!I', len(encoded))
    sock.sendall(length_prefix + encoded)

def recv_length_prefixed(sock: socket.socket) -> str:
    length_data = recv_until_complete(sock, 4)
    if len(length_data) < 4:
        raise CacheError("ERROR: incomplete length data")
    msg_length = struct.unpack('!I', length_data)[0]

    raw_data = recv_until_complete(sock, msg_length)
    if len(raw_data) < msg_length:
        raise CacheError("ERROR: incomplete message data")

    return raw_data.decode('utf-8', errors='replace')

def recv_until_complete(sock: socket.socket, num_bytes: int) -> bytes:
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
        time.sleep(0.5)
        return str(a + b)

    print("First call (should miss):", memoize_to_disk("test1", slow_add, 10, 20))
    print("Second call (should hit):", memoize_to_disk("test2", slow_add, 10, 20))