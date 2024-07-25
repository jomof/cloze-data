#!/usr/bin/env python3
import sys
import zipfile

def zip_files(output, files):
    with zipfile.ZipFile(output, 'w') as zipf:
        for file in files:
            zipf.write(file, arcname=file)

if __name__ == "__main__":
    output = sys.argv[0]
    files = []
    i = 1
    while i < len(sys.argv):
        files.append(sys.argv[i])
        i += 1

    zip_files(output, files)
