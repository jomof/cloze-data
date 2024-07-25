#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import yaml

def extract_grammar_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    grammar_point = {}

    # Extracting title
    try:
        title_tag = soup.title
        grammar_point['title'] = title_tag.string.strip() if title_tag else 'Title not found'
    except Exception as e:
        print(f"Error extracting title: {e}")

    # Extracting grammar point and description
    try:
        grammar_info = soup.find('div', class_='grid gap-24 text-center')
        if grammar_info:
            h1_tag = grammar_info.find('h1')
            h2_tag = grammar_info.find('h2')
            grammar_point['grammar_point'] = h1_tag.text.strip() if h1_tag else 'Grammar point not found'
            grammar_point['description'] = h2_tag.text.strip() if h2_tag else 'Description not found'
        else:
            grammar_point['grammar_point'] = 'Grammar point section not found'
            grammar_point['description'] = 'Description section not found'
    except Exception as e:
        print(f"Error extracting grammar point and description: {e}")

    # Extracting structure
    try:
        structure_section = soup.find('div', id='structure')
        if not structure_section:
            structure_section = soup.find('section', id='structure')
        if structure_section:
            p_tag = structure_section.find('p')
            grammar_point['structure'] = p_tag.text.strip() if p_tag else 'Structure not found'
        else:
            print("Structure section not found")
            grammar_point['structure'] = 'Structure section not found'
    except Exception as e:
        print(f"Error extracting structure: {e}")

    # Extracting details
    try:
        details_section = soup.find('div', id='details')
        if not details_section:
            details_section = soup.find('section', id='details')
        if details_section:
            details_items = details_section.find_all('li')
            grammar_point['details'] = {}
            for item in details_items:
                h4_tag = item.find('h4')
                p_tag = item.find('p')
                key = h4_tag.text.strip() if h4_tag else 'Key not found'
                value = p_tag.text.strip() if p_tag else 'Value not found'
                grammar_point['details'][key] = value
        else:
            grammar_point['details'] = 'Details section not found'
    except Exception as e:
        print(f"Error extracting details: {e}")

    # Extracting explanation
    try:
        explanation_section = soup.find('div', id='about')
        if not explanation_section:
            explanation_section = soup.find('section', id='about')
        if explanation_section:
            writeup_body = explanation_section.find('div', class_='writeup-body')
            grammar_point['explanation'] = writeup_body.text.strip() if writeup_body else 'Explanation not found'
        else:
            print("Explanation section not found")
            grammar_point['explanation'] = 'Explanation section not found'
    except Exception as e:
        print(f"Error extracting explanation: {e}")

    # Extracting examples
    try:
        examples_section = soup.find('div', id='examples')
        if not examples_section:
            examples_section = soup.find('section', id='examples')
        if examples_section:
            examples = examples_section.find_all('div', class_='writeup-example')
            grammar_point['examples'] = []
            for example in examples:
                jp_tag = example.find('div', class_='writeup-example--japanese')
                en_tag = example.find('div', class_='writeup-example--english')
                jp = jp_tag.text.strip() if jp_tag else 'Japanese example not found'
                en = en_tag.text.strip() if en_tag else 'English example not found'
                grammar_point['examples'].append({'japanese': jp, 'english': en})
        else:
            grammar_point['examples'] = 'Examples section not found'
    except Exception as e:
        print(f"Error extracting examples: {e}")

    return grammar_point

def main(filename, input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()

        grammar_info = extract_grammar_info(html_content)

        with open(output_file, 'w', encoding='utf-8') as file:
            yaml.dump(grammar_info, file, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python script.py <filename> <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        filename = sys.argv[1]
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        main(filename, input_file, output_file)
