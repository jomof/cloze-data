#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
import zipfile

app = Flask(__name__)

# Directory where our cached data will be stored as .zip
CACHE_DIR = '/workspaces/cloze-data/cache_data'
os.makedirs(CACHE_DIR, exist_ok=True)

# How many results to keep
MAX_ENTRIES = 500  # Change this to any desired value

# Plaintext password (for demonstration only, not secure)
ZIP_PASSWORD = b"plaintext-password"

@app.route('/cache/<string:key>', methods=['GET'])
def get_value(key):
    """
    GET /cache/<key>
    Returns the stored value for <key>, or None if no file exists.
    Updates the file's modification time if it exists (to count as "most recently accessed").
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")
    if not os.path.exists(zip_path):
        return jsonify({"value": None}), 200

    # Touch the ZIP file to update its modification time (most recently accessed).
    os.utime(zip_path, None)

    try:
        data_obj = read_data_from_zip(zip_path, ZIP_PASSWORD)
        if data_obj is None:
            # Means we couldn't read or decode it
            return jsonify({"value": None}), 200
        
        # Return the stored value (the key we read is optional for verifying correctness)
        return jsonify({"value": data_obj["value"]}), 200
    except Exception as e:
        app.logger.error(f"Error reading from {zip_path}: {e}")
        return jsonify({"value": None}), 200

@app.route('/cache/<string:key>', methods=['POST'])
def set_value(key):
    """
    POST /cache/<key>
    Expects a JSON body with {"value": ...}.
    Stores the value in a password-protected ZIP with separate key.txt/value.txt files.
    Then performs garbage collection to keep only the most recently accessed N results.
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")

    payload = request.get_json()
    if not payload or "value" not in payload:
        return jsonify({"error": "Missing 'value' in JSON payload"}), 400

    # Write data into the ZIP
    for i in range(10):
        try:
            write_data_to_zip(zip_path, key, payload["value"], ZIP_PASSWORD)
            # Touch the zip file
            os.utime(zip_path, None)
            break
        except Exception as e:
            app.logger.error(f"Error writing to {zip_path}: {e}")
            return jsonify({"error": "Could not store data"}), 500

    # Run garbage collection
    garbage_collect(MAX_ENTRIES)

    return jsonify({"success": True}), 200

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

def garbage_collect(max_entries):
    """
    Keep only the most recent `max_entries` zip files in the cache,
    where "most recent" is determined by file modification time (mtime).
    """
    all_files = [
        os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)
        if f.endswith('.zip')
    ]
    if len(all_files) <= max_entries:
        return

    # Sort by modification time descending: newest first
    all_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    old_files = all_files[max_entries:]
    for old_file in old_files:
        try:
            os.remove(old_file)
            app.logger.info(f"Garbage collected: {old_file}")
        except OSError as e:
            app.logger.error(f"Error removing {old_file}: {e}")

if __name__ == '__main__':
    # Run service on localhost:5000
    app.run(debug=True, host='127.0.0.1', port=5000)
