#!/usr/bin/env python3
import json
import argparse

# Function to read JSON data from a file
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to write formatted text to a file
def write_formatted_text(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for item in data:
            term = item['Term']
            if ("○○" not in term): continue
            file.write(f"{term}\n")
            for meaning in item['Meanings']:
                level = meaning['Level']
                english_term_meaning = meaning['EnglishTermMeaning']
                nuance = meaning['Nuance']
                file.write(f"  - {level}: {english_term_meaning} -> {nuance}\n")
            file.write("\n")

# Main function
def main():
    parser = argparse.ArgumentParser(description='Process JSON data and produce formatted text output.')
    parser.add_argument('input', type=str, help='Input JSON file path')
    parser.add_argument('output', type=str, help='Output text file path')
    args = parser.parse_args()

    # Read data from input file
    data = read_json(args.input)
    
    # Write formatted data to output file
    write_formatted_text(data, args.output)
    
    #print(f"Formatted data from {args.input} has been saved to {args.output}")

if __name__ == '__main__':
    main()
