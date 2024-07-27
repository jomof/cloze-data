#!/usr/bin/env python3
import zipfile
import os
import subprocess
import argparse
import shutil
import concurrent.futures
import queue

def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

def process_file(shell_script, input_file, output_file):
    try:
        subprocess.run([shell_script, input_file, input_file, output_file], check=True)
    except subprocess.CalledProcessError:
        pass  # Handle the error according to your needs

def unzip_files(zip_in, input_dir, file_queue):
    with zipfile.ZipFile(zip_in, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            extracted_path = zip_ref.extract(file_info, input_dir)
            if os.path.isfile(extracted_path):
                file_queue.put(file_info.filename)

def process_zip(zip_in, zip_out, shell_script, num_workers):
    base_dir = 'process_zip'
    input_dir = os.path.join(base_dir, 'in')
    output_dir = os.path.join(base_dir, 'out')

    # Create the processing directories
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(input_dir)
    os.makedirs(output_dir)

    file_queue = queue.Queue()

    # Start the producer thread for unzipping files
    unzip_thread = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    unzip_future = unzip_thread.submit(unzip_files, zip_in, input_dir, file_queue)

    # Start the consumer threads for processing files
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        
        def worker_function(worker_id):
            while not unzip_future.done() or not file_queue.empty():
                try:
                    file_name = file_queue.get(timeout=1)
                except queue.Empty:
                    continue

                input_file = os.path.join(input_dir, file_name)
                output_file = os.path.join(output_dir, file_name)
                ensure_directory_exists(output_file)
                process_file(shell_script, input_file, output_file)
        
        futures = [executor.submit(worker_function, i) for i in range(num_workers)]
        
        # Ensure all futures are completed
        concurrent.futures.wait(futures)

    # Create the output zip file
    with zipfile.ZipFile(zip_out, 'w') as zip_output:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zip_output.write(file_path, arcname)

def main():
    parser = argparse.ArgumentParser(description='Process a zip file and invoke a shell script on each file.')
    parser.add_argument('zip_in', type=str, help='Path to the input zip file.')
    parser.add_argument('zip_out', type=str, help='Path to the output zip file.')
    parser.add_argument('shell_script', type=str, help='Path to the shell script.')
    parser.add_argument('--workers', type=int, default=os.cpu_count(), help='Number of worker threads (default: number of CPUs).')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.zip_in):
        print(f"The zip file {args.zip_in} does not exist.")
        return

    if not os.path.isfile(args.shell_script):
        print(f"The shell script {args.shell_script} does not exist.")
        return

    process_zip(args.zip_in, args.zip_out, args.shell_script, args.workers)

if __name__ == "__main__":
    main()
