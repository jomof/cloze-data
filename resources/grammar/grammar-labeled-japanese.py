from python.mapreduce import MapReduce
import os
import asyncio
from python.mecab.compact_sentence import japanese_to_compact_sentence
from python.console import display
import json
from python.classifiers.grammar import JapaneseGrammarLabelCompletingClassifier

if __name__ == '__main__':
    if os.getenv("ENABLE_DEBUGPY"):
        import debugpy
        for name, value in os.environ.items():
            if 'PATH' in name: continue
            if 'resources' not in value: continue
            print(f"{name}={value}")
        debugpy.listen(("0.0.0.0", 5678))
        print("⏳ Waiting for debugger to attach on port 5678...")
        debugpy.wait_for_client()
        print("✅ Debugger attached!")
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )
    training_data_file = os.path.join(grammar_root, 'summary', 'grammar-labeled-japanese-training-data.json')
    model_file = os.path.join(grammar_root, 'summary', 'grammar-labeled-japanese-classifier.pkl')
    interference_results_file = os.path.join(grammar_root, 'summary', 'grammar-labeled-japanese-interference.json')
    interference_analysis_file = os.path.join(grammar_root, 'summary', 'grammar-labeled-japanese-interference-analysis.txt')
    test_evaluation_results_file = os.path.join(grammar_root, 'summary', 'grammar-labeled-japanese-test-evaluation.json')
    
    classifier = JapaneseGrammarLabelCompletingClassifier()
    display.start()
    if os.path.exists(model_file) and os.path.exists(training_data_file):
        display.start()
        with display.work("loading existing training data"):
            with open(training_data_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
        with display.work("loading existing model"):
            classifier.load_model(model_file)
        with display.work("loading existing interference results"):
            with open(interference_results_file, 'r', encoding='utf-8') as f:
                interference_results = json.load(f)
        with display.work("loading existing test evaluation results"):
            with open(test_evaluation_results_file, 'r', encoding='utf-8') as f:
                test_split_evaluation = json.load(f)
    else:
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
            input_dir            = grammar_root,
            map_func_name        = 'building training set',
            map_func             = map,
            fold_func_name       = 'accumulating training set',
            fold_func            = fold,
            max_threads          = 5,
        )

        result = asyncio.run(mr.run())

        with open(training_data_file, 'w', encoding='utf-8') as file:
            json.dump(training_data, file, ensure_ascii=False, indent=4)
        test_split_evaluation = classifier.fit_from_dict(training_data)
        classifier.save_model(model_file)

        with open(test_evaluation_results_file, 'w', encoding='utf-8') as file:
            json.dump(test_split_evaluation, file, ensure_ascii=False, indent=4)

        with display.work("analyzing label interference"):
            interference_results = classifier.analyze_label_interference(
                training_data=training_data,
                max_label_pairs=10000
            )
        with open(interference_results_file, 'w', encoding='utf-8') as file:
            json.dump(interference_results, file, ensure_ascii=False, indent=4)

    display.stop()
    interference_analysis_output = classifier.dump_interference_analysis(interference_results)
    classifier.print_evaluation_results(test_split_evaluation)
    print(interference_analysis_output)
