#!/usr/bin/env python3
import sys
import yaml
import json
from dumpyaml import dump_yaml
import argparse

def clean(data):
    def replace(value):
        if isinstance(value, str):
            # Strip each line and join them back together with a newline
            value = '\n'.join(line.strip() for line in value.split('\n'))
            if value.startswith('http'):
                return value  # Keep URLs unchanged

            # Dictionary of replacements
            replacements = {
                "  ": " ",  # Replace double spaces with single space
                "\n\n\n": "\n\n",  # Replace triple newlines with double newlines
                "　": " ",  # Replace full-width space with half-width space
                "–": "-",  # Replace en-dash with hyphen
                "’": "'",  # Replace right single quotation mark with apostrophe
                "：": ":",  # Replace full-width colon with standard colon
                "？": "?"  # Replace full-width question mark with standard question mark
            }

            # Apply replacements
            for old, new in replacements.items():
                value = value.replace(old, new)

            return value if value else None  # Treat empty strings as None

        elif isinstance(value, dict):
            # Recursively clean each value in the dictionary, removing keys with None, empty strings, or empty lists
            return {k: replace(v) for k, v in value.items() if v not in (None, [], "")}
        elif isinstance(value, list):
            # Recursively clean each item in the list, removing empty arrays
            cleaned_list = [replace(i) for i in value]
            return [item for item in cleaned_list if item != []]  # Filter out empty arrays
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Input file path')
    parser.add_argument('--destination', required=True, help='Output file path')
    args = parser.parse_args()

    main(args.source, args.destination)
