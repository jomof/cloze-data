from python.mapreduce import MapReduce
import os
import asyncio
from collections import OrderedDict
import yaml
import json
from python.grammar import clean_lint, GRAMMAR_SCHEMA
from python.utils.visit_json import visit_json

def sort_summary(summary):
    """
    Sorts the summary dictionary by all-grammar-points key.
    Leaves the rest of the structure intact.
    """
    if 'all-grammar-points' in summary:
        sorted_points = OrderedDict(sorted(summary['all-grammar-points'].items()))
        summary['all-grammar-points'] = sorted_points
    return summary

def save_summary(summary, grammar_root):
    """
    Saves the summary to a file.
    """
    summary_root = os.path.join(grammar_root, 'summary')
    if not os.path.isdir(summary_root):
        os.makedirs(summary_root)
    file_path = os.path.join(summary_root, 'summary.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(sort_summary(summary), f, ensure_ascii=False, indent=4)

def deserialize_yaml(raw: str):
    return yaml.load(raw, Loader=yaml.CSafeLoader)

def serialize_json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=4)
    
def generate_summary(grammar_root):
    """
    Generates a summary of all grammar points in the specified directory.
    """
    summary = {'all-grammar-points': OrderedDict()}

    def fold(_, current):
        summary['all-grammar-points'][current['grammar_point']] = {
            'meaning': current.get('meaning'),
        }
    
    mr = MapReduce(
        input_dir            = grammar_root,
        fold_func            = fold,
        deserialize_func     = deserialize_yaml,
        max_threads          = 4,
    )

    asyncio.run(mr.run())
    
    return summary

if __name__ == '__main__':
    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    # Generate the grammary summary object
    grammar_summary = generate_summary(grammar_root)
    save_summary(grammar_summary, grammar_root)
    print(f"Generated grammar summary with {len(grammar_summary['all-grammar-points'])} grammar points.")

    def logic(parsed_obj, file_path):
        result = clean_lint(parsed_obj, file_path, grammar_summary)
        return result

    mr = MapReduce(
        input_dir            = grammar_root,
        output_dir           = grammar_root,
        map_func_name        = 'linting',
        map_func             = logic,        # or a sync function
        deserialize_func     = deserialize_yaml,
        serialize_func       = serialize_json,
        temp_dir             = os.path.join(grammar_root, '.temp'),
        max_threads          = 4,
    )

    asyncio.run(mr.run())
