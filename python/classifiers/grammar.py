
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer, MaxAbsScaler
from sklearn.metrics import hamming_loss, jaccard_score
import pickle
from typing import List, Dict, Union
import warnings
warnings.filterwarnings('ignore')

from python.mecab.compact_sentence import compact_sentence_to_japanese, japanese_to_compact_sentence
from python.console import display
import numpy as np
from itertools import combinations
import os

from python.classifiers.training_tokens import prepare_sentence_for_tokenization



class JapaneseGrammarLabelCompletingClassifier:
    """
    Multi-label classifier for Japanese grammar patterns using logistic regression.
    Handles imbalanced data with configurable parameters.
    """
    
    def __init__(self, 
                 min_label_freq=3,
                 max_features=7500,
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
        self.scaler = None # <-- Added scaler
        self.label_binarizer = None
        self.classifier = None
        self.label_counts = None
        self.valid_labels = None
    
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
        # Good: 2000 iterations/liblinear/l1/C=1.5/features=5000
        base_classifier = LogisticRegression(
            max_iter=7500,
            class_weight=self.class_weight,
            random_state=self.random_state,
            solver='liblinear',
            # solver='saga',      # Use the SAGA solver
            # penalty='elasticnet',
            # l1_ratio=0.01
            penalty='l1',
            # l1_ratio=0.1,
            # penalty='l1',       # Enable L1 regularization for sparsity
            C=1.9,
            # n_jobs=-1  
            # verbose=1
        )
        # display.check(f"{base_classifier}")
        # display.check(f"  solver={base_classifier.solver}")
        # display.check(f"  penalty={base_classifier.penalty}")
        
        
        # Use OneVsRestClassifier for multi-label classification
        self.classifier = OneVsRestClassifier(base_classifier, n_jobs=-1)
        
    
    def fit_from_dict(self, data: Dict[str, List[str]], test_split = True):
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
        
        if test_split:  # Only split if we have enough data
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
            display.warn("Full training with no test split")
            self.fit(texts, labels)
            return None # No evaluation results in this case
    
    def fit(self, texts: List[str], labels: List[List[str]]):
        """Train the classifier.
        
        Args:
            texts: List of texts with positive examples
            labels: List of label lists for positive examples
        """
        # Clean texts and filter labels
        with display.work("preprocessing"):
            cleaned_texts = [prepare_sentence_for_tokenization(text) for text in texts]
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
        
        with display.work("scaling features"):
            self.scaler = MaxAbsScaler()
            X_scaled = self.scaler.fit_transform(X)
        
        # Prepare labels
        with display.work("preparing labels"):
            self.label_binarizer = MultiLabelBinarizer()
            y = self.label_binarizer.fit_transform(filtered_labels)
            # display.check(f"Label matrix shape: {y.shape}")
            # display.check(f"Active labels: {len(self.label_binarizer.classes_)}")
        
        # Train classifier
        with display.work("training model"):
            self._setup_classifier()
            self.classifier.fit(X_scaled, y)
        
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
        
        # display.check("Training completed!")
        return self
    
    def predict(self, texts: Union[str, List[str], Dict[str, List[str]]], 
                threshold: float = 0.5) -> Union[List[str], List[List[str]], Dict[str, List[str]]]:
        """
        Predict labels for input texts.
        
        Args:
            texts: Single text or list of texts
            threshold: Probability threshold for predictions
            
        Returns:
            List of labels for single text, or list of label lists for multiple texts
        """

        if isinstance(texts, dict):
            sentences = list(texts.keys())
            predictions = self.predict(sentences, threshold)
            return dict(zip(sentences, predictions))
        if isinstance(texts, str):
            prediction = self.predict([texts])
            return prediction[0]

        # Clean and vectorize texts
        cleaned_texts = [prepare_sentence_for_tokenization(text) for text in texts]
        X = self.vectorizer.transform(cleaned_texts)
        
        # --- ADDED: Apply the same scaling ---
        X_scaled = self.scaler.transform(X)
        
        # Get probability predictions
        if hasattr(self.classifier, "predict_proba"):
            # For logistic regression classifier that supports predict_proba
            try:
                y_prob = self.classifier.predict_proba(X_scaled) # <-- Use scaled data
                # Convert to binary predictions based on threshold
                y_pred = (y_prob >= threshold).astype(int)
            except:
                # Fallback to decision_function or predict
                if hasattr(self.classifier, "decision_function"):
                    y_scores = self.classifier.decision_function(X_scaled) # <-- Use scaled data
                    y_pred = (y_scores >= 0).astype(int)
                else:
                    y_pred = self.classifier.predict(X_scaled) # <-- Use scaled data
        else:
            y_pred = self.classifier.predict(X_scaled) # <-- Use scaled data
        
        # Convert back to labels
        predicted_labels = self.label_binarizer.inverse_transform(y_pred)
        
        # Convert tuples to lists and handle empty predictions
        result = []
        for labels in predicted_labels:
            if len(labels) == 0:
                # If no labels predicted, return most frequent label as fallback
                if self.label_counts:
                    most_frequent_label = self.label_counts.most_common(1)[0][0]
                    result.append([most_frequent_label])
                else:
                    result.append([]) # Should not happen if model is fitted
            else:
                result.append(list(labels))
        
        return result
    
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
        import os
        model_data = {
            'vectorizer': self.vectorizer,
            'scaler': self.scaler, # <-- Save the scaler
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
        self.scaler = model_data['scaler'] # <-- Load the scaler
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

    def _analyze_label_feature_overlap(self, min_support=10):
        """
        Find labels with highly overlapping feature importance, considering only features
        with non-zero weights and sufficient support.
        """
        if not hasattr(self, 'classifier') or not hasattr(self.classifier, 'estimators_'):
            raise ValueError("Model must be trained first")
        
        label_features = {}
        all_labels = self.label_binarizer.classes_
        
        # Filter for labels that have enough training examples to be reliable
        supported_labels = {label for label, count in self.label_counts.items() 
                            if count >= min_support}
        if not supported_labels:
            return []

        # --- Part 1: Build the feature set for each supported label ---
        for i, estimator in enumerate(self.classifier.estimators_):
            label = all_labels[i]
            
            # Skip labels that are too rare
            if label not in supported_labels:
                continue
            
            if hasattr(estimator, 'coef_'):
                feature_importance = np.abs(estimator.coef_[0])
                
                # Filter for features with non-zero weights
                non_zero_indices = np.where(feature_importance > 0)[0]
                if len(non_zero_indices) == 0:
                    continue

                # Get the importance scores for ONLY the non-zero features
                active_importances = feature_importance[non_zero_indices]
                
                # Sort these active features to find the top N
                sorted_active_indices = np.argsort(active_importances)
                
                num_top_features = min(100, len(sorted_active_indices))
                top_feature_indices = non_zero_indices[sorted_active_indices[-num_top_features:]]
                
                label_features[label] = set(top_feature_indices)
        
        # --- Part 2: Calculate pairwise overlaps (This was the missing part) ---
        overlaps = []
        # Note: We iterate through the original list of supported labels
        for label1, label2 in combinations(sorted(list(supported_labels)), 2):
            # Ensure both labels were processed and are in the dictionary
            if label1 in label_features and label2 in label_features:
                intersection_set = label_features[label1] & label_features[label2]
                union_set = label_features[label1] | label_features[label2]
                
                jaccard = len(intersection_set) / len(union_set) if len(union_set) > 0 else 0
                
                # Optional: Add a threshold to reduce noise in the final report
                if jaccard > 0.05:
                    overlaps.append((label1, label2, jaccard, len(intersection_set)))
        
        return sorted(overlaps, key=lambda x: x[2], reverse=True)

    def _find_merge_candidates(self, training_data, min_cooccurrence_rate=0.8, min_samples=10):
        """
        [CORRECTED] Finds grammar points that are likely identical by pre-calculating
        predictions in manageable batches. This version fixes the AttributeError.

        Args:
            training_data: Training data dictionary
            min_cooccurrence_rate: Minimum rate of co-occurrence to consider for merging
            min_samples: Minimum number of samples for a label to be considered
        """
        import random
        from collections import defaultdict

        # 1. Build label-to-texts mapping and filter for labels with enough samples
        label_to_texts = defaultdict(list)
        for text, labels in training_data.items():
            for label in labels:
                label_to_texts[label].append(text)

        valid_labels = {label: texts for label, texts in label_to_texts.items()
                        if len(texts) >= min_samples}

        if len(valid_labels) < 2:
            return []

        # 2. Pre-sample all texts to identify the full set that needs prediction
        label_to_sampled_texts = {}
        all_texts_to_predict = set()

        for label, texts in valid_labels.items():
            sample_texts = random.sample(texts, min(100, len(texts)))
            label_to_sampled_texts[label] = sample_texts
            all_texts_to_predict.update(sample_texts)

        # 3. Run prediction in batches to manage memory
        predictions_cache = {}
        unique_texts_list = list(all_texts_to_predict)
        batch_size = 5000
        total_batches = (len(unique_texts_list) + batch_size - 1) // batch_size

        # The initial message now includes all relevant info, and the problematic p.update() is removed.
        for i in range(0, len(unique_texts_list), batch_size):
            batch_texts = unique_texts_list[i:i + batch_size]
            batch_predictions = self.predict(batch_texts)
            
            # Update the cache with the results from the current batch
            predictions_cache.update({text: preds for text, preds in zip(batch_texts, batch_predictions)})

        # 4. Build the co-occurrence matrix using the pre-computed predictions
        cooccurrence_matrix = defaultdict(lambda: defaultdict(int))
        label_prediction_counts = defaultdict(int)
        shared_examples = defaultdict(lambda: defaultdict(list))

        for label, sampled_texts in label_to_sampled_texts.items():
            for text in sampled_texts:
                predicted_labels = predictions_cache.get(text, [])
                label_prediction_counts[label] += 1
                for pred_label in predicted_labels:
                    if pred_label != label and pred_label in valid_labels:
                        cooccurrence_matrix[label][pred_label] += 1
                        if len(shared_examples[label][pred_label]) < 3:
                            shared_examples[label][pred_label].append(text)

        # 5. Calculate merge candidates (logic remains unchanged)
        merge_candidates = []
        for label1 in valid_labels:
            if label_prediction_counts[label1] == 0:
                continue
            for label2, cooccurrence_count in cooccurrence_matrix[label1].items():
                if label1 >= label2:
                    continue
                rate1 = cooccurrence_count / label_prediction_counts[label1]
                rate2 = cooccurrence_count / label_prediction_counts.get(label2, 1)
                avg_rate = (rate1 + rate2) / 2
                if avg_rate >= min_cooccurrence_rate:
                    merge_candidates.append({
                        'label1': label1,
                        'label2': label2,
                        'similarity_score': avg_rate,
                        'shared_samples': cooccurrence_count,
                        'total_samples_1': len(valid_labels[label1]),
                        'total_samples_2': len(valid_labels[label2]),
                        'jaccard': 0,
                        'overlap_ratio_1': rate1,
                        'overlap_ratio_2': rate2,
                        'sample_texts': shared_examples[label1][label2]
                    })

        return sorted(merge_candidates, key=lambda x: x['similarity_score'], reverse=True)

    def _test_train_split(self, training_data: Dict[str, List[str]]):
        """
        Split training data into train and test sets using stratification.
        """
        all_texts = list(training_data.keys())
        all_labels_list = list(training_data.values())
        
        # You need a binary matrix for stratification in multi-label scenarios
        mlb = MultiLabelBinarizer()
        all_labels_binarized = mlb.fit_transform(all_labels_list)

        # Use stratify on the binarized labels
        # Note: Stratification in multi-label settings can be complex.
        # For simpler cases, you might stratify on the presence of rare labels,
        # but sklearn's train_test_split doesn't support this directly for multilabel.
        # A common library for this is scikit-multilearn.
        
        # --- Simple (non-stratified) way from your original code ---
        # train_texts, test_texts, train_labels, test_labels = train_test_split(
        #     all_texts, all_labels_list, 
        #     test_size=self.test_size, 
        #     random_state=self.random_state
        # )
        
        # --- Using scikit-multilearn for a proper stratified split ---
        from skmultilearn.model_selection import iterative_train_test_split
        
        # iterative_train_test_split needs numpy arrays
        X = np.array(all_texts).reshape(-1, 1)
        y = all_labels_binarized
        
        X_train, y_train, X_test, y_test = iterative_train_test_split(X, y, test_size=self.test_size)
        
        # Convert back to original formats
        train_texts = X_train.flatten().tolist()
        test_texts = X_test.flatten().tolist()
        train_labels = mlb.inverse_transform(y_train)
        test_labels = mlb.inverse_transform(y_test)

        return train_texts, test_texts, train_labels, test_labels

    def analyze_label_interference(self, training_data, 
                                sample_percent=0.1, max_label_pairs=1000,
                                feature_overlap=True,
                                merge_candidates=True):
        """
        Comprehensive analysis of potentially interfering labels with intelligent sampling.
        
        Args:
            training_data: Training data dictionary for all analysis
            sample_percent: Percentage of data to sample (0.1 = 10%). If None, auto-determines based on size
            max_label_pairs: Maximum number of label pairs to analyze for sample similarity (default: 1000)
            feature_overlap: Whether to analyze feature overlap between labels
            merge_candidates: Whether to find grammatically identical labels that should be merged
        """
        
        # Count labels to determine if sampling is needed
        total_labels = len(set(label for labels in training_data.values() for label in labels))
        
        
        display.check(f"Label interference analysis: {total_labels} labels, {sample_percent:.1%} sampling")
        
        results = {
            'feature_overlap': None,
            'merge_candidates': None,
            'sampling_info': {
                'total_labels': total_labels,
                'sample_percent': sample_percent,
                'max_label_pairs': max_label_pairs
            }
        }
        
        # 1. Feature overlap analysis
        if feature_overlap:
            with display.work("analyzing feature overlap"):
                results['feature_overlap'] = self._analyze_label_feature_overlap()
        
        # 2. Merge candidates analysis
        if merge_candidates:
            with display.work("finding merge candidates"):
                candidates = self._find_merge_candidates(training_data)
                results['merge_candidates'] = candidates
                display.check(f"Found {len(candidates)} merge candidates")
        
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
        
        if results['feature_overlap']:
            output.append(f"\n📊 LABELS NEEDING DISTINCTION IMPROVEMENT")
            output.append("-" * 30)
            for label1, label2, jaccard, overlap in results['feature_overlap'][:10]:
                output.append(f"{label1[:30]} ↔ {label2[:30]}: {jaccard:.3f} jaccard ({overlap} features)")
        
        if results.get('merge_candidates'):
            output.append("\n🔀 RECOMMENDED GRAMMAR POINT MERGES (Top 10)")
            output.append("-" * 30)
            output.append("These grammar points appear to be functionally identical:")
            output.append("")
            
            for i, candidate in enumerate(results['merge_candidates'][:10]):
                label1 = candidate['label1']
                label2 = candidate['label2']
                score = candidate['similarity_score']
                shared = candidate['shared_samples']
                total1 = candidate['total_samples_1']
                total2 = candidate['total_samples_2']
                overlap1 = candidate['overlap_ratio_1']
                overlap2 = candidate['overlap_ratio_2']
                
                output.append(f"{i+1}. {label1[:40]} ≈ {label2[:40]}")
                output.append(f"   Similarity: {score:.1%} | Examples: {total1} vs {total2}")
                if shared > 0:
                    output.append(f"   Coverage: {overlap1:.1%} of '{label1[:30]}' | {overlap2:.1%} of '{label2[:30]}'")
                
                # Show a sample shared sentence
                if candidate.get('sample_texts'):
                    sample = candidate['sample_texts'][0]
                    # Convert back to Japanese for readability
                    clean = sample.replace('⌈ ', '⌈').replace(' ⌉', '⌉').replace(' ˢ', 'ˢ').replace(' ᵖ', 'ᵖ').replace(' ʳ', 'ʳ').replace(' ', '').strip()
                    try:
                        japanese = compact_sentence_to_japanese(clean)
                        output.append(f"   Example: {japanese}")
                    except:
                        output.append(f"   Example: {clean[:60]}...")
                
                if i < len(results['merge_candidates'][:10]) - 1:
                    output.append("")
        
        # Remove the section that tries to access evaluation metrics
        # since this method is for interference analysis, not evaluation results
        output.append(f"\n💡 NEXT STEPS")
        output.append(f"{'='*30}")
        output.append("1. Review high-overlap feature pairs for potential label consolidation")
        output.append("2. Merge grammatically identical labels identified above")
        
        return "\n".join(output)
    

    
def apply_negatives(
        positives: Dict[str, List[str]], 
        negatives: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Add negatives to the corpus and remove the negated labels"""
    positives = positives.copy()
    for negative in negatives.keys():
        positive_labels = set(positives.get(negative, []))
        negative_labels = set(negatives[negative])
        positives[negative] = list(positive_labels - negative_labels)
    return positives
    

def union_positives(*dicts: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Combines multiple dictionaries by unioning values with the same key.

    Args:
        *dicts: A variable number of dictionaries, where keys are strings
                and values are lists of strings.

    Returns:
        A single dictionary representing the union of all input dictionaries,
        where values for common keys are the union of their respective lists.
    """
    result: Dict[str, set[str]] = {} # Use sets internally for efficient union operations

    for d in dicts:
        for key, values in d.items():
            if key not in result:
                result[key] = set() # Initialize with an empty set if key is new
            result[key].update(values) # Add all elements from the current list to the set

    # Convert all sets back to lists for the final result
    final_result: Dict[str, List[str]] = {}
    for key, s in result.items():
        final_result[key] = list(s)

    return final_result
