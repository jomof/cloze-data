#!/usr/bin/env python3
from bs4 import BeautifulSoup
from stripper import strip_html

def main(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html = file.read()

        stripped_content = strip_html(BeautifulSoup(html, 'html.parser'))

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(stripped_content)
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        print("Usage: python script.py <filename> <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        main(input_file, output_file)
