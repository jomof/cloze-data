#!/usr/bin/env python3
import json
import os
from bs4 import BeautifulSoup
import yaml
from collections import OrderedDict

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

def str_presenter(dumper, data):
    # If the string has newline characters, use block style
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(str, str_presenter, Dumper=MyDumper)
yaml.add_representer(OrderedDict, dict_representer, Dumper=MyDumper)
yaml.add_constructor('tag:yaml.org,2002:map', dict_constructor, Loader=yaml.Loader)

def dump_yaml(data):
    return yaml.dump(data, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)

def dump_yaml_file(data, file):
    return yaml.dump(data, file, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)

def strip_html_tags(text):
    try:
        return BeautifulSoup(text, "html.parser").get_text(strip=True)
    except Exception as e:
        print(f"Error: {e}")
        return text

def html_to_markdown(html):
    soup = BeautifulSoup(html, 'html.parser')

    def clean_text(text):
        # Remove internal whitespace and replace multiple spaces with a single space
        return ' '.join(text.split())

    # Convert the <p> tag
    p_tag = soup.find('p')
    p_text = clean_text(p_tag.get_text()) if p_tag else ""

    # Convert the table
    markdown = f"## {p_text}\n\n"

    if table := soup.find('table'):
        rows = table.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            for col in columns:
                col_text = clean_text(col.get_text(strip=True))
                if col_text:
                    markdown += f"- {col_text}\n"

    return markdown.strip()

def process_note_fields(note_fields):
    # Split the fields by the 'u001f' separator
    subfields = note_fields.split("u001f")
    
    # Collect examples into a list of dictionaries
    examples = []
    for i in range(9, 39, 2):
        if i < len(subfields) and i + 1 < len(subfields):
            japanese = strip_html_tags(subfields[i])
            english = subfields[i + 1]
            if japanese and english:
                examples.append({"japanese": japanese, "english": english})

    # Return a dictionary of named fields
    return {
        "grammar_point": subfields[0] if len(subfields) > 0 else "",
        "description": subfields[1] if len(subfields) > 1 else "",
        "meaning": subfields[2] if len(subfields) > 2 else "",
        "level": subfields[4] if len(subfields) > 4 else "",
        "level_symbol": subfields[5] if len(subfields) > 5 else "",
        "level_japanese": subfields[6] if len(subfields) > 6 else "",
        "page": subfields[7] if len(subfields) > 7 else "",
        "examples": examples,
        "writeup": html_to_markdown(subfields[42]) if len(subfields) > 42 else "",
        "formation": html_to_markdown(subfields[43]) if len(subfields) > 43 else "",
        "part_of_speech": subfields[44] if len(subfields) > 44 else "",
        "related": subfields[45] if len(subfields) > 45 else "",
        "antonym": subfields[46] if len(subfields) > 46 else ""
    }

def sanitize_filename(filename):
    replacements = {
        "/": "・",
        " ": "",
        "（": "(",
        "）": ")",
        "(1)": "①",
        "(2)": "②",
        "(3)": "③",
        "(4)": "④",
        "(5)": "⑤",
        "(6)": "⑥",
        "(7)": "⑦",
        "(8)": "⑧",
        "(9)": "⑨",
        "(10)": "⑩",
        "(11)": "⑪",
        "(12)": "⑫",
        "(13)": "⑬",
        "(14)": "⑭",
        "(15)": "⑮",
        "(16)": "⑯",
        "(17)": "⑰",
        "(18)": "⑱",
        "(19)": "⑲",
        "(20)": "⑳"
    }
    
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    return filename.strip()

def main():
    # Read the initial JSON input from a file
    with open('collections.json', 'r', encoding='utf-8') as file:
        notes = json.load(file)

    for note in notes:
        structured_note = {
            "sfld": note["sfld"],
            "flds": process_note_fields(note["flds"])
        }
        
        # Sanitize the filename
        filename = sanitize_filename(note['sfld']) + ".yaml"
        structured_note["flds"]["grammar_point"] = os.path.splitext(filename)[0]
        print(structured_note["flds"]["grammar_point"], "--", structured_note["flds"]["meaning"] )

        # Write each structured note to a separate file
        with open(os.path.join("all", filename), 'w', encoding='utf-8') as file:
            dump_yaml_file(structured_note["flds"], file)

if __name__ == "__main__":
    main()
