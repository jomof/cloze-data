#!/usr/bin/env python3
import yaml
import sys
from dumpyaml import dump_yaml_file

def read_yaml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def update_grammar_points(input_yaml, fixup_yaml, output_yaml):
    input_data = read_yaml_file(input_yaml)
    fixup_data = read_yaml_file(fixup_yaml)
    grammar_point_fixups = fixup_data.get('grammar_point_fixups', {})
    false_friend_fixups = fixup_data.get('false_friend_fixups', {})
    
    grammar_point = input_data.get('grammar_point')
    url = input_data.get('url')
    
    unused_fixups = []
    present_false_friends = []

    # Check if the grammar_point's URL is in the grammar_point_fixups data
    if url in grammar_point_fixups:
        new_grammar_point = grammar_point_fixups[url]
        if grammar_point != new_grammar_point:
            input_data['grammar_point'] = new_grammar_point
        else:
            unused_fixups.append(f"grammar_point_fixups[{url}] = '{new_grammar_point}'")

    # Check and fix false friends
    if url in false_friend_fixups:
        false_friends_mapping = false_friend_fixups[url]
        if 'false_friends' in input_data:
            for ff in input_data['false_friends']:
                term = ff['term']
                if term in false_friends_mapping:
                    new_term = false_friends_mapping[term]
                    if term != new_term:
                        ff['term'] = new_term
                    else:
                        unused_fixups.append(f"false_friend_fixups[{url}]['{term}'] = '{new_term}'")
                present_false_friends.append(term)
    
    if unused_fixups:
        for fixup in unused_fixups:
            if "false_friend_fixups" in fixup:
                print(f"Error: Fixup '{fixup}' available for URL '{url}' but not used in file '{input_yaml}'", file=sys.stderr)
                if present_false_friends:
                    print(f"Present false friends for URL '{url}': {', '.join(present_false_friends)}", file=sys.stderr)
            else:
                print(f"Error: Fixup '{fixup}' available for URL '{url}' but not used in file '{input_yaml}'", file=sys.stderr)
        sys.exit(1)
    
    # Write the updated or original data to the output file
    with open(output_yaml, 'w', encoding='utf-8') as file:
        dump_yaml_file(input_data, file)

def main(input_yaml, output_yaml, fixup_yaml):
    update_grammar_points(input_yaml, fixup_yaml, output_yaml)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: update_grammar_points.py <input_yaml> <output_yaml> <fixup_yaml>", file=sys.stderr)
        sys.exit(1)
    
    input_yaml = sys.argv[1]
    output_yaml = sys.argv[2]
    fixup_yaml = sys.argv[3]
    
    main(input_yaml, output_yaml, fixup_yaml)
