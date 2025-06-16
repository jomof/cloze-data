

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


        count_this_grammar_point = union_of_examples_grammar_points[grammar_point]
        del union_of_examples_grammar_points[grammar_point]
        union_of_examples_grammar_points = dict(sorted(union_of_examples_grammar_points.items(), key=lambda x: x[1], reverse=True))
        union_of_examples_grammar_points = {k: v for k, v in union_of_examples_grammar_points.items() if v < count_this_grammar_point}
        # filtered_dict = {k: v for k, v in union_of_examples_grammar_points.items() if v/count_this_grammar_point > 0.9}

        if 'learn_after' in current:
            del current['learn_after']
        if union_of_examples_grammar_points:
            dependencies = sorted(list(union_of_examples_grammar_points.keys())[:3])
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