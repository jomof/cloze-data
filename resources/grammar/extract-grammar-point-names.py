#!/usr/bin/env python3
import yaml
import sys

def read_yaml_files(file_paths):
    grammar_points = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            grammar_point = data.get('grammar_point')
            url = data.get('url')
            if grammar_point and url:
                grammar_points.append({'grammar_point': grammar_point, 'url': url})
    return grammar_points

def write_grammar_points_to_file(grammar_points, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        yaml.dump({'grammar_points': grammar_points}, file, allow_unicode=True)

def main(file_paths, output_file):
    # Read YAML files and extract grammar points and URLs
    grammar_points = read_yaml_files(file_paths)
    
    # Write the grammar points and URLs to a single file
    write_grammar_points_to_file(grammar_points, output_file)

if __name__ == "__main__":
    # Get file paths and output file from command-line arguments
    file_paths = sys.argv[1:-1]
    output_file = sys.argv[-1]
    
    main(file_paths, output_file)
