from collections import OrderedDict
import json
from python.mapreduce import MapReduce
import asyncio
import os

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
    
def generate_summary(grammar_root, fields = ['id', 'meaning']):
    """
    Generates a summary of all grammar points in the specified directory.
    """
    summary = {'all-grammar-points': OrderedDict()}

    def fold(_, current):
        summary_field = { }
        for field in fields:
            if field in current:
                summary_field[field] = current[field]
        summary['all-grammar-points'][current['grammar_point']] = summary_field
    
    mr = MapReduce(
        input_dir            = grammar_root,
        fold_func_name       = 'summarizing',
        fold_func            = fold,
        max_threads          = 4,
    )

    asyncio.run(mr.run())
    
    return summary