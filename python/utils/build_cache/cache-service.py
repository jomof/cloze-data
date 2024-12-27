#!/usr/bin/env python3

import os
import time
import signal
import sys
import logging
import asyncio
import socket
import struct
import base64
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

SOCKET_PATH = '/dev/shm/cloze.sock'
CACHE_DIR = '/workspaces/cloze-data/cache_data'
MAX_WORKERS = 32
os.makedirs(CACHE_DIR, exist_ok=True)

MAX_ENTRIES = 2000
GC_INTERVAL = 3600

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

def sync_file_read(key: str, caller_id: str):
    logging.info(f"Reading: {key} from caller: {caller_id}")
    value_file = os.path.join(CACHE_DIR, f"{key}-value.txt")
    access_file = os.path.join(CACHE_DIR, f"{key}-access.txt")
    
    if not os.path.exists(value_file):
        return None
        
    try:
        os.utime(value_file, None)
        
        callers = set()
        if os.path.exists(access_file):
            with open(access_file, 'r', encoding='utf-8') as af:
                callers = set(af.read().splitlines())
                
        if caller_id not in callers:
            with open(access_file, 'a', encoding='utf-8') as af:
                af.write(f"{caller_id}\n")
                
        with open(value_file, 'r', encoding='utf-8') as vf:
            stored_value = vf.read()
            encoded_value = base64.b64encode(stored_value.encode()).decode()
        logging.info(f"Cache hit: {value_file} from caller: {caller_id}")
        return encoded_value
    except Exception as e:
        logging.error(f"Error reading from {value_file}: {e}")
        return None

def sync_file_write(key: str, value: str, caller_id: str):
    logging.info(f"Writing: {key} from caller: {caller_id}")
    value_file = os.path.join(CACHE_DIR, f"{key}-value.txt")
    access_file = os.path.join(CACHE_DIR, f"{key}-access.txt")
    try:
        decoded_value = base64.b64decode(value.encode()).decode()
        with open(value_file, 'w', encoding='utf-8') as vf:
            vf.write(decoded_value)
        with open(access_file, 'w', encoding='utf-8') as af:
            af.write(f"{caller_id}\n")
        logging.info(f"Wrote: {value_file} from caller: {caller_id}")
        os.utime(value_file, None)
    except Exception as e:
        logging.error(f"Error writing to {value_file}: {e}")

async def get_value(executor: ThreadPoolExecutor, key: str, caller_id: str):
    return await asyncio.get_event_loop().run_in_executor(executor, sync_file_read, key, caller_id)

async def set_value(executor: ThreadPoolExecutor, key: str, value: str, caller_id: str):
    await asyncio.get_event_loop().run_in_executor(executor, sync_file_write, key, value, caller_id)

async def garbage_collect():
    logging.info("Running garbage collection...")
    now = datetime.now()
    one_day_ago = now - timedelta(hours=24)

    try:
        all_value_files = [
            os.path.join(CACHE_DIR, f)
            for f in os.listdir(CACHE_DIR)
            if f.endswith('-value.txt')
        ]

        all_value_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

        if MAX_ENTRIES > 0:
            files_to_keep = all_value_files[:MAX_ENTRIES]
            files_to_delete = all_value_files[MAX_ENTRIES:]
        else:
            files_to_keep = all_value_files
            files_to_delete = []

        final_keep = []
        for f in files_to_keep:
            if datetime.fromtimestamp(os.path.getmtime(f)) < one_day_ago:
                files_to_delete.append(f)
            else:
                final_keep.append(f)

        deleted_count = 0
        for value_file in files_to_delete:
            try:
                access_file = value_file.replace('-value.txt', '-access.txt')
                os.remove(value_file)
                if os.path.exists(access_file):
                    os.remove(access_file)
                logging.info(f"Garbage collected: {value_file}")
                deleted_count += 1
            except OSError as e:
                logging.error(f"Error removing {value_file}: {e}")

        logging.info(f"{deleted_count} record(s) were deleted during garbage collection.")
    except Exception as e:
        logging.error(f"Error during garbage collection: {e}")
    finally:
        logging.info("Garbage collection finished.")

async def gc_task():
    while True:
        await garbage_collect()
        await asyncio.sleep(GC_INTERVAL)

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, executor: ThreadPoolExecutor):
    try:
        length_data = await reader.readexactly(4)
        msg_length = struct.unpack('!I', length_data)[0]
        
        raw_data = await reader.readexactly(msg_length)
        data = raw_data.decode('utf-8', errors='replace').strip()
        
        parts = data.split(":", 3)  # Split into max 4 parts for POST
        if len(parts) < 3:
            response = "ERROR: Invalid request format"
        else:
            action = parts[0]
            key = parts[1]
            caller_id = parts[-1]
            
            if action == "GET":
                value = await get_value(executor, key, caller_id)
                response = value if value is not None else "None"
            elif action == "POST" and len(parts) == 4:
                val = parts[2]
                await set_value(executor, key, val, caller_id)
                response = "OK"
            else:
                response = "ERROR: Invalid request format"

        encoded = response.encode('utf-8')
        writer.write(struct.pack('!I', len(encoded)))
        writer.write(encoded)
        await writer.drain()

    except asyncio.IncompleteReadError:
        logging.error("Client connection closed prematurely")
    except Exception as e:
        logging.error(f"Error handling client: {e}", exc_info=True)
        try:
            error_msg = "ERROR".encode('utf-8')
            writer.write(struct.pack('!I', len(error_msg)))
            writer.write(error_msg)
            await writer.drain()
        except Exception:
            pass
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    
    try:
        os.unlink(SOCKET_PATH)
    except OSError:
        pass

    server = await asyncio.start_unix_server(
        lambda r, w: handle_client(r, w, executor),
        SOCKET_PATH
    )
    os.chmod(SOCKET_PATH, 0o666)
    
    gc = asyncio.create_task(gc_task())
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down.")
    finally:
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass
        logging.info("Server has shut down.")