#!/usr/bin/env python3
import sys
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
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        main(input_file, output_file)
