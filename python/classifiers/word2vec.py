import os
from python.console import display
from python.classifiers.gather_sentences import (
        gather_training_data,
    )
from gensim.models import FastText
import numpy as np

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from python.mecab.compact_sentence import compact_sentence_to_japanese, split_compact_sentence
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter, defaultdict


# 1. Intrinsic dimensionality estimation
def estimate_intrinsic_dim(model, sample_size=1000):
    """Estimate if vector_size captures enough variance"""
    words = list(model.wv.key_to_index.keys())[:sample_size]
    vectors = np.array([model.wv[word] for word in words])
    
    # PCA to see how much variance is captured
    from sklearn.decomposition import PCA
    pca = PCA()
    pca.fit(vectors)
    
    # Find dimensions needed for 90%, 95%, 99% variance
    cumsum = np.cumsum(pca.explained_variance_ratio_)
    dims_90 = np.argmax(cumsum >= 0.90) + 1
    dims_95 = np.argmax(cumsum >= 0.95) + 1
    dims_99 = np.argmax(cumsum >= 0.99) + 1
    
    print(f"Dimensions needed for 90% variance: {dims_90}")
    print(f"Dimensions needed for 95% variance: {dims_95}")
    print(f"Dimensions needed for 99% variance: {dims_99}")
    print(f"Current vector_size: {model.wv.vector_size}")
    
    return dims_90, dims_95, dims_99

# 2. Saturation analysis - do larger dimensions help?
def analyze_vector_saturation(texts, sizes=[50, 100, 200, 300]):
    """Train models with different vector sizes and compare performance"""
    
    results = {}
    for size in sizes:
        model_temp = FastText(texts, vector_size=size, window=5, 
                             min_count=1, workers=14, sg=1)
        
        # Test on word similarity task (if you have word pairs)
        # Or use internal coherence metrics
        avg_similarity = []
        words = list(model_temp.wv.key_to_index.keys())[:100]
        
        for word in words[:10]:  # Sample some words
            if word in model_temp.wv:
                similar = model_temp.wv.most_similar(word, topn=5)
                avg_sim = np.mean([sim for _, sim in similar])
                avg_similarity.append(avg_sim)
        
        results[size] = np.mean(avg_similarity)
        print(f"Vector size {size}: avg similarity = {results[size]:.3f}")
    
    return results

def analyze_min_count_impact(texts, min_counts=[1, 2, 5, 10]):
    """See how min_count affects vocabulary and quality"""
    
    for min_count in min_counts:
        model_temp = FastText(texts, vector_size=100, window=5, 
                             min_count=min_count, workers=14)
        
        vocab_size = len(model_temp.wv.key_to_index)
        
        # Calculate average vector quality (coherence)
        coherence_scores = []
        sample_words = list(model_temp.wv.key_to_index.keys())[:20]
        
        for word in sample_words:
            similar = model_temp.wv.most_similar(word, topn=5)
            avg_sim = np.mean([sim for _, sim in similar])
            coherence_scores.append(avg_sim)
        
        avg_coherence = np.mean(coherence_scores)
        
        print(f"min_count={min_count}: vocab={vocab_size}, "
              f"avg_coherence={avg_coherence:.3f}")

def check_training_convergence(model):
    """Analyze if model has trained enough"""
    
    # 1. Loss progression (if available in your version)
    if hasattr(model, 'running_training_loss'):
        print(f"Final training loss: {model.running_training_loss}")
    
    # 2. Vector stability test
    # Train a bit more and see if vectors change significantly
    original_vectors = {word: model.wv[word].copy() 
                       for word in list(model.wv.key_to_index.keys())[:10]}
    
    # Continue training
    model.train([["additional", "training", "data"]], 
                total_examples=1, epochs=1)
    
    # Check vector drift
    vector_changes = []
    for word, orig_vec in original_vectors.items():
        if word in model.wv:
            new_vec = model.wv[word]
            change = np.linalg.norm(new_vec - orig_vec)
            vector_changes.append(change)
    
    avg_change = np.mean(vector_changes)
    print(f"Average vector change after additional training: {avg_change:.6f}")
    print("Low change suggests convergence, high change suggests more training needed")

def comprehensive_quality_check(model):
    """Multi-faceted quality assessment"""
    
    # 1. Vocabulary coverage
    vocab_size = len(model.wv.key_to_index)
    print(f"Vocabulary size: {vocab_size}")
    
    # 2. Vector space density
    sample_words = list(model.wv.key_to_index.keys())[:100]
    vectors = np.array([model.wv[word] for word in sample_words])
    
    # Average cosine similarity (should not be too high or too low)
    similarity_matrix = cosine_similarity(vectors)
    avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
    print(f"Average pairwise similarity: {avg_similarity:.3f}")
    print("Good range: 0.1-0.4 (too low=sparse, too high=collapsed)")
    
    # 3. Nearest neighbor consistency
    consistency_scores = []
    for word in sample_words[:20]:
        neighbors = model.wv.most_similar(word, topn=5)
        # Check if the word appears in its neighbors' neighbor lists
        mutual_neighbors = 0
        for neighbor, _ in neighbors:
            neighbor_neighbors = model.wv.most_similar(neighbor, topn=10)
            if word in [nn[0] for nn in neighbor_neighbors]:
                mutual_neighbors += 1
        consistency_scores.append(mutual_neighbors / 5)
    
    avg_consistency = np.mean(consistency_scores)
    print(f"Neighborhood consistency: {avg_consistency:.3f}")
    print("Higher is better (0.2-0.5 is typical)")

def parse_rich_token(token_string):
    """Parses your complex token into a dictionary."""
    if not token_string.startswith('⌈ˢ') or not token_string.endswith('⌉'):
        return {'raw': token_string} # Not a rich token

    parts = token_string[1:-1].split('ᵖ')
    surface_form = parts[0][1:]
    
    info = {'surface': surface_form}
    
    if len(parts) > 1:
        # Split by the markers ᵇ, ᵈ, ʳ
        # This is a simplified parser; a regex one would be more robust
        details = parts[1]
        
        # Extract POS tag (up to the first marker)
        pos_part = details.split('ᵇ')[0]
        info['pos'] = pos_part

        if 'ᵇ' in details:
            info['base'] = details.split('ᵇ')[1].split('ᵈ')[0].split('ʳ')[0]
        if 'ᵈ' in details:
             info['dict'] = details.split('ᵈ')[1].split('ʳ')[0]
        if 'ʳ' in details:
            info['reading'] = details.split('ʳ')[1]
            
    return info

def discover_clusters(model, num_clusters=20):
    """
    Performs K-Means clustering on all vectors to find macro-groups.
    """
    vectors = model.wv.vectors
    words = model.wv.index_to_key
    
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
    kmeans.fit(vectors)
    
    # Group words by their assigned cluster
    clusters = defaultdict(list)
    for word, label in zip(words, kmeans.labels_):
        clusters[label].append(word)
        
    # Print a sample from each cluster to identify its theme
    for i in range(num_clusters):
        # Analyze the most common POS tags in the cluster
        pos_counts = Counter(
            parse_rich_token(token).get('pos', 'N/A')
            for token in clusters[i]
        )
        most_common_pos = pos_counts.most_common(1)[0]
        
        print(f"\n--- Cluster {i} (Theme: {most_common_pos[0]}) ---")
        print(f"({most_common_pos[1]} of {len(clusters[i])} tokens have this POS tag)")
        
        # Print a few random examples
        sample_size = min(5, len(clusters[i]))
        for token in np.random.choice(clusters[i], sample_size, replace=False):
            parsed = parse_rich_token(token)
            print(f"  - {parsed.get('surface', '')} ({parsed.get('pos', 'N/A')})")


if __name__ == '__main__':
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = f"{workspace_root}/resources/processed/ai-cleaned-merge-grammars"

    display.start()

    training_data = gather_training_data(
        grammar_root, 
        matcher_augment=True)
    tokenized = []
    for instance in training_data['positive']:
        tokens = split_compact_sentence(instance)
        grammar_points = training_data['positive'][instance]
        if grammar_points:
            tokens.extend(grammar_points)

        #tokens = compact_sentence_to_japanese(instance, spaces=True, collapse_punctuation=False).split(' ')
        tokenized.append(tokens)

    with display.work("training fast text"):
        model = FastText(tokenized, vector_size=100, window=5, min_count=1, workers=14)


    display.stop()

    # 1. Identify the anchor token for 'tsumori'
    # You would search your vocab for the token containing 'つもり'
    anchor_token = "⌈ˢかったᵖadj:general:adjective:stemᵇかったいᵈ固いʳカッタ⌉" # Example rich token
    print(f"anchor token: {anchor_token}")

    # 2. (Optional) Validate its role by finding neighbors
    # This should show other nominalizers like はず, こと, もの etc.
    print("--- Neighbors of the anchor ---")
    for neighbor, sim in model.wv.most_similar(anchor_token, topn=10):
        print(neighbor)

    # 3 & 4. Find all preceding tokens in the corpus
    preceding_tokens = []
    for sentence in tokenized:
        for i, token in enumerate(sentence):
            if token == anchor_token and i > 0:
                # Get the token right before the anchor
                preceding_token = sentence[i-1]
                preceding_tokens.append(preceding_token)

    # 5. Count the frequencies of what comes before 'tsumori'
    print("\n--- Most Common Preceding POS Tags for 'つもり' ---")
    preceding_pos_counts = Counter(
        parse_rich_token(tok).get('pos', 'N/A') for tok in preceding_tokens
    )

    for pos, count in preceding_pos_counts.most_common(5):
        print(f"{pos}: {count} times")
        
    # vocabulary = model.wv.index_to_key


    # Print the first 20 and a random sample of 20 tokens
    # print("--- First 20 Tokens in Vocabulary ---")
    # for token in vocabulary[:20]:
    #     print(token)

    # print("\n--- Random 20 Tokens in Vocabulary ---")
    # import random
    # for token in random.sample(vocabulary, 20):
    #     print(token)

    discover_clusters(model)

    print(f"Training set size: {len(tokenized)})")
    print(f"Example: {tokenized[37]}")
    print(f"Vocabulary size: {len(model.wv.key_to_index)}")
    print(f"Vector dimensions: {model.wv.vector_size}")
    print(f"Training algorithm: {model.sg}")  # 0=CBOW, 1=Skip-gram
    print(f"Window size: {model.window}")
    print(f"Min word count: {model.min_count}")
    print(f"Total training words: {model.corpus_total_words}")

    # Most/least frequent words
    vocab_freq = [(word, model.wv.get_vecattr(word, "count")) 
                for word in model.wv.key_to_index]
    vocab_freq.sort(key=lambda x: x[1], reverse=True)

    print("Most frequent words:")
    for word, freq in vocab_freq[:10]:
        print(f"{word}: {freq}")

    print("\nLeast frequent words:")
    for word, freq in vocab_freq[-10:]:
        print(f"{word}: {freq}")

    # Calculate average vector magnitude
    magnitudes = [np.linalg.norm(model.wv[word]) for word in model.wv.key_to_index]
    print(f"Average vector magnitude: {np.mean(magnitudes):.3f}")
    print(f"Vector magnitude std: {np.std(magnitudes):.3f}")

    # Find words with highest/lowest magnitudes
    word_mags = [(word, np.linalg.norm(model.wv[word])) 
                for word in model.wv.key_to_index]
    word_mags.sort(key=lambda x: x[1], reverse=True)
    print(f"Highest magnitude: {word_mags[0]}")
    print(f"Lowest magnitude: {word_mags[-1]}")

    with display.work("estimating intrinsic dim"):
        estimate_intrinsic_dim(model)
    with display.work("analyzing vector saturation"):
        analyze_vector_saturation(tokenized)
    with display.work("analyzing min count"):
        analyze_min_count_impact(tokenized)
    with display.work("checking training convergence"):
        check_training_convergence(model)
    with display.work("checking quality"):
        comprehensive_quality_check(model)