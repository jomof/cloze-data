import os
from grammar_summary import generate_summary, save_summary
import yaml
import sys
from python.utils.visit_json.visit_json import visit_json
from python.mapreduce import MapReduce
import asyncio
from python.grammar import GRAMMAR_SCHEMA
import time

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

        # Check whether any new names are also old names
        intersection = all_old_names.intersection(all_new_names)

        # TODO: Handle case where an old name is also a new name
        if intersection:
            raise Exception(f"Renames file {renames_allowed} has a new name that is also an old name: {intersection}")
        
        # Build a map of old name to new names
        old_to_new = {}
        for new_name in renames:
            for old_name in renames[new_name]['old-names']:
                if old_name in old_to_new:
                    old_to_new[old_name].append(new_name)
                else:
                    old_to_new[old_name] = [new_name]

        # Error if any old name maps to more than one new name
        for old_name in old_to_new:
            if len(old_to_new[old_name]) > 1:
                raise Exception(f"Renames file {renames_allowed} has an old name that maps to more than one new name: {old_name} -> {old_to_new[old_name]}")

        # Replace references to old names with new names in all grammar files
        def fn(value, type_name, path):
            if type_name != 'grammarType': return
            # Strip: <suggest>: prefix from value
            stripped = value.removeprefix('<suggest>:').strip()
            if stripped in old_to_new:
                if len(old_to_new[stripped]) > 1:
                    raise Exception(f"Renames file {renames_allowed} has an old name that maps to more than one new name: {stripped} -> {old_to_new[stripped]}")
                if '<suggest>:' in value:
                    print(f"Renaming {value} to {old_to_new[stripped][0]} at {path}")
                return old_to_new[stripped][0]
  
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

        # Rename the grammar points themselves
        for rename in renames:
            old_names = renames[rename]['old-names']
            grammar_id = renames[rename]['id']
            for old_name in old_names:
                old_name = f"{grammar_id}-{old_name}.yaml"
                new_name = f"{grammar_id}-{rename}.yaml"
                old_path = os.path.join(grammar_root, old_name)
                new_path = os.path.join(grammar_root, new_name)
                if os.path.exists(old_path):
                    print(f"Renaming {old_name} to {new_name}")
                    os.rename(old_path, new_path)
                else:
                    print(f"Old path {old_path} does not exist, skipping rename to {new_path}")

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
    