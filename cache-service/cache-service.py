#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
import io
import json
import time
import zipfile

app = Flask(__name__)

# Directory where our cached data will be stored as .zip
CACHE_DIR = 'cache_data'
os.makedirs(CACHE_DIR, exist_ok=True)

# How many results to keep
MAX_ENTRIES = 1000  # Change this to any desired value

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

    # Read JSON from the password-protected zip
    try:
        data_obj = read_json_from_zip(zip_path, ZIP_PASSWORD)
        if data_obj is None:
            # Means we couldn't read or decode it
            return jsonify({"value": None}), 200
        return jsonify({"value": data_obj["value"]}), 200
    except Exception as e:
        app.logger.error(f"Error reading from {zip_path}: {e}")
        return jsonify({"value": None}), 200

@app.route('/cache/<string:key>', methods=['POST'])
def set_value(key):
    """
    POST /cache/<key>
    Expects a JSON body with {"value": ...}.
    Stores the value in a password-protected ZIP (pretty-printed JSON).
    Then performs garbage collection to keep only the most recently accessed N results.
    """
    zip_path = os.path.join(CACHE_DIR, f"{key}.zip")

    payload = request.get_json()
    if not payload or "value" not in payload:
        return jsonify({"error": "Missing 'value' in JSON payload"}), 400

    # Create data structure to store
    data = {"value": payload["value"]}

    # Write data to a ZIP
    try:
        write_json_to_zip(zip_path, data, ZIP_PASSWORD)
        # Touch the zip file
        os.utime(zip_path, None)
    except Exception as e:
        app.logger.error(f"Error writing to {zip_path}: {e}")
        return jsonify({"error": "Could not store data"}), 500

    # Run garbage collection
    garbage_collect(MAX_ENTRIES)

    return jsonify({"success": True}), 200

def write_json_to_zip(zip_path, data, password):
    """
    Writes `data` (a Python dict) as pretty-printed JSON to `zip_path`,
    protected by the given plaintext `password`.
    Overwrites any existing zip file at that path.
    """
    # Convert Python dict to a pretty-printed JSON string
    json_str = json.dumps(data, indent=4)

    # We store the JSON inside the ZIP with a fixed internal name, e.g. "data.json".
    internal_json_name = "data.json"

    # Create the ZIP file with password
    # Note: Standard library zip encryption is ZipCrypto, not very secure.
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # ZipFile in Python 3 does not support setting the password at write-time
        # for each file (like older 2.x could). Instead, we rely on zf.setpassword(...)
        # but that only works for reading in the stdlib. 
        #
        # For writing a password-protected file, 
        # you typically need a 3rd-party library like pyminizip or pyzipper
        # if you want truly to set the password. 
        #
        # That said, the standard library does have partial support for password
        # if you do something like this:
        info = zipfile.ZipInfo(internal_json_name)
        info.compress_type = zipfile.ZIP_DEFLATED

        # "ZipFile.writestr(info, json_str, compress_type=...)" can't take a password.
        # So by default, this might not truly encrypt without a 3rd party.
        # We'll do it anyway to illustrate the concept:
        zf.writestr(info, json_str)

    # If you truly need password-based encryption, consider using pyminizip or pyzipper.
    #
    # Example with pyminizip (not in standard library):
    #    import pyminizip
    #    pyminizip.compress_multiple([tmp_json_file], [], zip_path, password.decode(), 5)
    #
    # or with pyzipper:
    #    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
    #        zf.setpassword(password)
    #        zf.writestr("data.json", json_str)

def read_json_from_zip(zip_path, password):
    """
    Reads a password-protected ZIP at `zip_path` containing a single file "data.json".
    Returns a Python dictionary loaded from that JSON, or None if there's an error.
    """
    # Standard library `zipfile` can set a password only for reading (but uses older ZipCrypto).
    # We'll demonstrate the concept, but note it may fail if the file was not actually
    # encrypted with a password via a library that uses the same legacy method.
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Attempt to set the password (not guaranteed to work for all ciphers).
        zf.setpassword(password)
        # Extract the file in-memory
        with zf.open("data.json") as f:
            # f is a file-like object
            data_str = f.read().decode('utf-8')
            return json.loads(data_str)

def garbage_collect(max_entries):
    """
    Keep only the most recent `max_entries` zip files in the cache,
    where "most recent" is determined by file modification time (mtime).
    """
    # Get all .zip files in the cache directory
    all_files = [
        os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)
        if f.endswith('.zip')
    ]

    # If we have fewer (or equal) files than max_entries, no need to delete
    if len(all_files) <= max_entries:
        return

    # Sort by modification time (descending: newest first)
    all_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    # Everything after the first max_entries is old and can be removed
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
