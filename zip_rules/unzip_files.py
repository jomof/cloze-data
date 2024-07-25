#!/usr/bin/env python3
import sys
import zipfile
import os

def unzip_file(zip_path, output_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

if __name__ == "__main__":
    zip_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    unzip_file(zip_path, output_dir)
