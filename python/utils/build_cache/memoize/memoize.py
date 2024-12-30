#!/usr/bin/env python3

import hashlib
import time
import socket
import struct
import base64
import logging

SOCKET_PATH = '/dev/shm/cloze.sock'
DEBUG_LOGGING = True  # Control flag for logging
LOG_FILE = './memoize-client.log'

class CacheError(Exception):
    pass

def setup_logging():
    if DEBUG_LOGGING:
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.DEBUG,
            format='%(asctime)s - %(message)s'
        )

def get_hash(func_name, *args):
    combined_args = ":".join(map(str, args))
    return hashlib.md5(f"{func_name}:{combined_args}".encode()).hexdigest()

def memoize_to_disk(caller_id, func, *args):
    setup_logging()
    hash_key = get_hash(func.__name__, *args)
    
    if DEBUG_LOGGING:
        logging.debug(f"Request - caller_id: {caller_id}, func: {func.__name__}, args: {args}")
        logging.debug(f"Generated hash: {hash_key}")
    
    response = do_socket_request(f"GET:{hash_key}:{caller_id}").strip()
    
    if DEBUG_LOGGING:
        logging.debug(f"GET response: {response}")
    
    if response.startswith("ERROR"):
        if DEBUG_LOGGING:
            logging.error(f"Server error during GET: {response}")
        raise CacheError(f"Server error during GET: {response}")
        
    if response != "None":
        decoded_response = base64.b64decode(response.encode()).decode()
        if DEBUG_LOGGING:
            logging.debug("Cache hit - decoded response: {decoded_response[:100]}...")
        print("Cache hit")
        return decoded_response
        
    print("Cache miss")
    if DEBUG_LOGGING:
        logging.debug("Cache miss - executing function")
    
    result = func(*args)
    encoded_result = base64.b64encode(str(result).encode()).decode()
    
    if DEBUG_LOGGING:
        logging.debug(f"Sending POST request with hash: {hash_key}")
    
    response = do_socket_request(f"POST:{hash_key}:{encoded_result}:{caller_id}")
    
    if DEBUG_LOGGING:
        logging.debug(f"POST response: {response}")
    
    if response.strip() != "OK":
        if DEBUG_LOGGING:
            logging.error(f"Server error during POST: {response}")
        raise CacheError(f"Server error during POST: {response}")
        
    return result

def do_socket_request(request_str: str) -> str:
    if DEBUG_LOGGING:
        logging.debug(f"Opening socket connection - request: {request_str}")
    
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # 5 second timeout
            if DEBUG_LOGGING:
                logging.debug("Connecting to socket...")
            s.connect(SOCKET_PATH)
            
            if DEBUG_LOGGING:
                logging.debug("Sending length-prefixed data...")
            send_length_prefixed(s, request_str)
            
            if DEBUG_LOGGING:
                logging.debug("Receiving response...")
            response = recv_length_prefixed(s)
            
            if DEBUG_LOGGING:
                logging.debug(f"Response received: {response[:100]}...")
            return response
    except socket.timeout:
        error_msg = "Socket timeout after 5 seconds"
        if DEBUG_LOGGING:
            logging.error(error_msg)
        raise CacheError(error_msg)
    except Exception as e:
        if DEBUG_LOGGING:
            logging.error(f"Socket error: {str(e)}")
        raise

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