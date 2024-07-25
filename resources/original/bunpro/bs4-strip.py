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
        print(f"Extracted title: {grammar_point['title']}")
    except Exception as e:
        print(f"Error extracting title: {e}")

    # Extracting grammar point and description
    try:
        grammar_info = soup.find('div', class_='grid gap-24 text-center')
        print(f"Grammar info section: {grammar_info}")
        if grammar_info:
            h1_tag = grammar_info.find('h1')
            h2_tag = grammar_info.find('h2')
            grammar_point['grammar_point'] = h1_tag.text.strip() if h1_tag else 'Grammar point not found'
            grammar_point['description'] = h2_tag.text.strip() if h2_tag else 'Description not found'
            print(f"Extracted grammar point: {grammar_point['grammar_point']}")
            print(f"Extracted description: {grammar_point['description']}")
        else:
            print("Grammar info section not found")
            grammar_point['grammar_point'] = 'Grammar point section not found'
            grammar_point['description'] = 'Description section not found'
    except Exception as e:
        print(f"Error extracting grammar point and description: {e}")

    # Extracting structure
    try:
        structure_section = soup.find('div', id='structure')
        if not structure_section:
            structure_section = soup.find('section', id='structure')
        print(f"Structure section: {structure_section}")
        if structure_section:
            p_tag = structure_section.find('p')
            grammar_point['structure'] = p_tag.text.strip() if p_tag else 'Structure not found'
            print(f"Extracted structure: {grammar_point['structure']}")
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
        print(f"Details section: {details_section}")
        if details_section:
            details_items = details_section.find_all('li')
            grammar_point['details'] = {}
            for item in details_items:
                h4_tag = item.find('h4')
                p_tag = item.find('p')
                key = h4_tag.text.strip() if h4_tag else 'Key not found'
                value = p_tag.text.strip() if p_tag else 'Value not found'
                grammar_point['details'][key] = value
                print(f"Extracted detail - {key}: {value}")
        else:
            print("Details section not found")
            grammar_point['details'] = 'Details section not found'
    except Exception as e:
        print(f"Error extracting details: {e}")

    # Extracting explanation
    try:
        explanation_section = soup.find('div', id='about')
        if not explanation_section:
            explanation_section = soup.find('section', id='about')
        print(f"Explanation section: {explanation_section}")
        if explanation_section:
            writeup_body = explanation_section.find('div', class_='writeup-body')
            grammar_point['explanation'] = writeup_body.text.strip() if writeup_body else 'Explanation not found'
            print(f"Extracted explanation: {grammar_point['explanation']}")
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
        print(f"Examples section: {examples_section}")
        if examples_section:
            examples = examples_section.find_all('div', class_='writeup-example')
            grammar_point['examples'] = []
            for example in examples:
                jp_tag = example.find('div', class_='writeup-example--japanese')
                en_tag = example.find('div', class_='writeup-example--english')
                jp = jp_tag.text.strip() if jp_tag else 'Japanese example not found'
                en = en_tag.text.strip() if en_tag else 'English example not found'
                grammar_point['examples'].append({'japanese': jp, 'english': en})
                print(f"Extracted example - Japanese: {jp}, English: {en}")
        else:
            print("Examples section not found")
            grammar_point['examples'] = 'Examples section not found'
    except Exception as e:
        print(f"Error extracting examples: {e}")

    return grammar_point

def main(filename, input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
            print(f"Read HTML content from {input_file}")

        grammar_info = extract_grammar_info(html_content)

        with open(output_file, 'w', encoding='utf-8') as file:
            yaml.dump(grammar_info, file, allow_unicode=True, default_flow_style=False, sort_keys=False)
            print(f"Written YAML content to {output_file}")
        
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
        print("START BS4 PROCESSING", filename, input_file, output_file)
        main(filename, input_file, output_file)
        print("END BS4 PROCESSING", input_file, output_file)
