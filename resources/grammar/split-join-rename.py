import os
from grammar_summary import generate_summary, save_summary
import yaml
import sys
from python.utils.visit_json.visit_json import visit_json
from python.mapreduce import MapReduce
import asyncio
from python.grammar import GRAMMAR_SCHEMA
import time
import json

if __name__ == '__main__':
    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    # The name of the renames file
    renames_allowed = os.path.join(grammar_root, 'summary/renames-allowed.yaml')

    # Generate the grammary summary object
    grammar_summary = generate_summary(grammar_root, ['id', 'better_grammar_point_name'])
    save_summary(grammar_summary, grammar_root, 'split-join-rename-summary.json')
    print(f"Generated grammar summary with {len(grammar_summary['all-grammar-points'])} grammar points.")

    if os.path.exists(renames_allowed):
        print(f"Renames file {renames_allowed} exists, renaming now.")
        # Read the renames-allowed.yaml file
        with open(renames_allowed, 'r', encoding='utf-8') as f:
            renames = yaml.safe_load(f)
        # Make a set of all old names
        all_old_names = set()
        for new_name in renames:
            for old_name in renames[new_name]['old-names']:
                all_old_names.add(old_name)
        # Make a set of all new names
        all_new_names = set(renames.keys())
        
        # Build a map of old name to new names
        old_to_new = {}
        for new_name in renames:
            for old_name in renames[new_name]['old-names']:
                if old_name in old_to_new:
                    old_to_new[old_name].append(new_name)
                else:
                    old_to_new[old_name] = [new_name]

        # Check for cases where items are split into multiple new names
        split_new_names = set()
        for old_name in old_to_new:
            if len(old_to_new[old_name]) > 1:
                split_new_names.add(new_name)
                print(f"Splitting {old_name} -> {old_to_new[old_name]}")

        # Replace references to old names with new names in all grammar files
        def fn(value, type_name, path):
            if type_name == None: 
                for act in ['before', 'after']:
                    learn = value.get(f'learn_{act}', [])
                    result = []
                    for grammar_point in learn:
                        stripped = grammar_point.removeprefix('<suggest>:').strip()
                        if stripped in old_to_new:
                            result.extend(old_to_new[stripped])
                        else:
                            result.append(grammar_point)
                    value[f'learn_{act}'] = result
                
                return value
            if type_name != 'grammarType': return
            # Strip: <suggest>: prefix from value
            stripped = value.removeprefix('<suggest>:').strip()
            if stripped in old_to_new:
                if '<suggest>:' in value:
                    print(f"Renaming {value} to {old_to_new[stripped][0]} at {path}")
                return old_to_new[stripped][0]
            return value
  
        def logic(parsed_obj, file_path):
            better_names = parsed_obj.get('better_grammar_point_name', [])
            if len(better_names) == 1 and parsed_obj['grammar_point'] in old_to_new:
                del parsed_obj['better_grammar_point_name']
            visit_json(parsed_obj, GRAMMAR_SCHEMA, fn)
            return parsed_obj
        
        mr = MapReduce(
            input_dir            = grammar_root,
            output_dir           = grammar_root,
            map_func_name        = 'replacing grammar point references',
            map_func             = logic,        # or a sync function
            max_threads          = 4,
        )

        asyncio.run(mr.run())

        # Copy old name to new name files
        old_name_paths = set()
        new_name_paths = set()
        for new_name in renames:
            old_names = renames[new_name]['old-names']
            grammar_id = renames[new_name]['id']
            new_id_name = f"{grammar_id}-{new_name}"
            for old_name in old_names:
                old_id_name = f"{grammar_id}-{old_name}"
                old_path = os.path.join(grammar_root, old_id_name + '.yaml')
                new_path = os.path.join(grammar_root, new_id_name + '.yaml')
                old_name_paths.add(old_path)
                new_name_paths.add(new_path)
                if old_path != new_path and not os.path.exists(new_path):
                    # Read the old content
                    with open(old_path, 'r', encoding='utf-8') as f:
                        content = f.read() 
                    if old_name in old_to_new and len(old_to_new[old_name]) > 1:
                        all_new_names = old_to_new[old_name]
                        new_names_list = ', '.join(f"'{item}'" for item in all_new_names)
                        header = f"An old grammar point, '{old_name}', has been split into multiple new names: {new_names_list}. You are working on '{new_name}', please be sure to call out the distinction between this new point and the other new points. "
                    else:
                        header = f"An old grammar point has had its name changed from '{old_name}' to '{new_name}'. "

                    old_grammar_obj = yaml.safe_load(content)
                    new_content = {
                        'grammar_point': new_name,
                        'id': grammar_id,
                        'learn_before': old_grammar_obj['learn_before'],
                        'learn_after': old_grammar_obj['learn_after'],
                        'split_predecessor': 
                            f"{header}"
                            f"Please recreate this grammar point with this information in mind. All fields **MUST** be suitable for the new name. "
                            f"For your reference, here is the old content:\n\n{content}",
                        'lint-errors': [f"You **MUST** repopulate this grammar point with the new name '{new_name}' in mind. All fields **MUST** be suitable for the new name."],
                    }
                
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(new_content, ensure_ascii=False, indent=2))
      
   
    
        # Remove old name files that are not in the new name paths
        for old_path in old_name_paths:
            if old_path not in new_name_paths:
                print(f"Removing old name file {old_path}")
                os.remove(old_path)

        # Rename the renames-allowed.yaml file to renames-allowed.yaml.bak
        os.rename(renames_allowed, renames_allowed + f'-{int(time.time())}.bak')

        # Regenerate summary
        grammar_summary = generate_summary(grammar_root)
        save_summary(grammar_summary, grammar_root)
        sys.exit(0)

    # Create a map of renames
    # {
    #   'better-name': {
    #     'id': 'gp0001',
    #     'old-names': ['old-name-1', 'old-name-2'],
    #   }
    # }
    renames = {} # Key is new name, value is list of old names
    for grammar_point_name in grammar_summary['all-grammar-points']:
        summary_point = grammar_summary['all-grammar-points'][grammar_point_name]
        better_names = summary_point.get('better_grammar_point_name')
        if not better_names:
            continue

        for better_name in better_names:
            if better_name not in summary_point:
                node = renames.get(better_name, { 'id': summary_point['id'], 'old-names': [] })
                node['old-names'].append(grammar_point_name)
                renames[better_name] = node

    # Save the renames-allowed.yaml file
    if len(renames) > 0:
        print(f"Found {len(renames)} renames, saving to {os.path.basename(renames_allowed)}.")
        print(f"Check that file and then re-run this script to apply the renames.")
        with open(renames_allowed, 'w', encoding='utf-8') as f:
            yaml.dump(renames, f, allow_unicode=True)
    else:
        print(f"No renames found.")
    