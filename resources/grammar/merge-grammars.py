import sys
import yaml
from dumpyaml import dump_yaml_file


#   merged_count: 211
#   dojg_only_count: 404
#   bunpro_only_count: 716

grammar_point_name_translations = {
    "べからず・べからざる": "べからず",
    "られる②": "れる・られる (Potential)",
    "(と言)ったらない": "ったらない・といったらない",
    "させる": "Verb［せる・させる］",
    "(っ)きり": "きり",
    "て": "Verb[て]",
    "なくて": "なくて (not)",
    "始める・はじめる": "はじめる",
    "終わる・おわる": "おわる",
    "難い・にくい": "にくい",
    "易い・やすい": "やすい",
}

def read_file_list(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

def read_yaml(input_file: str) -> dict:
    with open(input_file, 'r') as file:
        return yaml.safe_load(file)

def apply_translations(yaml_list, translations):
    for item in yaml_list:
        if item['grammar_point'] in translations:
            item['grammar_point'] = translations[item['grammar_point']]
    return yaml_list

def trim_elements(merged_list):
    trimmed_list = []
    for item in merged_list:
        trimmed_item = {'grammar_point': item['grammar_point']}
        
        if 'meaning' in item:
            trimmed_item['meaning'] = item['meaning']
        
        if 'bunpro' in item and item['bunpro']:
            bunpro_trimmed = {'grammar_point': item['bunpro']['grammar_point']}
            if 'meaning' in item['bunpro']:
                bunpro_trimmed['meaning'] = item['bunpro']['meaning']
            if 'examples' in item['bunpro']:
                bunpro_trimmed['examples'] = item['bunpro']['examples'][:2]
            trimmed_item['bunpro'] = bunpro_trimmed
        
        if 'dojg' in item and item['dojg']:
            dojg_trimmed = {'grammar_point': item['dojg']['grammar_point']}
            if 'meaning' in item['dojg']:
                dojg_trimmed['meaning'] = item['dojg']['meaning']
            if 'examples' in item['dojg']:
                dojg_trimmed['examples'] = item['dojg']['examples'][:2]
            trimmed_item['dojg'] = dojg_trimmed
        
        trimmed_list.append(trimmed_item)
    
    return trimmed_list


def merge_lists(list_one, list_two, list_name_one='one', list_name_two='two'):
    merged_dict = {}

    # Add items from the first list
    for item in list_one:
        grammar_point = item['grammar_point']
        if grammar_point not in merged_dict:
            merged_dict[grammar_point] = {'grammar_point': grammar_point, list_name_one: item, list_name_two: None}
        else:
            merged_dict[grammar_point][list_name_one] = item

    # Add items from the second list
    for item in list_two:
        grammar_point = item['grammar_point']
        if grammar_point not in merged_dict:
            merged_dict[grammar_point] = {'grammar_point': grammar_point, list_name_one: None, list_name_two: item}
        else:
            merged_dict[grammar_point][list_name_two] = item

    # Convert the dictionary back to a list
    merged_list = list(merged_dict.values())

    # Sort the merged list by 'grammar_point'
    sorted_merged = sorted(merged_list, key=lambda x: x['grammar_point'])

    return sorted_merged

def generate_statistics(merged_list, list_name_one, list_name_two):
    merged_count = 0
    dojg_only_count = 0
    bunpro_only_count = 0

    for item in merged_list:
        if item[list_name_one] and item[list_name_two]:
            merged_count += 1
        elif item[list_name_one]:
            bunpro_only_count += 1
        elif item[list_name_two]:
            dojg_only_count += 1

    return {
        'merged_count': merged_count,
        'dojg_only_count': dojg_only_count,
        'bunpro_only_count': bunpro_only_count
    }

def main():
    if len(sys.argv) != 5:
        print("Usage: merge_grammars.py <bunpro_file_list> <dojg_file_list> <output_file> <output_dir>")
        print("   bunpro_file_list and dojg_file_list contain lists of YAML files to merge")
        print("ARGS", sys.argv)
        sys.exit(1)

    bunpro_file = sys.argv[1]
    dojg_file = sys.argv[2]
    output_file = sys.argv[3]
    output_dir = sys.argv[4]

    bunpro_files = read_file_list(bunpro_file)
    dojg_files = read_file_list(dojg_file)

    bunpro_yamls = [read_yaml(f) for f in bunpro_files]
    dojg_yamls = [read_yaml(f) for f in dojg_files]

    # Apply translations to the grammar points before merging
    bunpro_yamls = apply_translations(bunpro_yamls, grammar_point_name_translations)
    dojg_yamls = apply_translations(dojg_yamls, grammar_point_name_translations)

    merged = merge_lists(bunpro_yamls, dojg_yamls, list_name_one='bunpro', list_name_two='dojg')

    statistics = generate_statistics(merged, list_name_one='bunpro', list_name_two='dojg')

    # Combine statistics and merged data
    output_data = {
        'statistics': statistics,
        'merged_data': trim_elements(merged)
    }

    with open(output_file, 'w') as f:
        dump_yaml_file(output_data, f)

if __name__ == "__main__":
    main()
