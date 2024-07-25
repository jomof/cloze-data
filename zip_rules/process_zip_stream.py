#!/usr/bin/env python3
import zipfile
import os
import subprocess
import argparse
import shutil

def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

def process_zip(zip_in, zip_out, shell_script):
    base_dir = 'process_zip'
    input_dir = os.path.join(base_dir, 'in')
    output_dir = os.path.join(base_dir, 'out')

    # Create the processing directories
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(input_dir)
    os.makedirs(output_dir)

    with zipfile.ZipFile(zip_in, 'r') as zip_ref:
        output_files = []
        for file_info in zip_ref.infolist():
            extracted_path = zip_ref.extract(file_info, input_dir)
            if os.path.isfile(extracted_path):
                output_file = os.path.join(output_dir, f"{file_info.filename}")
                ensure_directory_exists(output_file)
                subprocess.run([shell_script, file_info.filename, extracted_path, output_file])
                output_files.append(output_file)
    
    with zipfile.ZipFile(zip_out, 'w') as zip_output:
        for output_file in output_files:
            arcname = os.path.relpath(output_file, output_dir)
            zip_output.write(output_file, arcname)

def main():
    parser = argparse.ArgumentParser(description='Process a zip file and invoke a shell script on each file.')
    parser.add_argument('zip_in', type=str, help='Path to the input zip file.')
    parser.add_argument('zip_out', type=str, help='Path to the output zip file.')
    parser.add_argument('shell_script', type=str, help='Path to the shell script.')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.zip_in):
        print(f"The zip file {args.zip_in} does not exist.")
        return

    if not os.path.isfile(args.shell_script):
        print(f"The shell script {args.shell_script} does not exist.")
        return

    process_zip(args.zip_in, args.zip_out, args.shell_script)

if __name__ == "__main__":
    main()
