from python.mapreduce import MapReduce
import os
import asyncio
from python.mecab.compact_sentence import japanese_to_compact_sentence, compact_sentence_to_japanese
from python.console import display
import json
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import hamming_loss, jaccard_score
import pickle
import re
from typing import List, Dict, Union
import warnings
warnings.filterwarnings('ignore')

class JapaneseGrammarLabelCompletingClassifier:
    """
    Multi-label classifier for Japanese grammar patterns using logistic regression.
    Handles imbalanced data with configurable parameters.
    """
    
    def __init__(self, 
                 min_label_freq=2,
                 max_features=20000,
                 ngram_range=(1, 3),
                 class_weight='balanced',
                 random_state=42,
                 test_size=0.2):
        """
        Initialize the classifier.
        
        Args:
            min_label_freq: Minimum frequency for a label to be included
            max_features: Maximum number of TF-IDF features
            ngram_range: N-gram range for TF-IDF
            class_weight: How to handle class imbalance
            random_state: Random seed for reproducibility
            test_size: Fraction of data to use for testing (0.0-1.0)
        """
        self.min_label_freq = min_label_freq
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.class_weight = class_weight
        self.random_state = random_state
        self.test_size = test_size
        
        # Initialize components
        self.vectorizer = None
        self.label_binarizer = None
        self.classifier = None
        self.label_counts = None
        self.valid_labels = None
        
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess Japanese text."""
        # Remove curly braces that mark grammar patterns
        clean = re.sub(r'[{}]', '', text)
        clean = clean.replace('⌈', ' ⌈ ').replace('⌉', ' ⌉ ').replace('ˢ', ' ˢ').replace('ᵖ', ' ᵖ').replace('ʳ', ' ʳ').strip()
        return clean
    
    def _filter_rare_labels(self, labels_list: List[List[str]]) -> List[List[str]]:
        """Filter out rare labels based on min_label_freq."""
        # Count label frequencies
        label_counter = Counter()
        for labels in labels_list:
            label_counter.update(labels)
        
        # Keep only frequent labels
        self.valid_labels = {label for label, count in label_counter.items() 
                           if count >= self.min_label_freq}
        
        with display.work("filtering labels"):
            # Filter labels in dataset
            filtered_labels = []
            for labels in labels_list:
                filtered = [label for label in labels if label in self.valid_labels]
                # If all labels were filtered out, keep at least one most frequent
                if not filtered and labels:
                    most_frequent = max(labels, key=lambda x: label_counter[x])
                    if label_counter[most_frequent] >= self.min_label_freq:
                        filtered = [most_frequent]
                filtered_labels.append(filtered)
        
        return filtered_labels
    
    def _setup_classifier(self):
        """Setup the logistic regression classifier."""
        base_classifier = LogisticRegression(
            max_iter=1000,
            class_weight=self.class_weight,
            random_state=self.random_state,
        )
        
        # Use OneVsRestClassifier for multi-label classification
        self.classifier = OneVsRestClassifier(base_classifier, n_jobs=-1)
    
    def fit_from_dict(self, data: Dict[str, List[str]]):
        """
        Train the classifier directly from a dictionary with automatic evaluation.
        
        Args:
            data: Dictionary with texts as keys and label lists as values
              Keys are Japanese sentences augmented with grammar information. For example:
                ⌈ˢ机ᵖnʳツクエ⌉の⌈ˢ上ᵖnʳウエ⌉に⌈ˢ本ᵖnʳホン⌉は⌈ˢありᵖvᵇあるʳアル⌉⌈ˢますᵖauxvʳマス⌉。 for 机の上に本はあります。
              Values are lists of grammar point names. For example:
                な-Adjective[でも] (concessive)
        """
        texts = list(data.keys())
        labels = list(data.values())
        
        if len(data) > 10:  # Only split if we have enough data
            # Split data for evaluation
            train_texts, test_texts, train_labels, test_labels = self._test_train_split(data)
            display.check(f"Dataset split: {len(train_texts):,} train, {len(test_texts):,} test")
            
            # Train on training set
            self.fit(train_texts, train_labels)
            
            # Evaluate on test set
            with display.work("evaluating holdback set"):
                results = self.evaluate(test_texts, test_labels)

            return results
        else:
            # Train on all data if insufficient data for split
            display.warn("Insufficient data for split - training on full dataset")
            self.fit(texts, labels)
            return None # No evaluation results in this case
    
    def fit(self, texts: List[str], labels: List[List[str]]):
        """Train the classifier."""
        # Clean texts and filter labels
        with display.work("preprocessing"):
            cleaned_texts = [self._clean_text(text) for text in texts]
            filtered_labels = self._filter_rare_labels(labels)
        
        # Vectorize texts
        with display.work("vectorizing"):
            self.vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=self.ngram_range,
                analyzer='word',
                min_df=3,
                max_df=0.85,
                strip_accents=None,
                sublinear_tf=True 
            )
            X = self.vectorizer.fit_transform(cleaned_texts)
            display.check(f"Feature matrix shape: {X.shape}")
        
        # Prepare labels
        with display.work("preparing labels"):
            self.label_binarizer = MultiLabelBinarizer()
            y = self.label_binarizer.fit_transform(filtered_labels)
            display.check(f"Label matrix shape: {y.shape}")
            display.check(f"Active labels: {len(self.label_binarizer.classes_)}")
        
        # Train classifier
        with display.work("training model"):
            self._setup_classifier()
            self.classifier.fit(X, y)
        
        # Analyze training data
        with display.work("gathering statistics"):
            # Store label statistics
            self.label_counts = Counter()
            for labels in filtered_labels:
                self.label_counts.update(labels)
            
            # Analyze co-occurrences in training data
            self.cooccurrence_counts = defaultdict(int)
            self.cooccurrence_samples = defaultdict(list)
            
            for i, labels in enumerate(filtered_labels):
                if len(labels) > 1:  # Only analyze multi-label samples
                    for label1, label2 in combinations(sorted(labels), 2):
                        pair_key = f"{label1}||{label2}"  
                        self.cooccurrence_counts[pair_key] += 1
                        if len(self.cooccurrence_samples[pair_key]) < 3:
                            self.cooccurrence_samples[pair_key].append({
                                'text': cleaned_texts[i],
                                'labels': labels
                            })
        
        display.check("Training completed!")
        return self
    
    def predict(self, texts: Union[str, List[str]], 
                threshold: float = 0.45) -> Union[List[str], List[List[str]]]:
        """
        Predict labels for input texts.
        
        Args:
            texts: Single text or list of texts
            threshold: Probability threshold for predictions
            
        Returns:
            List of labels for single text, or list of label lists for multiple texts
        """
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        # Clean and vectorize texts
        cleaned_texts = [self._clean_text(text) for text in texts]
        X = self.vectorizer.transform(cleaned_texts)
        
        # Get probability predictions
        if hasattr(self.classifier, "predict_proba"):
            # For logistic regression classifier that supports predict_proba
            try:
                y_prob = self.classifier.predict_proba(X)
                # Convert to binary predictions based on threshold
                y_pred = (y_prob >= threshold).astype(int)
            except:
                # Fallback to decision_function or predict
                if hasattr(self.classifier, "decision_function"):
                    y_scores = self.classifier.decision_function(X)
                    y_pred = (y_scores >= 0).astype(int)
                else:
                    y_pred = self.classifier.predict(X)
        else:
            y_pred = self.classifier.predict(X)
        
        # Convert back to labels
        predicted_labels = self.label_binarizer.inverse_transform(y_pred)
        
        # Convert tuples to lists and handle empty predictions
        result = []
        for labels in predicted_labels:
            if len(labels) == 0:
                # If no labels predicted, return most frequent label as fallback
                most_frequent_label = self.label_counts.most_common(1)[0][0]
                result.append([most_frequent_label])
            else:
                result.append(list(labels))
        
        return result[0] if single_input else result
    
    def evaluate(self, texts: List[str], labels: List[List[str]]) -> Dict:
        """Evaluate the classifier performance with detailed statistics."""

        # texts, labels should be lists of the same length
        predictions = self.predict(texts)
        
        # Convert to binary matrix for metrics
        y_true = self.label_binarizer.transform(labels)
        y_pred = self.label_binarizer.transform(predictions)
        
        # Basic multi-label metrics
        hamming = hamming_loss(y_true, y_pred)
        jaccard = jaccard_score(y_true, y_pred, average='samples')
        
        # Additional sample-wise metrics
        exact_match_ratio = np.mean([set(true) == set(pred) for true, pred in zip(labels, predictions)])
        
        # Label-wise statistics
        from sklearn.metrics import precision_recall_fscore_support, accuracy_score
        precision_micro = precision_recall_fscore_support(y_true, y_pred, average='micro')[0]
        recall_micro = precision_recall_fscore_support(y_true, y_pred, average='micro')[1]
        f1_micro = precision_recall_fscore_support(y_true, y_pred, average='micro')[2]
        
        precision_macro = precision_recall_fscore_support(y_true, y_pred, average='macro')[0]
        recall_macro = precision_recall_fscore_support(y_true, y_pred, average='macro')[1]
        f1_macro = precision_recall_fscore_support(y_true, y_pred, average='macro')[2]
        
        # Subset accuracy (exact match)
        subset_accuracy = accuracy_score(y_true, y_pred)
        
        # Label cardinality (average number of labels per sample)
        true_cardinality = np.mean(np.sum(y_true, axis=1))
        pred_cardinality = np.mean(np.sum(y_pred, axis=1))
        
        # Per-label analysis
        per_label_stats = {}
        label_names = self.label_binarizer.classes_
        
        for i, label in enumerate(label_names):
            y_true_label = y_true[:, i]
            y_pred_label = y_pred[:, i]
            
            if np.sum(y_true_label) > 0:  # Only for labels that appear in test set
                precision = precision_recall_fscore_support(y_true_label, y_pred_label, average='binary')[0]
                recall = precision_recall_fscore_support(y_true_label, y_pred_label, average='binary')[1]
                f1 = precision_recall_fscore_support(y_true_label, y_pred_label, average='binary')[2]
                support = np.sum(y_true_label)
                
                per_label_stats[label] = {
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1': float(f1),
                    'support': int(support),
                    'predicted_count': int(np.sum(y_pred_label))
                }
        
        # Prediction analysis
        correct_predictions = 0
        partial_matches = 0
        complete_misses = 0
        over_predictions = 0
        under_predictions = 0
        
        for true, pred in zip(labels, predictions):
            true_set = set(true)
            pred_set = set(pred)
            
            if true_set == pred_set:
                correct_predictions += 1
            elif true_set.intersection(pred_set):
                partial_matches += 1
            else:
                complete_misses += 1
            
            if len(pred_set) > len(true_set):
                over_predictions += 1
            elif len(pred_set) < len(true_set):
                under_predictions += 1
        
        # Use training data co-occurrences (more comprehensive than test set)
        if hasattr(self, 'cooccurrence_counts') and self.cooccurrence_counts:
            top_cooccurrences = [
                [pair_key.split("||"), count] 
                for pair_key, count in sorted(self.cooccurrence_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            cooccurrence_samples = self.cooccurrence_samples
            cooccurrence_counts = self.cooccurrence_counts
        else:
            # Fallback: analyze test set if training co-occurrences not available
            cooccurrence_counts = defaultdict(int)
            cooccurrence_samples = defaultdict(list)
            
            for i, label_list in enumerate(labels):
                if len(label_list) > 1:  # Only analyze multi-label samples
                    for label1, label2 in combinations(sorted(label_list), 2):
                        pair_key = f"{label1}||{label2}"  # Use string key for consistency
                        cooccurrence_counts[pair_key] += 1
                        if len(cooccurrence_samples[pair_key]) < 3:
                            cooccurrence_samples[pair_key].append({
                                'text': texts[i],
                                'labels': label_list
                            })
            
            top_cooccurrences = [
                [pair_key.split("||"), count] 
                for pair_key, count in sorted(cooccurrence_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
        
        results = {
            'sample_count': len(texts),
            'hamming_loss': float(hamming),
            'jaccard_score': float(jaccard),
            'exact_match_ratio': float(exact_match_ratio),
            'subset_accuracy': float(subset_accuracy),
            'precision_micro': float(precision_micro),
            'recall_micro': float(recall_micro),
            'f1_micro': float(f1_micro),
            'precision_macro': float(precision_macro),
            'recall_macro': float(recall_macro),
            'f1_macro': float(f1_macro),
            'true_label_cardinality': float(true_cardinality),
            'pred_label_cardinality': float(pred_cardinality),
            'correct_predictions': int(correct_predictions),
            'partial_matches': int(partial_matches),
            'complete_misses': int(complete_misses),
            'over_predictions': int(over_predictions),
            'under_predictions': int(under_predictions),
            'per_label_stats': per_label_stats,  # This one needs special handling
            'top_cooccurrences': top_cooccurrences,
            'cooccurrence_samples': cooccurrence_samples,
            'cooccurrence_counts': dict(cooccurrence_counts)  # Convert defaultdict to dict
        }

        
        return results
    
    def print_evaluation_results(self, results: Dict):
        """Print formatted evaluation results."""
        if not results: return
        print("=" * 60)
        print("🎯 MODEL EVALUATION RESULTS")
        print("=" * 60)
        
        print(f"\n📈 COMPLETION EFFECTIVENESS")
        print(f"{'='*30}")
        print(f"Label discovery rate: {results['recall_micro']:.1%} (finding {results['recall_micro']*100:.0f}% of existing patterns)")
        print(f"Precision of additions: {results['precision_micro']:.1%}")
        print(f"Coverage improvement: {1-results['hamming_loss']:.1%}")
        print(f"Sample enrichment ratio: {results['pred_label_cardinality']:.1f}x")
        
        print(f"\n🎯 MICRO-AVERAGED METRICS")
        print(f"{'='*30}")
        print(f"Precision: {results['precision_micro']:.3f}")
        print(f"Recall: {results['recall_micro']:.3f}")
        print(f"F1-score: {results['f1_micro']:.3f}")
        
        print(f"\n🎯 MACRO-AVERAGED METRICS")
        print(f"{'='*30}")
        print(f"Precision: {results['precision_macro']:.3f}")
        print(f"Recall: {results['recall_macro']:.3f}")
        print(f"F1-score: {results['f1_macro']:.3f}")
        
        print(f"\n📈 LABEL CARDINALITY")
        print(f"{'='*30}")
        print(f"True avg labels/sample: {results['true_label_cardinality']:.2f}")
        print(f"Pred avg labels/sample: {results['pred_label_cardinality']:.2f}")
        
        total = results['sample_count']
        print(f"\n🔍 LABEL COMPLETION ANALYSIS")
        print(f"{'='*30}")
        print(f"Perfect matches: {results['correct_predictions']:,} ({results['correct_predictions']/total:.1%})")
        print(f"Enhanced with additional labels: {results['partial_matches']:,} ({results['partial_matches']/total:.1%})")
        print(f"Potential gaps identified: {results['complete_misses']:,} ({results['complete_misses']/total:.1%})")
        print(f"Label set enrichment: {results['over_predictions']:,} samples ({results['over_predictions']/total:.1%})")
        print(f"Completeness confidence: {(total-results['under_predictions'])/total:.1%}")
        
        # Top performing labels
        per_label = results['per_label_stats']
        if per_label:
            print(f"\n🏆 TOP PERFORMING LABELS (by F1-score)")
            print(f"{'='*50}")
            sorted_labels = sorted(per_label.items(), key=lambda x: x[1]['f1'], reverse=True)
            for i, (label, stats) in enumerate(sorted_labels[:10]):
                print(f"{i+1:2d}. {label[:40]:<40} F1:{stats['f1']:.3f} P:{stats['precision']:.3f} R:{stats['recall']:.3f} (n={stats['support']})")
            
            print(f"\n⚠️  CHALLENGING LABELS (lowest F1-score)")
            print(f"{'='*50}")
            # Only show labels with reasonable support
            challenging = [(label, stats) for label, stats in sorted_labels 
                          if stats['support'] >= 3][-10:]
            for i, (label, stats) in enumerate(challenging):
                print(f"{i+1:2d}. {label[:40]:<40} F1:{stats['f1']:.3f} P:{stats['precision']:.3f} R:{stats['recall']:.3f} (n={stats['support']})")
        
        # Co-occurrence analysis
        if results['top_cooccurrences']:
            total_cooccurrences = len(results.get('cooccurrence_counts', {}))
            print(f"\n🔗 DISCOVERED GRAMMAR PATTERN RELATIONSHIPS")
            print(f"{'='*60}")
            print(f"Total pattern combinations identified: {total_cooccurrences}")
            print(f"\nMost Frequent Multi-Pattern Samples:")
            print()
            cooccurrence_samples = results['cooccurrence_samples']
            
            for i, ([label1, label2], count) in enumerate(results['top_cooccurrences'][:10]):
                print(f"\n{i+1:2d}. {label1} + {label2} ({count} times)")
                print(f"    {'─'*50}")
                
                # Show sample texts for this pair
                samples = cooccurrence_samples.get(f"{label1}||{label2}", [])
                for j, sample in enumerate(samples[:2]):  # Show up to 2 samples
                    labels_str = ", ".join(sample['labels'])
                    clean = sample['text'].replace('⌈ ', '⌈').replace(' ⌉', '⌉').replace(' ˢ', 'ˢ').replace(' ᵖ', 'ᵖ').replace(' ʳ', 'ʳ').replace(' ', '').strip()
                    print(f"    📝 {compact_sentence_to_japanese(clean)}")
                    print(f"       Labels: [{labels_str}]")
                    if j < len(samples) - 1:
                        print()
        
        print("\n" + "=" * 60)
       
    
    def save_model(self, file_path: str):
        """Save the trained model."""
        model_data = {
            'vectorizer': self.vectorizer,
            'label_binarizer': self.label_binarizer,
            'classifier': self.classifier,
            'label_counts': self.label_counts,
            'valid_labels': self.valid_labels,
            'cooccurrence_counts': getattr(self, 'cooccurrence_counts', {}),
            'cooccurrence_samples': getattr(self, 'cooccurrence_samples', {}),
            'config': {
                'min_label_freq': self.min_label_freq,
                'max_features': self.max_features,
                'ngram_range': self.ngram_range,
                'class_weight': self.class_weight
            }
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        display.check(f"Model saved to {os.path.basename(file_path)}")
    
    def load_model(self, file_path: str):
        """Load a trained model."""
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vectorizer = model_data['vectorizer']
        self.label_binarizer = model_data['label_binarizer']
        self.classifier = model_data['classifier']
        self.label_counts = model_data['label_counts']
        self.valid_labels = model_data['valid_labels']
        self.cooccurrence_counts = model_data.get('cooccurrence_counts', {})
        self.cooccurrence_samples = model_data.get('cooccurrence_samples', {})
        
        # Restore config
        config = model_data['config']
        self.min_label_freq = config['min_label_freq']
        self.max_features = config['max_features']
        self.ngram_range = config['ngram_range']
        self.class_weight = config['class_weight']
        
        display.check(f"Model loaded from {os.path.basename(file_path)}")
        return self
    
    def _analyze_sample_overlap_sampled(self, training_data, max_pairs=1000):
        """Sample similarity analysis with random sampling of label pairs."""
        import random
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Group samples by label
        label_to_samples = defaultdict(list)
        for text, labels in training_data.items():
            for label in labels:
                label_to_samples[label].append(text)
        
        # Get all possible label pairs and sample them
        all_labels = list(label_to_samples.keys())
        all_pairs = list(combinations(all_labels, 2))
        
        if len(all_pairs) <= max_pairs:
            pairs_to_analyze = all_pairs
        else:
            pairs_to_analyze = random.sample(all_pairs, max_pairs)
        
        # Calculate average similarity between sampled label pairs
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        
        similarities = []
        for label1, label2 in pairs_to_analyze:
            samples1 = label_to_samples[label1][:100]  # Cap at 100
            samples2 = label_to_samples[label2][:100]  # Cap at 100
            
            all_samples = samples1 + samples2
            if len(all_samples) < 2:
                continue
                
            # Vectorize
            vectors = vectorizer.fit_transform(all_samples)
            
            # Calculate average cross-similarity
            vectors1 = vectors[:len(samples1)]
            vectors2 = vectors[len(samples1):]
            
            if vectors1.shape[0] > 0 and vectors2.shape[0] > 0:
                cross_sim = cosine_similarity(vectors1, vectors2)
                avg_similarity = float(np.mean(cross_sim))
                similarities.append((label1, label2, avg_similarity))
        
        return sorted(similarities, key=lambda x: x[2], reverse=True)

    def _analyze_sample_overlap(self, training_data):
        """Find labels that appear on very similar samples."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Group samples by label
        label_to_samples = defaultdict(list)
        for text, labels in training_data.items():
            for label in labels:
                label_to_samples[label].append(text)
        
        # Calculate average similarity between label sample sets
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        
        similarities = []
        for label1, label2 in combinations(label_to_samples.keys(), 2):
            samples1 = label_to_samples[label1]
            samples2 = label_to_samples[label2]
            
            # Sample up to 100 examples from each to avoid memory issues
            samples1 = samples1[:100]
            samples2 = samples2[:100]
            
            all_samples = samples1 + samples2
            if len(all_samples) < 2:
                continue
                
            # Vectorize
            vectors = vectorizer.fit_transform(all_samples)
            
            # Calculate average cross-similarity
            vectors1 = vectors[:len(samples1)]
            vectors2 = vectors[len(samples1):]
            
            if vectors1.shape[0] > 0 and vectors2.shape[0] > 0:
                cross_sim = cosine_similarity(vectors1, vectors2)
                avg_similarity = np.mean(cross_sim)
                similarities.append((label1, label2, avg_similarity))
        
        return sorted(similarities, key=lambda x: x[2], reverse=True)

    def _analyze_prediction_confusion(self, texts, labels):
        """Find labels that are frequently confused with each other."""
        predictions = self.predict(texts)
        
        confusion_pairs = defaultdict(int)
        
        for true_set, pred_set in zip(labels, predictions):
            true_set = set(true_set)
            pred_set = set(pred_set)
            
            # Find labels that were predicted but not true (false positives)
            false_positives = pred_set - true_set
            # Find labels that were true but not predicted (false negatives)  
            false_negatives = true_set - pred_set
            
            # Count confusion between FP and FN labels
            for fp_label in false_positives:
                for fn_label in false_negatives:
                    pair = tuple(sorted([fp_label, fn_label]))
                    confusion_pairs[pair] += 1
        
        return sorted(confusion_pairs.items(), key=lambda x: x[1], reverse=True)

    def _find_suspicious_cooccurrences(self):
        """Find label pairs that co-occur more than expected by chance."""
        if not hasattr(self, 'cooccurrence_counts'):
            raise ValueError("No co-occurrence data available")
        
        total_samples = sum(self.label_counts.values())
        suspicious_pairs = []
        
        for pair_key, observed_count in self.cooccurrence_counts.items():
            label1, label2 = pair_key.split("||")
            # Expected co-occurrence if independent
            freq1 = self.label_counts[label1] / total_samples
            freq2 = self.label_counts[label2] / total_samples
            expected_count = freq1 * freq2 * total_samples
            
            # Calculate lift (observed/expected)
            lift = observed_count / expected_count if expected_count > 0 else 0
            
            # Chi-square like statistic
            chi_square = ((observed_count - expected_count) ** 2) / expected_count if expected_count > 0 else 0
            
            suspicious_pairs.append((label1, label2, observed_count, expected_count, lift, chi_square))
        
        return sorted(suspicious_pairs, key=lambda x: x[5], reverse=True) 
    
    def _analyze_label_feature_overlap(self):
        """Find labels with highly overlapping feature importance."""
        if not hasattr(self, 'classifier') or not hasattr(self.classifier, 'estimators_'):
            raise ValueError("Model must be trained first")
        
        label_features = {}
        labels = self.label_binarizer.classes_
        
        # Extract feature importance for each label's binary classifier
        for i, estimator in enumerate(self.classifier.estimators_):
            label = labels[i]
            if hasattr(estimator, 'coef_'):
                # Get top features for this label
                feature_importance = np.abs(estimator.coef_[0])
                top_features = np.argsort(feature_importance)[-100:]  # Top 100 features
                label_features[label] = set(top_features)
        
        # Calculate pairwise overlaps
        overlaps = []
        for label1, label2 in combinations(labels, 2):
            if label1 in label_features and label2 in label_features:
                overlap = len(label_features[label1] & label_features[label2])
                total = len(label_features[label1] | label_features[label2])
                jaccard = overlap / total if total > 0 else 0
                overlaps.append((label1, label2, jaccard, overlap))
        
        return sorted(overlaps, key=lambda x: x[2], reverse=True)
    
    def _test_train_split(self, training_data: Dict[str, List[str]]):
        """
        Split training data into train and test sets.
        
        Args:
            training_data: Dictionary with texts as keys and label lists as values
            
        Returns:
            Tuple of (train_texts, test_texts, train_labels, test_labels)
        """
        all_texts = list(training_data.keys())
        all_labels = list(training_data.values())
        
        # Use same split logic as fit_from_dict
        from sklearn.model_selection import train_test_split
        train_texts, test_texts, train_labels, test_labels = train_test_split(
            all_texts, all_labels, test_size=self.test_size, random_state=self.random_state
        )
        return train_texts, test_texts, train_labels, test_labels

    def analyze_label_interference(self, training_data, 
                                sample_percent=0.1, max_label_pairs=1000):
        """
        Comprehensive analysis of potentially interfering labels with intelligent sampling.
        
        Args:
            training_data: Training data dictionary for all analysis
            sample_percent: Percentage of data to sample (0.1 = 10%). If None, auto-determines based on size
            max_label_pairs: Maximum number of label pairs to analyze for sample similarity (default: 1000)
        """
        import random
        
        # Create test split for prediction confusion analysis
        _, texts, _, labels = self._test_train_split(training_data)
        
        # Count labels to determine if sampling is needed
        total_labels = len(set(label for labels in training_data.values() for label in labels))
        
        
        display.check(f"Label interference analysis: {total_labels} labels, {sample_percent:.1%} sampling")
        
        results = {
            'feature_overlap': None,
            'prediction_confusion': None,
            'sample_similarity': None,
            'suspicious_cooccurrence': None,
            'sampling_info': {
                'total_labels': total_labels,
                'sample_percent': sample_percent,
                'max_label_pairs': max_label_pairs
            }
        }
        
        # 1. Feature overlap analysis (always run - relatively fast)
        with display.work("analyzing feature overlap"):
            results['feature_overlap'] = self._analyze_label_feature_overlap()
        
        # 2. Prediction confusion analysis
        sample_size = len(texts)
        if sample_percent < 1.0:
            sample_size = max(1000, int(len(texts) * sample_percent))  # At least 1000 samples
            if sample_size < len(texts):
                display.check(f"Sampling {sample_size:,} out of {len(texts):,} test samples")
                indices = random.sample(range(len(texts)), sample_size)
                sampled_texts = [texts[i] for i in indices]
                sampled_labels = [labels[i] for i in indices]
            else:
                sampled_texts = texts
                sampled_labels = labels
        else:
            sampled_texts = texts
            sampled_labels = labels
        
        results['sampling_info']['test_samples_used'] = len(sampled_texts)
        
        with display.work("analyzing prediction confusion"):
            results['prediction_confusion'] = self._analyze_prediction_confusion(sampled_texts, sampled_labels)
        
        # 3. Sample similarity analysis with intelligent sampling
        estimated_pairs = (total_labels * (total_labels - 1)) // 2
        
        if estimated_pairs <= max_label_pairs:
            # Small enough to run without sampling
            with display.work("analyzing sample similarity"):
                results['sample_similarity'] = self._analyze_sample_overlap(training_data)
            results['sampling_info']['label_pairs_analyzed'] = estimated_pairs
        else:
            # Need to sample label pairs or labels
            display.check(f"Large label space detected ({estimated_pairs:,} potential pairs)")
            
            if sample_percent >= 0.5:
                # Sample by most frequent labels
                label_counts = Counter(label for labels in training_data.values() for label in labels)
                num_labels_to_keep = int(total_labels * sample_percent)
                top_labels = set(label for label, _ in label_counts.most_common(num_labels_to_keep))
                
                display.check(f"Analyzing top {num_labels_to_keep} most frequent labels")
                
                # Filter training data
                filtered_data = {}
                for text, labels in training_data.items():
                    filtered_labels = [l for l in labels if l in top_labels]
                    if filtered_labels:
                        filtered_data[text] = filtered_labels
                
                with display.work("analyzing sample similarity (top labels)"):
                    results['sample_similarity'] = self._analyze_sample_overlap(filtered_data)
                results['sampling_info']['label_pairs_analyzed'] = (num_labels_to_keep * (num_labels_to_keep - 1)) // 2
            else:
                # Random sampling of label pairs
                display.check(f"Randomly sampling {max_label_pairs:,} label pairs from {estimated_pairs:,}")
                
                with display.work("analyzing sample similarity (sampled pairs)"):
                    results['sample_similarity'] = self._analyze_sample_overlap_sampled(
                        training_data, max_pairs=max_label_pairs
                    )
                results['sampling_info']['label_pairs_analyzed'] = max_label_pairs
        
        # 4. Co-occurrence analysis (always fast)
        with display.work("analyzing suspicious co-occurrences"):
            results['suspicious_cooccurrence'] = self._find_suspicious_cooccurrences()
        
        return results

    def dump_interference_analysis(self, results):
        """Generate interference analysis results as formatted text."""
        output = []
        output.append(f"\n🎯 LABEL REFINEMENT OPPORTUNITIES")
        output.append("=" * 50)
        
        # Show sampling information
        if 'sampling_info' in results:
            info = results['sampling_info']
            output.append(f"\n📋 ANALYSIS SCOPE")
            output.append("-" * 20)
            output.append(f"Total labels: {info['total_labels']:,}")
            output.append(f"Sampling rate: {info['sample_percent']:.1%}")
            if 'test_samples_used' in info:
                output.append(f"Test samples analyzed: {info['test_samples_used']:,}")
            if 'label_pairs_analyzed' in info:
                output.append(f"Label pairs analyzed: {info['label_pairs_analyzed']:,}")
        
        if results['feature_overlap']:
            output.append(f"\n📊 LABELS NEEDING DISTINCTION IMPROVEMENT")
            output.append("-" * 30)
            for label1, label2, jaccard, overlap in results['feature_overlap'][:10]:
                output.append(f"{label1[:30]} ↔ {label2[:30]}: {jaccard:.3f} jaccard ({overlap} features)")
        
        if results['prediction_confusion']:
            output.append("\n🔀 SYSTEMATIC CONFUSION PATTERNS (Top 10)")
            output.append("-" * 30)
            for (label1, label2), count in results['prediction_confusion'][:10]:
                output.append(f"{label1[:30]} ↔ {label2[:30]}: confused {count} times")
        else:
            output.append("\n🔀 SYSTEMATIC CONFUSION PATTERNS")
            output.append("-" * 30)
            output.append("❌ No prediction confusion data available")
        
        if results['sample_similarity']:
            output.append("\n📝 SIMILAR PATTERN CONTEXTS (Top 10)")
            output.append("-" * 30)
            for label1, label2, similarity in results['sample_similarity'][:10]:
                output.append(f"{label1[:30]} ↔ {label2[:30]}: {similarity:.3f} avg similarity")
        
        if results['suspicious_cooccurrence']:
            output.append("\n🔗 UNEXPECTEDLY FREQUENT COMBINATIONS (Top 10)")
            output.append("-" * 30)
            for label1, label2, _, _, lift, chi2 in results['suspicious_cooccurrence'][:10]:
                output.append(f"{label1[:30]} ↔ {label2[:30]}: {lift:.2f}x more than expected (χ²={chi2:.1f})")
        
        # Remove the section that tries to access evaluation metrics
        # since this method is for interference analysis, not evaluation results
        output.append(f"\n💡 NEXT STEPS")
        output.append(f"{'='*30}")
        output.append("1. Review high-overlap feature pairs for potential label consolidation")
        output.append("2. Examine systematic confusion patterns for training improvements")
        output.append("3. Investigate similar pattern contexts for label refinement")
        output.append("4. Consider splitting unexpectedly frequent combinations")
        
        return "\n".join(output)
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
    
    classifier = JapaneseGrammarLabelCompletingClassifier(
        min_label_freq=3,  # Adjust based on your data
        max_features=20000,
        ngram_range=(1, 3)
    )

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
