from python.mapreduce import MapReduce
import os
import asyncio

from python.grammar import clean_lint_memoize
from grammar_summary import generate_summary, save_summary
from python.console import display

if __name__ == '__main__':
    try:
        # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
        workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
        grammar_root   = os.path.join(
            workspace_root,
            'resources', 'processed', 'ai-cleaned-merge-grammars'
        )
        display.start()

        # Generate the grammary summary object
        grammar_summary = generate_summary(grammar_root)
        save_summary(grammar_summary, grammar_root)
        display.check(f"Generated grammar summary with {len(grammar_summary['all-grammar-points'])} grammar points.")

        def logic(parsed_obj, file_path):
            result = clean_lint_memoize(parsed_obj, file_path, grammar_summary)
            return result

        mr = MapReduce(
            input_dir            = grammar_root,
            output_dir           = grammar_root,
            map_func_name        = 'linting',
            map_func             = logic,        # or a sync function
            max_threads          = 10,
        )

        result = asyncio.run(mr.run())

        display.check(f"Replaced {result['files-written']} files with cleaned grammar points.")
    finally:
        display.stop()
