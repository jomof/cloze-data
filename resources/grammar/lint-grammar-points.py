from python.mapreduce import MapReduce
import os
import asyncio

from python.grammar import clean_lint
from grammar_summary import generate_summary, save_summary

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
        max_threads          = 4,
    )

    asyncio.run(mr.run())
