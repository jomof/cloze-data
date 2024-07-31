#!/usr/bin/env python3
import yaml
import sys
from collections import defaultdict

def read_yaml_files(file_paths):
    grammar_points = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            grammar_point = data.get('grammar_point')
            url = data.get('url')
            false_friends = data.get('false_friends', [])
            if grammar_point and url:
                grammar_points.append({
                    'grammar_point': grammar_point,
                    'url': url,
                    'false_friends': false_friends,
                    'file_path': file_path
                })
    return grammar_points

def check_for_duplicates(grammar_points):
    grammar_point_dict = defaultdict(list)
    for entry in grammar_points:
        grammar_point_dict[entry['grammar_point']].append(entry['url'])
    
    duplicates = {gp: urls for gp, urls in grammar_point_dict.items() if len(urls) > 1}
    return duplicates

def check_false_friends(grammar_points):
    all_grammar_points = {entry['grammar_point'] for entry in grammar_points}
    missing_false_friends = defaultdict(list)
    
    for entry in grammar_points:
        for false_friend in entry['false_friends']:
            term = false_friend['term']
            if term not in all_grammar_points:
                missing_false_friends[entry['url']].append({"term": term, "file_path": entry['file_path']})
    
    return missing_false_friends

def main(input_files, lint_report_file):
    grammar_points = read_yaml_files(input_files)
    duplicates = check_for_duplicates(grammar_points)
    missing_false_friends = check_false_friends(grammar_points)
    
    with open(lint_report_file, 'w', encoding='utf-8') as report:
        if duplicates:
            for gp, urls in duplicates.items():
                error_message = f"Duplicate grammar point '{gp}' found in the following URLs:"
                print(error_message, file=sys.stderr)
                print(error_message, file=report)
                for url in urls:
                    url_message = f"  - {url}"
                    print(url_message, file=sys.stderr)
                    print(url_message, file=report)
        
        if missing_false_friends:
            for url, terms in missing_false_friends.items():
                for term_info in terms:
                    term = term_info['term']
                    file_path = term_info['file_path']
                    error_message = f"False friend term '{term}' not found in grammar points for URL '{url}' in file '{file_path}'."
                    print(error_message, file=sys.stderr)
                    print(error_message, file=report)
        
        if duplicates or missing_false_friends:
            sys.exit(1)
        else:
            success_message = "No duplicates or missing false friend terms found."
            print(success_message)
            print(success_message, file=report)
            sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: bunpro-lint.py <input_yaml_file1> [<input_yaml_file2> ...] <output-lint-report>", file=sys.stderr)
        sys.exit(1)
    
    input_files = sys.argv[1:-1]
    lint_report_file = sys.argv[-1]
    main(input_files, lint_report_file)
