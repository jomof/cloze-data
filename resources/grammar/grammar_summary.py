import asyncio
import json
import os
from collections import OrderedDict

from dumpyaml import dump_yaml_file
from python.console import display
from python.mapreduce import MapReduce

def sort_summary(summary):
    """
    Sorts the summary dictionary by all-grammar-points key.
    Leaves the rest of the structure intact.
    """
    if 'all-grammar-points' in summary:
        sorted_points = OrderedDict(sorted(summary['all-grammar-points'].items()))
        summary['all-grammar-points'] = sorted_points
    return summary

def save_summary(summary, grammar_root, name='summary.yaml'):
    """
    Saves the summary to a file.
    """
    summary_root = os.path.join(grammar_root, 'summary')
    if not os.path.isdir(summary_root):
        os.makedirs(summary_root)
    file_path = os.path.join(summary_root, name)
    with open(file_path, 'w', encoding='utf-8') as f:
        dump_yaml_file(summary, f)
    
def generate_summary(grammar_root, fields = ['meaning']):
    """
    Generates a summary of all grammar points in the specified directory.
    """
    summary = {'all-grammar-points': OrderedDict()}

    seen = {}

    def preprocess(parsed_obj, file_path):
        basename = os.path.basename(file_path)
        _, grammar_point = os.path.splitext(basename)[0].split('-', 1)
        if grammar_point not in seen:
            seen[grammar_point] = []
        seen[grammar_point].append(file_path)
        return parsed_obj
        
    def fold(_, current):
        summary_field = { }
        for field in fields:
            if field in current:
                summary_field[field] = current[field]
        summary['all-grammar-points'][current['grammar_point']] = summary_field
    
    mr = MapReduce(
        input_dir            = grammar_root,
        preprocess_func      = preprocess,
        fold_func_name       = 'summarizing',
        fold_func            = fold,
        max_threads          = 4,
    )

    asyncio.run(mr.run())

    # Check for 'seen' grammar points that have multiple filenames
    should_error = False
    for grammar_point, files in seen.items():
        if len(files) > 1:
            basenames = [os.path.basename(f) for f in files]
            display.warn(f"Grammar point '{grammar_point}' has multiple files: {basenames}")
            should_error = True
    if should_error:
        raise ValueError("Multiple files found for the same grammar point. Please resolve the conflicts.")
    return summary