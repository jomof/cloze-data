from python.mapreduce import MapReduce
import os
import asyncio
import sys
import time

if __name__ == '__main__':
    import yaml
    import json
    from python.grammar import clean_lint

    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    if not os.path.isdir(grammar_root):
        print(f"ERROR: “{grammar_root}” is not a directory.")
        sys.exit(1)

    def deserialize_yaml(raw: str):
        return yaml.load(raw, Loader=yaml.CSafeLoader)

    def logic(parsed_obj, file_path):
        result = clean_lint(parsed_obj, file_path)
        return result
    
    def fold(accumulated, current):
        if accumulated is None:
            accumulated = {}
        if 'all-grammar-points' not in accumulated:
            accumulated['all-grammar-points'] = {}
        accumulated['all-grammar-points'][current['grammar_point']] = {
            'grammar_point': current['grammar_point'],
            'meaning': current['meaning'],
        }
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
        max_threads          = 3,
    )

    asyncio.run(mr.run())
