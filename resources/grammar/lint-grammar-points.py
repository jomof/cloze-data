from python.mapreduce import MapReduce
import os
import asyncio
import sys
from collections import OrderedDict
import cProfile
import yaml
import json
from python.grammar import clean_lint, GRAMMAR_SCHEMA
from python.utils.visit_json import visit_json

if __name__ == '__main__':
    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    # read the prior grammar summary file
    grammar_summary_file = os.path.join(grammar_root, 'summary/summary.json')
    with open(grammar_summary_file, 'r', encoding='utf-8') as f:
        grammar_summary_content = f.read()
    grammar_summary_obj = json.loads(grammar_summary_content)

    if not os.path.isdir(grammar_root):
        print(f"ERROR: “{grammar_root}” is not a directory.")
        sys.exit(1)

    def deserialize_yaml(raw: str):
        return yaml.load(raw, Loader=yaml.CSafeLoader)

    def logic(parsed_obj, file_path):
        result = clean_lint(parsed_obj, file_path, grammar_summary_obj)
        return result
    
    file_renames = []
    splits = []
    non_renames = []
    
    def fold(accumulated, current):
        if accumulated is None:
            accumulated = OrderedDict()
        if 'all-grammar-points' not in accumulated:
            accumulated['all-grammar-points'] = {}
        subset = {
            'grammar_point': current['grammar_point'],
            'meaning': current.get('meaning'),
        }
        better_grammar_point_name = current.get('better_grammar_point_name', [])
        if len(better_grammar_point_name) == 1 and '/' not in better_grammar_point_name[0] and ':' not in better_grammar_point_name[0]:
            file_renames.append({
                'old-id': current['id'],
                'old-grammar-point': current['grammar_point'],
                'new-grammar-point': better_grammar_point_name[0]
            })
        elif len(better_grammar_point_name) == 2 and '/' not in better_grammar_point_name[0] and ':' not in better_grammar_point_name[0]:
            splits.append({
                'id': current['id'],
                'grammar_point': current['grammar_point'],
                'better_grammar_point_name': better_grammar_point_name
            })
        else:
            non_renames.append({
                'id': current['id'],
                'grammar_point': current['grammar_point'],
            })
        accumulated['all-grammar-points'][current['grammar_point']] = subset
        return accumulated
    
    def serialize_json(obj):
        return json.dumps(obj, ensure_ascii=False, indent=4)

    mr = MapReduce(
        input_dir            = grammar_root,
        output_dir           = grammar_root,
        map_func_name        = 'linting',
        map_func             = logic,        # or a sync function
        fold_func            = fold,
        deserialize_func     = deserialize_yaml,
        serialize_func       = serialize_json,
        temp_dir             = os.path.join(workspace_root, '.temp'),
        max_threads          = 4,
    )

    asyncio.run(mr.run())

    if not file_renames and not splits:
        sys.exit()
    
    # Read the summary file
    summary_file = os.path.join(grammar_root, 'summary/summary.json')
    with open(summary_file, 'r', encoding='utf-8') as f:
        summary_content = f.read()
    summary = json.loads(summary_content)    

    if file_renames:
        print(f"Found {len(file_renames)} grammar points to rename.")

        all_grammar_points = summary['all-grammar-points']
        old_to_new = { }

        # Loop over each and specify the old and new file names
        for rename in file_renames:
            old_file_name = f"{grammar_root}/{rename['old-id']}-{rename['old-grammar-point']}.yaml"
            new_file_name = f"{grammar_root}/{rename['old-id']}-{rename['new-grammar-point']}.yaml"

            if not os.path.exists(old_file_name):
                raise FileNotFoundError(f"File not found: {old_file_name}")
            if os.path.exists(new_file_name):
                raise FileExistsError(f"File already exists: {new_file_name}")
            if rename['old-grammar-point'] not in all_grammar_points:
                raise KeyError(f"Old grammar point not found in summary: {rename['old-grammar-point']}")
            if rename['new-grammar-point'] in all_grammar_points:
                raise KeyError(f"New grammar point already exists in summary: {rename['new-grammar-point']}")
            if rename['old-grammar-point'] in old_to_new:
                raise KeyError(f"Old grammar point already exists in old_to_new mapping: {rename['old-grammar-point']}")
                    
            rename['old-file'] = old_file_name
            rename['new-file'] = new_file_name
            old_to_new[rename['old-grammar-point']] = rename['new-grammar-point']

        for non_rename in non_renames:
            grammar_point = non_rename['grammar_point']
            if grammar_point in old_to_new:
                raise KeyError(f"Grammar point '{grammar_point}' already exists in old_to_new mapping. Should they be merged?")
            old_to_new[grammar_point] = grammar_point

        # Rename the grammar points in summary
        for rename in file_renames:
            old_grammar_point_name = rename['old-grammar-point']
            new_grammar_point_name = rename['new-grammar-point']

            if old_grammar_point_name not in all_grammar_points:
                raise KeyError(f"Old grammar point not found in summary: {old_grammar_point_name}")
            
            grammar_point = all_grammar_points.pop(old_grammar_point_name)

            if old_grammar_point_name in all_grammar_points:
                raise KeyError(f"Old grammar point still exists in summary after pop: {old_grammar_point_name}")
            
            grammar_point['grammar_point'] = new_grammar_point_name
            grammar_point['old_grammar_point'] = old_grammar_point_name
            all_grammar_points[new_grammar_point_name] = grammar_point

        def fn(value, type_name, path):
            if type_name != 'knownGrammarType':
                return
            return old_to_new.get(value, value)

        # Iterate through renames, load the file, change the grammar point, remove 'better_grammar_point_name' if it exists, and write the file
        for rename in file_renames:
            old_file_name = rename['old-file']
            new_file_name = rename['new-file']

            # Load the YAML file
            with open(old_file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            parsed_obj = deserialize_yaml(content)

            # Update the grammar point
            parsed_obj['grammar_point'] = rename['new-grammar-point']
            
            # Remove 'better_grammar_point_name' if it exists
            if 'better_grammar_point_name' in parsed_obj:
                del parsed_obj['better_grammar_point_name']

            # Update references to grammar points in the JSON structure
            visit_json(parsed_obj, GRAMMAR_SCHEMA, fn)

            # Lint it again
            parsed_obj = clean_lint(parsed_obj, new_file_name, summary)

            # Write the updated content to the new file
            with open(new_file_name, 'w', encoding='utf-8') as f:
                json.dump(parsed_obj, f, ensure_ascii=False, indent=4)

            # Optionally remove the old file
            os.remove(old_file_name)

        # Look through the non-renames and ensure any references to a changed grammar point are updated
        for non_rename in non_renames:
            filename = f"{grammar_root}/{non_rename['id']}-{non_rename['grammar_point']}.yaml"
            if not os.path.exists(filename):
                raise FileNotFoundError(f"File not found: {filename}")
            # Load the YAML file
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            parsed_obj = deserialize_yaml(content)

            # Fix grammar point references
            visit_json(parsed_obj, GRAMMAR_SCHEMA, fn)

            # Lint it again
            parsed_obj = clean_lint(parsed_obj, filename, summary)

            # Write the updated content to the new file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(parsed_obj, f, ensure_ascii=False, indent=4)

        # Write the updated summary back to the file
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        print(f"{len(file_renames)} grammar point renames executed.")

    if splits:
        print(f"Found {len(splits)} grammar points to split.")
        for split in splits:
            old_file_name = f"{grammar_root}/{split['id']}-{split['grammar_point']}.yaml"
            if not os.path.exists(old_file_name):
                raise FileNotFoundError(f"File not found: {old_file_name}")
            # Load the YAML file
            with open(old_file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            parsed_obj = deserialize_yaml(content)
            os.remove(old_file_name)
            del summary['all-grammar-points'][split['grammar_point']]

            # Create new files for each better grammar point name
            for better_grammar_point_name in split['better_grammar_point_name']:
                new_file_name = f"{grammar_root}/{split['id']}-{better_grammar_point_name}.yaml"

                 # Remove 'better_grammar_point_name' if it exists
                if 'better_grammar_point_name' in parsed_obj:
                    del parsed_obj['better_grammar_point_name']

                summary['all-grammar-points'][better_grammar_point_name] = {
                    'grammar_point': better_grammar_point_name,
                    'old_grammar_point': split['grammar_point'],
                    'split': True,
                }

                new_object = {
                    'id': parsed_obj['id'],
                    'grammar_point': better_grammar_point_name,
                    'split_predecessor': repr(parsed_obj),
                }

                # Write the updated content to the new file
                with open(new_file_name, 'w', encoding='utf-8') as f:
                    json.dump(new_object, f, ensure_ascii=False, indent=4)

        # Write the updated summary back to the file
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
 
