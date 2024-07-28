#!/usr/bin/env python3
import hashlib
import os
import sys

def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def main(manifest_path, files):
    with open(manifest_path, 'w') as manifest:
        for filepath in files:
            file_hash = hash_file(filepath)
            manifest.write(f"{file_hash[:48]} {filepath}\n")

if __name__ == "__main__":
    manifest_path = sys.argv[1]
    files = sys.argv[2:]
    main(manifest_path, files)
