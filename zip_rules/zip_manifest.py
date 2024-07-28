#!/usr/bin/env python3
import zipfile
import sys
import os
import hashlib


def base36encode(number):
    if number < 0:
        raise ValueError("Base36 cannot encode negative numbers")

    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    base36 = ""

    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36

    return base36 or alphabet[0]


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_zip_file> <output_manifest_file>")
        sys.exit(1)

    input_zip = sys.argv[1]
    output_manifest = sys.argv[2]

    if not os.path.isfile(input_zip):
        print(f"Error: {input_zip} does not exist.")
        sys.exit(1)

    try:
        with zipfile.ZipFile(input_zip, 'r') as zip_ref:
            file_list = zip_ref.infolist()

            with open(output_manifest, 'w') as manifest_file:
                for file_info in file_list:
                    if file_info.is_dir():
                        continue  # Skip directories

                    file_name = file_info.filename

                    with zip_ref.open(file_name) as file:
                        file_content = file.read()
                        content_hash = hashlib.sha256(file_content).hexdigest()
                        content_hash_base36 = base36encode(int(content_hash, 16))

                    filename_hash = hashlib.sha256(file_name.encode()).hexdigest()
                    filename_hash_base36 = base36encode(int(filename_hash, 16))

                    manifest_file.write(f"{filename_hash_base36[:48]} {content_hash_base36[:48]} {file_name}\n")

        print(f"Manifest file created: {output_manifest}")

    except zipfile.BadZipFile:
        print(f"Error: {input_zip} is not a valid zip file.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
