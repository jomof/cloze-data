

from python.classifiers.grammar import JapaneseGrammarLabelCompletingClassifier
from python.console import display
from python.mapreduce import MapReduce
import json
import os
import asyncio
from python.mecab.compact_sentence import japanese_to_compact_sentence
from python.console import display
from collections import defaultdict
from python.classifiers.grammar import JapaneseGrammarLabelCompletingClassifier


def get_keys_with_second_highest_value(d):
    if not d:
        return [] # Handle empty dictionary

    # 1. Get all unique values
    unique_values = sorted(list(set(d.values())), reverse=True)

    # 2. Check if there's a second highest value
    if len(unique_values) < 2:
        return [] # Not enough unique values for a "second highest"

    second_highest_value = unique_values[1] # The second element after sorting descending

    # 3. Collect all keys that have this second highest value
    keys_with_second_highest = [key for key, value in d.items() if value == second_highest_value and value > 1]

    return keys_with_second_highest

if __name__ == '__main__':

    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )
    temp_dir = os.path.join(workspace_root, '.temp')
    display.start()
    classifier = JapaneseGrammarLabelCompletingClassifier()
    classifier.load_model('resources/grammar/trained-grammar-classifier.pkl')

    def map(current, file):
        # if 'gp0052' not in file: return None
        original_json = json.dumps(current, ensure_ascii=False, sort_keys=True)
        grammar_point : str = current['grammar_point']
        examples = current.get('examples', [])
        sentences = { }

        # Gather all sentences to classify
        for example in examples:
            japaneses = example.get('japanese', [])
            for japanese in japaneses:
                sentences[japanese] = []

        # Predict the grammar poin
        union_of_examples_grammar_points = defaultdict(int)
        predictions = classifier.predict(sentences.keys())
        for index, japanese in enumerate(sentences.keys()):
            predicted_grammar_points = set(predictions[index])
            sentences[japanese] = predicted_grammar_points
            # for predicted_grammar_point in predicted_grammar_points:
            #     union_of_examples_grammar_points[predicted_grammar_point] += 1


        # Calculate the grammar point usage per example
        # Make sure each example is equally weighted and so that number of alternate spellings
        # doesn't count toward frequency.
        for example in examples:
            japaneses = example.get('japanese', [])
            used_in_this_example = set()
            for japanese in japaneses:
                used_in_this_example |= sentences[japanese]
            for used in used_in_this_example:
                union_of_examples_grammar_points[used] += 1


        second_highest_frequency_items = get_keys_with_second_highest_value(union_of_examples_grammar_points)

        if second_highest_frequency_items:
            dependencies = sorted(second_highest_frequency_items)
            current['learn_before'] = dependencies
            # display.check(f"{grammar_point} examples reference {len(union_of_examples_grammar_points)} grammar points. Choosing dependency: {dependency}")
        
        new_json = json.dumps(current, ensure_ascii=False, sort_keys=True)
        if original_json == new_json:
            return None


        return current

    mr = MapReduce(
        input_dir            = grammar_root,
        output_dir           = grammar_root,
        map_func_name        = 'calculating dependencies',
        map_func             = map,
        max_threads          = 14,
    )

    result = asyncio.run(mr.run())

    display.stop()