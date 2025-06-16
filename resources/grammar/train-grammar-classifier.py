

from python.mapreduce import MapReduce
from python.mecab.compact_sentence import japanese_to_compact_sentence
from python.console import display
from python.classifiers.grammar import JapaneseGrammarLabelCompletingClassifier
import asyncio
import argparse



if __name__ == '__main__':
    """"""
    parser = argparse.ArgumentParser()
    parser.add_argument('output', help='Output filename')
    args = parser.parse_args()

    # Gather training data
    training_data = {}
    def map(current, _):
        grammar_point = current['grammar_point']
        examples = current.get('examples', [])
        result = []
        for example in examples:
            japaneses = example.get('japanese', [])
            for japanese in japaneses:
                compact = japanese_to_compact_sentence(japanese.replace('{', '').replace('}', ''))
                result.append([grammar_point, compact])
        return result

    def fold(_, points):
        global training_data
        for point in points:
            grammar_point, compact = point
            point_list = training_data.setdefault(compact, [])
            point_list.append(grammar_point)
            training_data[compact] = list(set(point_list))  # Ensure unique labels
    mr = MapReduce(
        input_dir            = 'resources/processed/ai-cleaned-merge-grammars',
        map_func_name        = 'building training set',
        map_func             = map,
        fold_func_name       = 'accumulating training set',
        fold_func            = fold,
        max_threads          = 5,
    )

    asyncio.run(mr.run())

    # Train classifier
    classifier = JapaneseGrammarLabelCompletingClassifier(
        test_size=0.1
    )
    test_split_evaluation = classifier.fit_from_dict(training_data)
    classifier.save_model(args.output)