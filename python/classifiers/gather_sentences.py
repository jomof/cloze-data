
from python.grammar import compile_matcher
from python.console import display
from typing import List, Dict, Union

# Gather training data consistently
from python.mapreduce import MapReduce
import asyncio
from python.mecab.compact_sentence import japanese_to_compact_sentence
positive_examples = {}
negative_examples = {}
matchers = {}

def accumulate(table: Dict[str, List[str]],
               key: str,
               value: Union[str, List[str]]) -> int:
    """Add value(s) under key, keep things sorted, and return how many NEW items."""
    # Normalize to a set of incoming values
    values = {value} if isinstance(value, str) else set(value)
    if not values:
        return 0

    # Existing entries as a set
    old_set = set(table.get(key, []))
    new_set = old_set.union(values)

    # Store back as a sorted list
    table[key] = sorted(new_set)
    # Return count of genuinely new items
    return len(new_set) - len(old_set)

def map(current, _):
    import re
    grammar_point = current['grammar_point']
    matcher_string = current.get('matcher','')
    if matcher_string:
        matcher = compile_matcher(matcher_string)
    else:
        matcher = None

    
    examples = current.get('examples', [])
    positive = []
    negative = []
    for example in examples:
        japaneses = example.get('japanese', [])
        for japanese in japaneses:
            compact = japanese_to_compact_sentence(japanese.replace('{', '').replace('}', ''))
            positive.append(compact)

            if matcher:
                if not matcher.match_japanese(compact):
                    display.warn(f"GRAMMAR:  {grammar_point}")
                    c = compact.replace('⌈','\u001b[K\n⌈')
                    display.warn(f"COMPACT:  {c}")
                    display.warn(f"JAPANESE: {japanese}")
                    display.warn(f"MATCHER: {matcher.regex_string}")
                    display.warn(f"EXPECTED MATCH")
                    display.error(f"Expected match {matcher}: {japanese}->{compact}")
            
        for competing in example.get("competing_grammar", []):
            for japanese in competing.get("competing_japanese", []):
                compact = japanese_to_compact_sentence(japanese.replace('{', '').replace('}', ''))
                negative.append(compact)
                if matcher:
                    if matcher.match_japanese(compact):
                        display.warn(f"POINT:    {grammar_point}")
                        c = compact.replace('⌈','\u001b[K\n⌈')
                        display.warn(f"COMPACT:  {c}")
                        display.warn(f"JAPANESE: {japanese}")
                        display.warn(f"EXPECTED NO MATCH")
                        display.error(f"Expected no match {matcher}: {japanese}->{compact}")
    return grammar_point, matcher, positive, negative

def fold(_, points):
    grammar_point, matcher, positive, negative = points
    
    if matcher:
        accumulate(matchers, matcher, grammar_point)
    for compact in positive:
        accumulate(positive_examples, compact, grammar_point)
    for compact in negative:
        accumulate(negative_examples, compact, grammar_point)



def gather_training_data(
        grammar_root, 
        matcher_augment=True):
    mr = MapReduce(
        input_dir            = grammar_root,
        map_func_name        = 'building training set',
        map_func             = map,
        fold_func_name       = 'accumulating training set',
        fold_func            = fold,
        max_threads          = 14,
    )

    asyncio.run(mr.run())

    if matcher_augment:
        with display.work("augmenting"):
            # Augment positives with explicit matchers
            added_grammar_points = 0
            sentences_before = len(positive_examples)
            remaining = len(matchers)
            for matcher, points in matchers.items():
                display.update_countdown(remaining)
                remaining -= 1
                for positive in positive_examples:
                    if matcher.match_japanese(positive):
                        added_grammar_points += accumulate(positive_examples, positive, points)
                for negative in negative_examples:
                    if matcher.match_japanese(negative):
                        added_grammar_points += accumulate(positive_examples, negative, points)
                
        display.check(f"Augmented with {len(positive_examples) - sentences_before} additional sentences")
        display.check(f"Augmented with {added_grammar_points} additional grammar points")



    return {
        'positive': positive_examples,
        'negative': negative_examples
    }