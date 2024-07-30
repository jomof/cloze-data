#!/usr/bin/env python3
import sys
import yaml
import json

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def str_presenter(dumper, data):
    # If the string has newline characters, use block style
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
yaml.add_representer(str, str_presenter, Dumper=MyDumper)


def clean(data):
    def replace_colons(value):
        if isinstance(value, str):
            value = '\n'.join(line.strip() for line in value.split('\n'))
            if value.startswith('http'):
                return value
            return value.replace("  ", " ").replace("\n\n\n", "\n\n")
        elif isinstance(value, dict):
            return {k: replace_colons(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_colons(i) for i in value]
        else:
            return value
    return replace_colons(data)


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
            
            dump = yaml.dump(result, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)
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
