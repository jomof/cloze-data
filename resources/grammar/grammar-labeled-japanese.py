from python.mapreduce import MapReduce
import os
import asyncio
from python.mecab.compact_sentence import japanese_to_compact_sentence
from python.console import display
import json
import json
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations

def analyze_training_corpus(corpus_data):
    """
    Analyze a multi-label training corpus to provide statistics for classifier design decisions.
    
    Args:
        corpus_data: dict in format {"sample-id": ["label1", "label2", ...], ...}
    
    Returns:
        dict: Comprehensive statistics about the corpus
    """
    
    # Basic corpus statistics
    n_samples = len(corpus_data)
    all_labels = set()
    labels_per_sample = []
    label_counts = Counter()
    
    # Collect basic stats
    for sample_id, labels in corpus_data.items():
        labels_per_sample.append(len(labels))
        for label in labels:
            all_labels.add(label)
            label_counts[label] += 1
    
    n_unique_labels = len(all_labels)
    all_labels = sorted(list(all_labels))
    
    # Label frequency statistics
    label_frequencies = {label: count/n_samples for label, count in label_counts.items()}
    
    # Label co-occurrence matrix
    cooccurrence = defaultdict(int)
    for sample_id, labels in corpus_data.items():
        for label1, label2 in combinations(labels, 2):
            pair = tuple(sorted([label1, label2]))
            cooccurrence[pair] += 1
    
    # Label imbalance metrics
    min_freq = min(label_frequencies.values()) if label_frequencies else 0
    max_freq = max(label_frequencies.values()) if label_frequencies else 0
    imbalance_ratio = max_freq / min_freq if min_freq > 0 else float('inf')
    
    # Rare label analysis (labels appearing in <5% of samples)
    rare_threshold = 0.05
    rare_labels = [label for label, freq in label_frequencies.items() if freq < rare_threshold]
    
    # Label cardinality (average labels per sample)
    label_cardinality = np.mean(labels_per_sample)
    
    # Label density (cardinality / total possible labels)
    label_density = label_cardinality / n_unique_labels if n_unique_labels > 0 else 0
    
    # Distinct labelsets
    labelsets = set()
    labelset_counts = Counter()
    for sample_id, labels in corpus_data.items():
        labelset = tuple(sorted(labels))
        labelsets.add(labelset)
        labelset_counts[labelset] += 1
    
    n_distinct_labelsets = len(labelsets)
    
    # Most common label combinations
    top_cooccurrences = sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Compilation of all statistics
    # Sample examples for inspection
    sample_examples = []
    sample_ids = list(corpus_data.keys())
    
    # Get examples with different characteristics
    examples_to_show = min(5, len(sample_ids))
    
    # Show samples with different label counts
    samples_by_label_count = sorted(corpus_data.items(), key=lambda x: len(x[1]))
    
    # Get diverse examples: min labels, max labels, median, and random
    import random
    random.seed(42)  # For reproducible examples
    indices_to_show = []
    if len(samples_by_label_count) > 0:
        indices_to_show.append(0)  # Min labels
        if len(samples_by_label_count) > 1:
            indices_to_show.append(-1)  # Max labels
        if len(samples_by_label_count) > 2:
            indices_to_show.append(len(samples_by_label_count) // 2)  # Median
        
        # Add a few more random examples if available
        remaining_indices = [i for i in range(len(samples_by_label_count)) if i not in indices_to_show]
        if remaining_indices:
            additional = min(2, len(remaining_indices))
            indices_to_show.extend(random.sample(remaining_indices, additional))
    
    for idx in indices_to_show[:examples_to_show]:
        sample_id, labels = samples_by_label_count[idx]
        sample_examples.append({
            'sample_id': sample_id,
            'labels': labels,
            'label_count': len(labels)
        })

    stats = {
        'basic_stats': {
            'n_samples': n_samples,
            'n_unique_labels': n_unique_labels,
            'n_distinct_labelsets': n_distinct_labelsets,
            'avg_labels_per_sample': label_cardinality,
            'label_density': label_density,
        },
        
        'sample_examples': sample_examples,
        
        'label_distribution': {
            'min_labels_per_sample': min(labels_per_sample) if labels_per_sample else 0,
            'max_labels_per_sample': max(labels_per_sample) if labels_per_sample else 0,
            'median_labels_per_sample': np.median(labels_per_sample) if labels_per_sample else 0,
            'std_labels_per_sample': np.std(labels_per_sample) if labels_per_sample else 0,
        },
        
        'label_frequency_stats': {
            'most_frequent_labels': label_counts.most_common(10),
            'least_frequent_labels': label_counts.most_common()[-10:] if len(label_counts) >= 10 else label_counts.most_common(),
            'rare_labels_count': len(rare_labels),
            'rare_labels': rare_labels[:10],  # Show first 10 rare labels
            'imbalance_ratio': imbalance_ratio,
        },
        
        'co_occurrence_stats': {
            'top_label_pairs': top_cooccurrences,
            'total_cooccurrence_pairs': len(cooccurrence),
        },
        
        'design_recommendations': {}
    }
    
    # Add design recommendations based on statistics
    recommendations = []
    
    # Recommendation based on number of labels
    if n_unique_labels <= 10:
        recommendations.append("SMALL_LABEL_SPACE: Consider Binary Relevance or Label Powerset")
    elif n_unique_labels <= 100:
        recommendations.append("MEDIUM_LABEL_SPACE: Binary Relevance or Classifier Chains recommended")
    else:
        recommendations.append("LARGE_LABEL_SPACE: Binary Relevance or embedding-based approaches recommended")
    
    # Recommendation based on label cardinality
    if label_cardinality <= 2:
        recommendations.append("LOW_CARDINALITY: Simple approaches like Binary Relevance work well")
    elif label_cardinality <= 5:
        recommendations.append("MEDIUM_CARDINALITY: Classifier Chains or MLkNN might be beneficial")
    else:
        recommendations.append("HIGH_CARDINALITY: Consider ensemble methods or deep learning approaches")
    
    # Recommendation based on imbalance
    if imbalance_ratio > 100:
        recommendations.append("HIGH_IMBALANCE: Use stratified sampling and consider cost-sensitive learning")
    elif imbalance_ratio > 10:
        recommendations.append("MODERATE_IMBALANCE: Consider balanced sampling or weighted loss functions")
    
    # Recommendation based on rare labels
    if len(rare_labels) > n_unique_labels * 0.3:
        recommendations.append("MANY_RARE_LABELS: Consider label hierarchy or transfer learning approaches")
    
    # Recommendation based on label dependencies
    if len(top_cooccurrences) > 0 and top_cooccurrences[0][1] > n_samples * 0.1:
        recommendations.append("STRONG_DEPENDENCIES: Classifier Chains or structured prediction methods recommended")
    
    stats['design_recommendations'] = recommendations
    
    return stats

def print_corpus_analysis(stats):
    """Pretty print the corpus analysis results"""
    
    print("=" * 60)
    print("TRAINING CORPUS ANALYSIS")
    print("=" * 60)
    
    print("\n📊 BASIC STATISTICS")
    print("-" * 30)
    basic = stats['basic_stats']
    print(f"Samples: {basic['n_samples']:,}")
    print(f"Unique labels: {basic['n_unique_labels']:,}")
    print(f"Distinct labelsets: {basic['n_distinct_labelsets']:,}")
    print(f"Average labels per sample: {basic['avg_labels_per_sample']:.2f}")
    print(f"Label density: {basic['label_density']:.3f}")
    
    print("\n📝 SAMPLE EXAMPLES")
    print("-" * 30)
    for i, example in enumerate(stats['sample_examples'], 1):
        labels_str = ", ".join(example['labels']) if example['labels'] else "No labels"
        
        # Add type indicator and special info
        type_indicator = ""
        if example.get('type') == 'most-labels':
            type_indicator = " [MOST LABELS]"
        elif example.get('type') == 'min-labels':
            type_indicator = " [MIN LABELS]"
        elif example.get('type') == 'median-labels':
            type_indicator = " [MEDIAN LABELS]"
        elif example.get('type') == 'co-occurrence':
            type_indicator = " [CO-OCCURRING PAIRS]"
            if 'matching_pairs' in example:
                pairs_str = ", ".join([f"({p[0]}, {p[1]})" for p in example['matching_pairs']])
                type_indicator += f" - Contains: {pairs_str}"
        elif example.get('type') == 'random':
            type_indicator = " [RANDOM]"
        
        print(f"{i}. {example['sample_id']}: [{labels_str}] ({example['label_count']} labels){type_indicator}")
    
    if len(stats['sample_examples']) < basic['n_samples']:
        print(f"... and {basic['n_samples'] - len(stats['sample_examples'])} more samples")
    
    print("\n📈 LABEL DISTRIBUTION")
    print("-" * 30)
    dist = stats['label_distribution']
    print(f"Labels per sample - Min: {dist['min_labels_per_sample']}, Max: {dist['max_labels_per_sample']}")
    print(f"Labels per sample - Median: {dist['median_labels_per_sample']:.1f}, Std: {dist['std_labels_per_sample']:.2f}")
    
    print("\n🏷️  LABEL FREQUENCY ANALYSIS")
    print("-" * 30)
    freq = stats['label_frequency_stats']
    print(f"Most frequent labels:")
    for label, count in freq['most_frequent_labels'][:5]:
        print(f"  {label}: {count} samples ({count/stats['basic_stats']['n_samples']*100:.1f}%)")
    
    print(f"\nRare labels (<%5 of samples): {freq['rare_labels_count']}")
    if freq['rare_labels']:
        print(f"Examples: {', '.join(freq['rare_labels'][:5])}")
    
    print(f"Imbalance ratio (max/min frequency): {freq['imbalance_ratio']:.1f}")
    
    print("\n🔗 LABEL CO-OCCURRENCE")
    print("-" * 30)
    cooc = stats['co_occurrence_stats']
    print(f"Total label pairs that co-occur: {cooc['total_cooccurrence_pairs']}")
    if cooc['top_label_pairs']:
        print("Most frequent label pairs:")
        for (label1, label2), count in cooc['top_label_pairs'][:5]:
            print(f"  ({label1}, {label2}): {count} times")
    
    print("\n🎯 DESIGN RECOMMENDATIONS")
    print("-" * 30)
    for rec in stats['design_recommendations']:
        print(f"✓ {rec}")
    
    print("\n💡 SUGGESTED SCIKIT-LEARN APPROACHES")
    print("-" * 30)
    
    basic = stats['basic_stats']
    if basic['n_unique_labels'] <= 20 and basic['avg_labels_per_sample'] <= 3:
        print("• MultiOutputClassifier with RandomForest/SVM")
        print("• MLPClassifier with sigmoid activation")
    
    if basic['n_unique_labels'] > 20:
        print("• OneVsRestClassifier (Binary Relevance)")
        print("• ClassifierChain for label dependencies")
    
    if stats['label_frequency_stats']['rare_labels_count'] > basic['n_unique_labels'] * 0.2:
        print("• Consider stratified sampling")
        print("• Use class_weight='balanced' in classifiers")

# Example usage function
def load_and_analyze_corpus(file_path):
    """Load corpus from JSON file and analyze it"""
    with open(file_path, 'r') as f:
        corpus_data = json.load(f)
    
    stats = analyze_training_corpus(corpus_data)
    print_corpus_analysis(stats)
    return stats


if __name__ == '__main__':
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    next_label = 0
    interned_labels = {} 
    training_data = {}

    def intern_label(label):
        global next_label, interned_labels
        if label not in interned_labels:
            interned_labels[label] = str(next_label)
            next_label += 1
        return interned_labels[label]

    def map(current, file_path):
        grammar_point = current['grammar_point']
        examples = current.get('examples', [])
        result = []
        for example in examples:
            japaneses = example.get('japanese', [])
            for japanese in japaneses:
                # compact = japanese_to_compact_sentence(japanese.replace('{', '').replace('}', ''))
                compact = japanese#.replace('{', '').replace('}', '')
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
        map_func             = map,
        fold_func            = fold,
        max_threads          = 5,
    )

    result = asyncio.run(mr.run())

    with open(f"{grammar_root}/summary/training-data.txt", 'w', encoding='utf-8') as file:
        json.dump(training_data, file, ensure_ascii=False, indent=4)
    display.stop()

    stats = analyze_training_corpus(training_data)
    print_corpus_analysis(stats)
    with open(f"{grammar_root}/summary/statistics.txt", 'w', encoding='utf-8') as file:
        json.dump(stats, file, ensure_ascii=False, indent=4)
    
    