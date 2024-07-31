#!/usr/bin/env python3
import sys
import yaml
import json
from dumpyaml import dump_yaml


def clean(data):
    def replace(value):
        if isinstance(value, str):
            # Strip each line and join them back together with a newline
            value = '\n'.join(line.strip() for line in value.split('\n'))
            if value.startswith('http'):
                return value  # Keep URLs unchanged
            # Replace multiple spaces with a single space and excessive newlines
            return value.replace("  ", " ").replace("\n\n\n", "\n\n")
        elif isinstance(value, dict):
            # Recursively clean each value in the dictionary, removing keys with None values
            return {k: replace(v) for k, v in value.items() if v is not None}
        elif isinstance(value, list):
            # Recursively clean each item in the list
            return [replace(i) for i in value]
        else:
            return value  # Return the value unchanged if it's not a string, dict, or list

    # Start the cleaning process
    return replace(data)

def main(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = file.read()

        if input_file.endswith('.yaml'):
            data = yaml.safe_load(data)
        else:
            data = json.loads(data)

        result = clean(data)

        with open(output_file, 'w', encoding='utf-8') as file:
            
            dump = dump_yaml(result)
            file.write(dump)
        
    except Exception as e:
        print(f"Error processing file {input_file}: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        main(input_file, output_file)
