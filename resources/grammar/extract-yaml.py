#!/usr/bin/env python3
import argparse
import os
from bs4 import BeautifulSoup

def extract_grammar_info(name, html):
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', id='grammar-data')
    data = script_tag.string.strip()
    return data

def main(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()

        grammar_info = extract_grammar_info(os.path.basename(input_file), html_content)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(grammar_info)
        
    except Exception as e:
        print(f"Error processing file {input_file}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Input file path')
    parser.add_argument('--destination', required=True, help='Output file path')
    args = parser.parse_args()
    main(args.source, args.destination)
