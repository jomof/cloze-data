import sys
import os
import yaml

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except IOError as e:
        print(f"Error reading file '{file_path}': {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <output_file> <input_file1> <input_file2> ... <input_fileN>")
        return

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    output_data = {}
    for input_file in input_files:
        content = read_file(input_file)
        if content is not None:
            file_name = os.path.basename(input_file)
            output_data[file_name] = content

    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            yaml.dump(output_data, outfile, allow_unicode=True, default_flow_style=False, indent=4)
        print(f"Data successfully written to '{output_file}'")
    except IOError as e:
        print(f"Error writing to file '{output_file}': {e}")

if __name__ == "__main__":
    main()
