import asyncio
import json
import logging
import os
import sys
import time

import yaml

from grammar_summary import generate_summary, save_summary
from python.console import display
from python.grammar import GRAMMAR_SCHEMA, clean_lint
from python.mapreduce import MapReduce
from python.utils.visit_json.visit_json import visit_json

def check_renames_allowed(renames, grammar_summary):
    """
    Check that all old grammar point names in renames exist in grammar summary.
    Also check for no-op renames where new name equals old name with single old name.
    If any issues are found, display warnings and return False. Otherwise return True.
    """
    missing_names = []
    noop_renames = []
    all_grammar_points = grammar_summary.get('all-grammar-points', {})
    
    for new_name, old_names_list in renames.items():
        # Check for no-op rename: new name same as old name when there's only one old name
        if len(old_names_list) == 1 and new_name == old_names_list[0]:
            noop_renames.append(new_name)
        
        for old_name in old_names_list:
            if old_name not in all_grammar_points:
                missing_names.append(old_name)
    
    has_errors = False
    
    if missing_names:
        for missing_name in missing_names:
            display.warn(f"Old grammar point name '{missing_name}' not found in grammar summary")
        display.warn(f"Found {len(missing_names)} missing grammar point names.")
        has_errors = True
    
    if noop_renames:
        for noop_name in noop_renames:
            display.warn(f"No-op rename detected: '{noop_name}' -> ['{noop_name}'] (new name same as old name)")
        display.warn(f"Found {len(noop_renames)} no-op renames.")
        has_errors = True
    
    if has_errors:
        display.warn("Cannot proceed with renames due to validation errors.")
        return False
    
    return True

if __name__ == '__main__':
    try:
        # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
        workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
        grammar_root   = os.path.join(
            workspace_root,
            'resources', 'processed', 'ai-cleaned-merge-grammars'
        )
        
        # Set up debug logging
        log_file = os.path.join(grammar_root, 'summary', 'split-join-rename.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='w')
            ]
        )
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting split-join-rename process")
        logger.info(f"Grammar root: {grammar_root}")
        logger.info(f"Log file: {log_file}")

        # The name of the renames file
        renames_allowed = os.path.join(grammar_root, 'summary/renames-allowed.yaml')

        # Generate the grammary summary object
        grammar_summary = generate_summary(grammar_root, ['id', 'better_grammar_point_name'])
        save_summary(grammar_summary, grammar_root, 'split-join-rename-summary.json')
        display.check(f"Generated grammar summary with {len(grammar_summary['all-grammar-points'])} grammar points.")

        if os.path.exists(renames_allowed):
            logger.info(f"Renames file {renames_allowed} exists, renaming now.")
            display.check(f"Renames file {renames_allowed} exists, renaming now.")
            # Read the renames-allowed.yaml file
            with open(renames_allowed, 'r', encoding='utf-8') as f:
                renames = yaml.safe_load(f)
            
            logger.info(f"Loaded renames: {renames}")
            
            # Check that all old grammar point names exist in grammar summary
            if not check_renames_allowed(renames, grammar_summary):
                sys.exit(1)
            
            # Build a map of old name to new names and look up IDs
            old_to_new = {}
            new_name_to_id = {}
            
            for new_name, old_names_list in renames.items():
                logger.debug(f"Processing rename: {new_name} <- {old_names_list}")
                if new_name == "":
                    # Handle deletion operation - just add to old_to_new with empty new name
                    for old_name in old_names_list:
                        old_to_new[old_name] = [""]
                    continue
                
                # Find the ID from the first old name that exists, or use gp9999
                found_id = "gp9999"
                for old_name in old_names_list:
                    # Look up the ID from the grammar summary
                    if old_name in grammar_summary['all-grammar-points']:
                        found_id = grammar_summary['all-grammar-points'][old_name]['id']
                        break
                new_name_to_id[new_name] = found_id
                
                for old_name in old_names_list:
                    logger.debug(f"  Mapping old name '{old_name}' -> new name '{new_name}'")
                    if old_name in old_to_new:
                        old_to_new[old_name].append(new_name)
                        logger.debug(f"    Added to existing mapping: {old_to_new[old_name]}")
                    else:
                        old_to_new[old_name] = [new_name]
                        logger.debug(f"    Created new mapping: {old_to_new[old_name]}")
            
            # Make a set of all old names
            all_old_names = set(old_to_new.keys())
            # Make a set of all new names
            all_new_names = set(renames.keys())
            
            # Check for illegal filename characters in new grammar point names
            for new_name in all_new_names:
                if new_name == "":  # Skip deletion operations
                    continue
                if '/' in new_name or '\0' in new_name:
                    logger.error(f"New grammar point name contains illegal filename character: '{new_name}'")
                    display.check(f"ERROR: New grammar point name contains illegal filename character: '{new_name}'")
                    sys.exit(1)

            # Check for cases where items are split into multiple new names
            split_new_names = set()
            for old_name in old_to_new:
                if len(old_to_new[old_name]) > 1:
                    split_new_names.add(new_name)
                    display.check(f"Splitting {old_name} -> {old_to_new[old_name]}")

            # Update the grammar summary by removing old names and adding new names
            updated_summary = {'all-grammar-points': {}}
            
            # Add existing grammar points that are not being renamed
            for name, point_data in grammar_summary['all-grammar-points'].items():
                if name not in all_old_names:
                    # Remove better_grammar_point_name field if it exists
                    clean_point_data = {k: v for k, v in point_data.items() if k != 'better_grammar_point_name'}
                    updated_summary['all-grammar-points'][name] = clean_point_data
            
            # Add new grammar points
            for new_name in all_new_names:
                if new_name != "":  # Skip deletion operations
                    updated_summary['all-grammar-points'][new_name] = {
                        'id': new_name_to_id[new_name]
                    }
            
            # Save the updated summary
            save_summary(updated_summary, grammar_root, 'split-join-rename-summary.json')
            display.check(f"Updated summary with {len(updated_summary['all-grammar-points'])} grammar points after renames.")

            # Log the final old_to_new mapping
            logger.info(f"Final old_to_new mapping: {old_to_new}")
            
            # Replace references to old names with new names in all grammar files
            def fn(value, type_name, path):
                if type_name == None: 
                    for act in ['before', 'after']:
                        learn = value.get(f'learn_{act}', [])
                        result = []
                        for grammar_point in learn:
                            stripped = grammar_point.removeprefix('<suggest>:').strip()
                            if stripped in old_to_new:
                                logger.debug(f"Renaming learn_{act} '{grammar_point}' to '{old_to_new[stripped]}' at {path}")
                                result.extend(old_to_new[stripped])
                            elif stripped in updated_summary['all-grammar-points']:
                                # Keep known grammar points that aren't being renamed
                                result.append(grammar_point)
                            else:
                                # Remove unknown grammar points
                                logger.debug(f"Removing unknown grammar point '{grammar_point}' from learn_{act} at {path}")
                                display.check(f"Removing unknown grammar point '{stripped}' from learn_{act}")
                        value[f'learn_{act}'] = result
                    
                    return value
                if type_name != 'grammarType': 
                    return
                # Strip: <suggest>: prefix from value
                stripped = value.removeprefix('<suggest>:').strip()
                if stripped in old_to_new:
                    new_value = old_to_new[stripped][0]
                    logger.info(f"Renaming grammarType '{value}' to '{new_value}' at {path}")
                    if '<suggest>:' in value:
                        display.check(f"Renaming {value} to {new_value} at {path}")
                    return new_value
                return value
    
            def logic(parsed_obj, file_path):
                better_names = parsed_obj.get('better_grammar_point_name', [])
                if len(better_names) == 1 and parsed_obj['grammar_point'] in old_to_new:
                    del parsed_obj['better_grammar_point_name']
                
                visit_json(parsed_obj, GRAMMAR_SCHEMA, fn)
                
                result = clean_lint(parsed_obj, file_path, updated_summary)
                return result
            
            mr = MapReduce(
                input_dir            = grammar_root,
                output_dir           = grammar_root,
                map_func_name        = 'replacing references',
                map_func             = logic,        # or a sync function
                max_threads          = 4,
            )

            asyncio.run(mr.run())

            # Copy old name to new name files
            old_name_paths = set()
            new_name_paths = set()
            for new_name in renames:
                old_names = renames[new_name]
                
                if new_name == "":
                    # Handle deletion operations - add old files to deletion list
                    for old_name in old_names:
                        # Find the ID from the grammar summary to build correct path
                        found_id = "gp9999"
                        if old_name in grammar_summary['all-grammar-points']:
                            found_id = grammar_summary['all-grammar-points'][old_name]['id']
                        old_id_name = f"{found_id}-{old_name}"
                        old_path = os.path.join(grammar_root, old_id_name + '.yaml')
                        old_name_paths.add(old_path)
                    continue
                    
                grammar_id = new_name_to_id[new_name]
                new_id_name = f"{grammar_id}-{new_name}"
                
                # Collect all old content for joining case
                all_old_content = []
                for old_name in old_names:
                    # Find the actual ID for this old name
                    old_grammar_id = "gp9999"
                    if old_name in grammar_summary['all-grammar-points']:
                        old_grammar_id = grammar_summary['all-grammar-points'][old_name]['id']
                    old_id_name = f"{old_grammar_id}-{old_name}"
                    old_path = os.path.join(grammar_root, old_id_name + '.yaml')
                    if os.path.exists(old_path):
                        with open(old_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            all_old_content.append(f"=== {old_name} ===\n{content}")
                    old_name_paths.add(old_path)
                
                new_path = os.path.join(grammar_root, new_id_name + '.yaml')
                new_name_paths.add(new_path)
                
                if not os.path.exists(new_path):
                    # Determine the type of operation and create appropriate header
                    if len(old_names) > 1:
                        # Multiple old names -> one new name (joining)
                        old_names_list = ', '.join(f"'{name}'" for name in old_names)
                        header = f"Multiple old grammar points have been combined into one: {old_names_list} -> '{new_name}'. Please create a unified grammar point that incorporates the relevant aspects of all the old points. "
                        combined_content = '\n\n'.join(all_old_content)
                    elif len(old_names) == 1:
                        old_name = old_names[0]
                        if old_name in old_to_new and len(old_to_new[old_name]) > 1:
                            # One old name -> multiple new names (splitting)
                            all_new_names = old_to_new[old_name]
                            new_names_list = ', '.join(f"'{item}'" for item in all_new_names)
                            header = f"An old grammar point, '{old_name}', has been split into multiple new names: {new_names_list}. You are working on '{new_name}', please be sure to call out the distinction between this new point and the other new points. "
                        else:
                            # Simple rename
                            header = f"An old grammar point has had its name changed from '{old_name}' to '{new_name}'. "
                        combined_content = all_old_content[0] if all_old_content else ""
                    else:
                        header = f"Creating a new grammar point '{new_name}' without any old content. "
                        combined_content = ""
                    
                    # Get learn_before/learn_after from all old grammar points
                    def remove_duplicates_preserve_order(items):
                        """Remove duplicates while preserving order"""
                        seen = set()
                        result = []
                        for item in items:
                            if item not in seen:
                                seen.add(item)
                                result.append(item)
                        return result
                    
                    learn_before = []
                    learn_after = []
                    for old_content in all_old_content:
                        # Extract YAML content (skip the === header ===)
                        old_yaml_content = old_content.split('\n', 1)[1] if '\n' in old_content else old_content
                        try:
                            old_grammar_obj = yaml.safe_load(old_yaml_content)
                            if old_grammar_obj:
                                learn_before.extend(old_grammar_obj.get('learn_before', []))
                                learn_after.extend(old_grammar_obj.get('learn_after', []))
                        except:
                            pass
                    
                    # Remove duplicates while preserving order
                    learn_before = remove_duplicates_preserve_order(learn_before)
                    learn_after = remove_duplicates_preserve_order(learn_after)

                    new_content = {
                        'grammar_point': new_name,
                        'id': grammar_id,
                        'learn_before': learn_before,
                        'learn_after': learn_after,
                        'split_predecessor': 
                            f"{header}"
                            f"Please recreate this grammar point with this information in mind. All fields **MUST** be suitable for the new name. "
                            f"For your reference, here is the old content:\n\n{combined_content}",
                        'lint-errors': [f"You **MUST** repopulate this grammar point with the new name '{new_name}' in mind. All fields **MUST** be suitable for the new name."],
                    }
                
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(new_content, ensure_ascii=False, indent=2))
        
        
            # Remove old name files that are not in the new name paths
            for old_path in old_name_paths:
                if old_path not in new_name_paths and os.path.exists(old_path):
                    display.check(f"Removing old name file {os.path.basename(old_path)}")
                    os.remove(old_path)

            # Rename the renames-allowed.yaml file to renames-allowed.yaml.bak
            os.rename(renames_allowed, renames_allowed + f'-{int(time.time())}.bak')

            sys.exit(0)

        # Create a map of renames in the new simplified format
        # {
        #   'better-name': ['old-name-1', 'old-name-2']
        # }
        renames = {} # Key is new name, value is list of old names
        for grammar_point_name in grammar_summary['all-grammar-points']:
            summary_point = grammar_summary['all-grammar-points'][grammar_point_name]
            better_names = summary_point.get('better_grammar_point_name')
            if not better_names:
                continue

            for better_name in better_names:
                if better_name not in summary_point:
                    if better_name not in renames:
                        renames[better_name] = []
                    renames[better_name].append(grammar_point_name)

        # Save the renames-allowed.yaml file
        if len(renames) > 0:
            display.check(f"Found {len(renames)} renames, saving to {os.path.basename(renames_allowed)}.")
            display.check(f"Check that file and then re-run this script to apply the renames.")
            with open(renames_allowed, 'w', encoding='utf-8') as f:
                yaml.dump(renames, f, allow_unicode=True)
        else:
            display.check(f"No renames found.")
    finally:
        display.stop()
    