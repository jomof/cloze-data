from python.mapreduce import MapReduce
import os
import asyncio
import yaml
from python.console import display
from python.mecab.compact_sentence import (
    japanese_to_compact_sentence,
    get_token_pairs
)

token_count_accumulator = {}
sorted_tokens = {}
tokens_ranked = {}
ranked_sentences = []
registered_tokens = set()
new_sentences = []  # Track new sentences found in current run
ranked_sentences_file = "/workspaces/cloze-data/ranked_sentences.yml"

def load_ranked_sentences():
    """Load ranked sentences and registered tokens from YAML file."""
    global ranked_sentences, registered_tokens
    if os.path.exists(ranked_sentences_file):
        with open(ranked_sentences_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data:
                ranked_sentences = [
                    (item['cost'], item['sentence'], item['tokens'], item.get('english', []))
                    for item in data.get('ranked_sentences', [])
                ]
                registered_tokens = set(data.get('registered_tokens', []))

def save_ranked_sentences():
    """Save ranked sentences and registered tokens to YAML file."""
    data = {
        'ranked_sentences': [
            {'cost': cost, 'sentence': sentence, 'tokens': tokens, 'english': english}
            for cost, sentence, tokens, english in ranked_sentences
        ],
        'registered_tokens': sorted(list(registered_tokens))
    }
    with open(ranked_sentences_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def map(grammar_point, _):
    examples = grammar_point.get('examples', [])
    token_count = {}
    for example in examples:
        japaneses = example.get('japanese', [])
        for japanese in japaneses:
            compact = japanese_to_compact_sentence(japanese.replace('{', '').replace('}', ''))
            tokens = get_token_pairs(compact)
            for token in tokens:
                token_count[token] = token_count.get(token, 0) + 1
    return grammar_point, token_count


def fold(_, grammar_tokens):
    global token_count_accumulator
    grammar_point, token_count = grammar_tokens
    for token, count in token_count.items():
        token_count_accumulator[token] = token_count_accumulator.get(token, 0) + count

def map_and_rank_sentences(grammar_point, _):
    examples = grammar_point.get('examples', [])
    sentence_costs = []

    for example in examples:
        english = example.get('english', [])
        japaneses = example.get('japanese', [])
        for japanese in japaneses:
            # Skip if sentence is already ranked
            if any(japanese == s for _, s, _, _ in ranked_sentences):
                continue

            # Clean the sentence
            cleaned = japanese.replace('{', '').replace('}', '')
            compact = japanese_to_compact_sentence(cleaned)
            tokens = get_token_pairs(compact)

            # Calculate cost: sum of rank for tokens not in registered_tokens
            cost = 0
            for token in tokens:
                if token not in registered_tokens and token in tokens_ranked:
                    rank = tokens_ranked[token]
                    cost += rank

            sentence_costs.append((cost, japanese, tokens, english))

    return grammar_point, sentence_costs

def fold_ranked_sentences(_, grammar_sentence_costs):
    global new_sentences
    grammar_point, sentence_costs = grammar_sentence_costs

    for cost, sentence, tokens, english in sentence_costs:
        # If this is the first new sentence or matches current best cost
        if not new_sentences or cost == new_sentences[0][0]:
            new_sentences.append((cost, sentence, tokens, english))
        # If we found a better (lower) cost sentence, replace all
        elif cost < new_sentences[0][0]:
            new_sentences[:] = [(cost, sentence, tokens, english)]

def rank_tokens_by_frequency():
    global sorted_tokens, tokens_ranked
    mr = MapReduce(
            input_dir            = grammar_root,
            map_func_name        = 'calculating',
            map_func             = map,
            fold_func_name       = 'accumulating',
            fold_func            = fold,
            max_threads          = 14,
        )
    asyncio.run(mr.run())
    # Sort all tokens by frequency (descending)
    sorted_tokens = sorted(token_count_accumulator.items(), key=lambda x: x[1], reverse=True)
    # Create tokens_ranked: token -> rank (0-based)
    tokens_ranked = {token: rank for rank, (token, _) in enumerate(sorted_tokens)}

def rank_sentences():
    global ranked_sentences, registered_tokens, new_sentences
    new_sentences = []  # Clear new sentences for this run
    mr = MapReduce(
            input_dir            = grammar_root,
            map_func_name        = 'ranking',
            map_func             = map_and_rank_sentences,
            fold_func_name       = 'collecting',
            fold_func            = fold_ranked_sentences,
            max_threads          = 14,
        )
    asyncio.run(mr.run())

    # Sort new sentences lexically (they already have the same lowest cost)
    new_sentences.sort(key=lambda x: x[1])

    # Append new sentences to ranked_sentences
    ranked_sentences.extend(new_sentences)

    # Add new tokens to registered_tokens
    for _, _, tokens, _ in new_sentences:
        registered_tokens.update(tokens)

    # Save to file
    save_ranked_sentences()

    # Return whether we found new sentences
    return len(new_sentences) > 0


if __name__ == '__main__':
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY')
    grammar_root   = f"{workspace_root}/resources/processed/ai-cleaned-merge-grammars"

    # Load existing ranked sentences
    load_ranked_sentences()

    display.start()
    try:
        rank_tokens_by_frequency()

        # Iterate until no new sentences are found
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"Iteration {iteration}")
            print(f"{'='*60}")

            found_new = rank_sentences()

            # Print the new sentences added in this iteration
            print(f"\nNew sentences added: {len(new_sentences)}")
            for cost, sentence, tokens, english in new_sentences:
                print(f"  [{cost:.0f}] {sentence}")
                print(f"    English: {english}")
                print(f"    Tokens: {tokens}")

            # Print summary
            print(f"\nTotal ranked sentences: {len(ranked_sentences)}")
            print(f"Total registered tokens: {len(registered_tokens)}")

            if not found_new:
                print(f"\nNo new sentences found. Stopping.")
                break

    finally:
        display.stop()


    # Print top 50 tokens by frequency
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print("\nTop 50 tokens by frequency and rank:")
    for token, count in sorted_tokens[:50]:
        rank = tokens_ranked[token]
        print(f"{token}: {count} (rank {rank})")

    print(f"\nTotal iterations: {iteration}")
    print(f"Total ranked sentences: {len(ranked_sentences)}")
    print(f"Total registered tokens: {len(registered_tokens)}")