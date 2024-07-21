import json
import sys

def check_json_array_distinct(input_file, key_field):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    seen = set()
    duplicates = []
    for item in data:
        key_value = item.get(key_field)
        if key_value in seen:
            duplicates.append(item)
        else:
            seen.add(key_value)
    
    if duplicates:
        print(f"Duplicates found based on key '{key_field}':")
        for dup in duplicates:
            print(dup)
    else:
        print(f"No duplicates found based on key '{key_field}'.")

