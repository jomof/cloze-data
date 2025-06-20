import copy
import hashlib
import os
import re
from collections import OrderedDict
from typing import Optional

from jsonschema import Draft7Validator

from .grammar_schema import GRAMMAR_SCHEMA
from python.mecab.compact_sentence import japanese_to_japanese_with_spaces
from python.utils.visit_json.visit_json import visit_json

QUOTE_PAIRS = [
    ('"', '"'),
    ("'", "'"),
    ("「", "」"),
    ("『", "』"),
    ('“', '”'),
    ('‘', '’'),
]

BRACKET_PATTERNS = [
    ('(', ')'),
    ('[', ']'),
    ('{', '}'),
    ('<', '>'),
]

def strip_matching_quotes(text, _ = None):
    """Remove matching quotes from the beginning and end of a string, including English and Japanese quotes."""
    if not isinstance(text, str) or len(text) < 2:
        return text

    stripped = text
    changed = True
    while changed and len(stripped) >= 2:
        changed = False
        for left, right in QUOTE_PAIRS:
            if stripped.startswith(left) and stripped.endswith(right):
                stripped = stripped[1:-1]
                changed = True
                break
    return stripped

def false_friends_unknown_grammar_type_to_suggest(val, type, all_grammars_summary):
    if type != "grammarType": return val
    if val and val.startswith("<strongly-suggest>:"): return
    with_no_suggest = val.strip().removeprefix("<suggest>:").strip()
    with_no_strongly_suggest = with_no_suggest.removeprefix("<strongly-suggest>:").strip()
    if with_no_suggest in all_grammars_summary['all-grammar-points'].keys():
        # Strip <suggest>: if it is in the dictionary
        return with_no_suggest 
    if with_no_strongly_suggest in all_grammars_summary['all-grammar-points'].keys():
        # Strip <strongly-suggest>: if it is in the dictionary
        return with_no_strongly_suggest 
    else:
        if val.startswith("<strongly-suggest>:"):
            return f"<strongly-suggest>:{with_no_strongly_suggest}"  
        else:
            # Prepend <suggest>: if it is in the dictionary
            return f"<suggest>:{with_no_suggest}" # Otherwise, prepend <suggest>:

def lv_quotes(val, type, path, messages):
    """
    Walks over the given data object and checks each example's English text for quotes.
    Returns a list of lint-style messages indicating which examples contain quotes.
    """
    if type != "exampleEnglish":
        return
    # Don't check for single quotes, because they are common in English contractions
    if '"' in val:
        messages.append(f"[rule-1] warning {path} has quotes and probably should not: {val}")


def lv_english_brackets(val, type, path, messages):
    """
    Walks over the given data object and checks each example's English text for bracket characters: {}, (), [], or <>.
    Returns a list of lint-style messages indicating which examples contain brackets.
    """
    if type != "exampleEnglish":
        return
    for left, right in BRACKET_PATTERNS:
        if left in val or right in val:
            messages.append(f"[rule-4] warning {path} has bracket characters {left}{right}: {val}")
            break

def lv_japanese_braces(val, type, path, messages):
    """
    Walks over the given data object and checks that each Japanese example string contains both '{' and '}'.
    Returns a list of lint-style messages indicating missing braces for bolding the grammar point.
    """
    if type != "japaneseVariationType":
        return

    # if '{' not in val or '}' not in val:
    #     messages.append(f"[rule-5] warning {path} missing {{bold}} grammar point: {val}")

def lv_missing_competing_grammar(val, type, path, messages):
    """
    For every example in grammar_point["examples"], warn if competing_grammar is
    missing or empty. Returns a list of lint‐style messages:
        "[rule-4] warning examples[i] has no competing_grammar"
    """
    if type != "examples/object":
        return

    cg = val.get("competing_grammar")
    if cg is None or (isinstance(cg, list) and len(cg) == 0):
        messages.append(
            f"[rule-4] warning {path} has no competing_grammar"
        )

def lv_example_count(val, type, path, messages):
    """
    Warn if there are fewer than 10 examples.
    Returns a list containing one warning string when len(examples) < 10.
    """
    if type != "examples/array":
        return
    count = len(val)
    if count < 10:
        messages.append(f"[rule-6] at {path} there are only {count} example(s); should have at least 10")

def lv_competing_grammar_count(val, type, path, messages):
    if type != "examples/competing_grammar/object":
        return
    competing_japanese = val.get("competing_japanese", [])
    count = len(competing_japanese)
    if count < 1:
        messages.append(f"warning at {path} there are only {count} ways of saying english in japanese; should have at least 2")

def lv_japanese_count(val, type, path, messages):
    """
    Walks over each example and warns if there are fewer than 2 'japanese' entries.
    """
    if type != "examples/object":
        return
    jap_list = val.get("japanese", [])
    # If it's not a list or has fewer than 2 items, warn
    if not isinstance(jap_list, list) or len(jap_list) < 2:
        count = len(jap_list) if isinstance(jap_list, list) else 0
        messages.append(
            f"[rule-7] warning {path} only has {count} element(s); should be every way of saying 'english' that adheres to the grammar point"
        )

def lv_better_grammar_name(val, type, path, messages):
    """
    [rule-8] Warn if:
      - grammar_point has no valid “(meaning)” section according to get_meaning(...), or
      - better_grammar_point_name is missing or none of its entries yield a non-None from get_meaning(...).
    """
    if type:
        # None for the root object
        return
    gp_name = val.get("grammar_point", "")
    better_grammar_point_name = val.get("better_grammar_point_name", [])
    if len(better_grammar_point_name) == 1:
        if better_grammar_point_name[0] == gp_name:
            messages.append(f"[rule-14] warning better_grammar_point_name[0] should not be the same as grammar_point: {gp_name}")

    meaning = get_meaning(gp_name)
    if meaning is None:
        found_valid = False
        
        for b in better_grammar_point_name:
            if get_meaning(b) is not None:
                found_valid = found_valid or True

        if not found_valid:
            messages.append(
                f"[rule-8] warning grammar_point '{gp_name}' lacks a valid “(meaning)” section; "
                f"better_grammar_point_name should include a name with parentheses starting with a lowercase English letter or ~"
            )
        
    # if meaning is not None:
    #     if ',' in meaning and not better_grammar_point_name:
    #         messages.append(f"[rule-16] warning 'grammar_point' meaning '({meaning})' contains a comma (,). It should use dot (・) instead. Suggest a new name in better_grammar_point_name.")

def lv_required_fields(val, type, path, messages):
    if type:
        # None for the root object
        return
    if "meaning" not in val:
        messages.append(f"error grammar point is missing required field 'meaning'")
    if "split_predecessor" in val:
        messages.append(f"[rule-18] warning grammar point has split_predecessor field. Use the information in it to help compose this new grammar point, then remove the field.")

def lv_validate_parenthetical_meaning(val, type, path, messages):
    if type != "wellFormedGrammarType":
        return
    if '(' not in val:
        messages.append(f"[rule-8] warning {path} '{val}' lacks a '(meaning)' section")
    invalid_chars = _validate_grammar_point_meaning(val)
    if invalid_chars:
        messages.append(f"[rule-9] warning {path} (meaning) starts with invalid char: {', '.join(invalid_chars)}")

def lv_false_friends_grammar_point(val, type, path, messages, all_grammars_summary):
    if type != "false_friends/object":
        return
    gp = val.get("grammar_point")
    if not isinstance(gp, str) or not gp.strip():
        messages.append(f"[rule-12] warning {path}.grammar_point is missing or empty")
    # elif gp.startswith("<suggest>:"):
    #     messages.append(f"warning {path}.grammar_point '{gp}' is <suggest>: prefixed. Please consider whether an existing grammar point applies (it **MUST** cover 'term'). If not, then change '<suggest>:' to '<strongly-suggest>:'. You **MUST NOT** just remove '<suggest>:', delete the false friend if you can't find an existing grammar point and you can't strongly suggest this one.")

def lv_known_grammar(val, type, path, messages, all_grammars_summary):
    if type != "knownGrammarType":
        return
    if not val in all_grammars_summary['all-grammar-points'].keys():
        if not val.startswith("<suggest>:"):
            messages.append(f"[rule-13] unknown grammar at '{path}': '{val}'. You may suggest new grammar points by adding a false_friend.")

def lv_grammar_point_special_characters(val, type, path, messages):
    if type != "grammarType":
        return
    if not val: return

    special = []
    trimmed = val.removeprefix("<suggest>:")
    for c in '/:':
        if c in trimmed:
            special.append(c)

    if special:
        messages.append(f"[rule-14] warning '{path}': '{trimmed}' contain illegal characters: {', '.join(special)}.")

def lv_check_grammar_matcher(val, type, path, messages):
    """Check grammar against matcher"""
    from python.grammar import compile_matcher
    if type: return
    matcher = val.get('matcher')
    if not matcher: return
    examples = val.get('examples')
    if not examples: return
    matcher_enforce_examples = val.get("matcher_enforce_examples", None)

    matcher = compile_matcher(matcher)
    for example_index, example in enumerate(examples):
        competing_grammars = example.get('competing_grammar')
        if not competing_grammars: continue
        for competing_grammar_index, competing_grammar in enumerate(competing_grammars):
            competing_japaneses = competing_grammar.get('competing_japanese')
            if not competing_japaneses: continue
            for competing_japanese_index, competing_japanese in enumerate(competing_japaneses):
                match = matcher.match_japanese(competing_japanese)
                if not match: continue
                messages.append(f"[rule-17] error at examples[{example_index}].competing_grammar[{competing_grammar_index}].competing_japanese[{competing_japanese_index}]. Competing Japanese '{match}' in '{competing_japanese}' appears to use the main grammar point.")
        if matcher_enforce_examples:
            japaneses = example.get('japanese', [])
            for japanese_index, japanese in enumerate(japaneses):
                match = matcher.match_japanese(japanese)
                if match: continue
                messages.append(f"[rule-18] error at examples[{example_index}].japanese[{japanese_index}]. Japanese '{japanese}' uses a different grammar point. Move this sentence to competing grammar if appropriate, but it can't stay here.")

def _validate_grammar_point_meaning(name: str):
    meaning = get_meaning(name)
    if not meaning:
        return []

    if meaning.startswith("I "):
        return []
    
    if meaning.startswith("~") or meaning.startswith("～"):
        return []
    
    if meaning[0].islower():
        return []

    return [meaning[0]] if meaning else []

def lint_schema_enums_with_jsonschema(instance, schema):
    """
    Validate `instance` against `schema` and return a list of all enum‑violation messages.
    Each message is formatted as:
        "<path> had an invalid enum value: <value>"
    where <path> is dotted/bracket notation into `instance`.
    """
    validator = Draft7Validator(schema)
    errors = []

    for error in validator.iter_errors(instance):
        # Only care about enum violations
        if error.validator == "enum":
            # Build a human‑readable path (e.g. "items[2].status")
            path_parts = []
            for part in error.absolute_path:
                if isinstance(part, int):
                    path_parts[-1] = f"{path_parts[-1]}[{part}]"
                else:
                    path_parts.append(str(part))
            path = ".".join(path_parts) if path_parts else "<root>"

            # The invalid value lives in error.instance
            invalid_value = error.instance
            errors.append(f"{path} had an invalid enum value: {repr(invalid_value)}")

    return errors

def prune_empty(obj):
    """
    Recursively remove any fields (in dicts) or items (in lists) where the value is:
        - empty string ""
        - empty list []
        - empty dict {}
        - None
        - string "null"
    This version mutates `obj` in place and returns it.
    """
    if isinstance(obj, dict):
        # First, recurse into each value
        for key, val in list(obj.items()):
            if isinstance(val, (dict, list)):
                prune_empty(val)
            # Re-fetch the (possibly pruned) value
            new_val = obj.get(key)
            # If it’s now an empty container, or matches one of the "empty" primitives, delete it
            if new_val in ("", None, "null") or (isinstance(new_val, (dict, list)) and not new_val):
                del obj[key]
        return obj

    elif isinstance(obj, list):
        # Iterate backwards so that removing by index doesn’t shift unprocessed items
        for i in range(len(obj) - 1, -1, -1):
            item = obj[i]
            if isinstance(item, (dict, list)):
                prune_empty(item)
                # After recursion, check if the container is now empty
                if not item:
                    del obj[i]
                    continue
            # If it’s a “scalar” empty value, remove it
            if item in ("", None, "null"):
                del obj[i]
        return obj

    else:
        # Non-container primitives are returned unchanged
        return obj



def reorder_keys(obj, schema):
    """
    Return a new dict where keys are ordered according to schema's "properties" order.
    Any keys in obj not found in schema.properties will be appended afterward in original order.
    """
    if not isinstance(obj, dict):
        return obj

    properties = schema.get("properties", OrderedDict())
    new_obj = OrderedDict()

    # First, add keys in schema order
    for key in properties:
        if key in obj:
            value = obj[key]
            # If nested object with its own schema, recurse
            prop_schema = properties[key]
            if isinstance(value, dict) and isinstance(prop_schema, dict):
                new_obj[key] = reorder_keys(value, prop_schema)
            elif isinstance(value, list) and isinstance(prop_schema, dict) and prop_schema.get("type") == "array":
                item_schema = prop_schema.get("items", {})
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        new_list.append(reorder_keys(item, item_schema))
                    else:
                        new_list.append(item)
                new_obj[key] = new_list
            else:
                new_obj[key] = value

    # Then, append any remaining keys in original order
    for key, value in obj.items():
        if key not in new_obj:
            new_obj[key] = value

    return new_obj


def japanese_with_space(japanese):
    return japanese_to_japanese_with_spaces(japanese)


def replace_japanese_characters(japanese):

    replacements = {
        '：': [':'], 
        '「': ['『'],
        '」': ['』'],
    }
    for invalids, valids in replacements.items():
        for invalid in invalids:
            for valid in valids:
                japanese = japanese.replace(invalid, valid)
    return japanese


def get_meaning(name: str) -> Optional[str]:
    """
    Extract the content of the last parenthesized group in `name`, 
    but only if it is preceded by a space. Return that content 
    if its first character is '~' or a lowercase English letter [a-z]; 
    otherwise return None.
    """
    # Find all occurrences of " (…)" (i.e., space before the paren)
    matches = re.findall(r' \(([^)]*)\)', name)
    if not matches:
        return None

    # Take the last parenthesized group
    inside = matches[-1].strip()
    if not inside:
        return None

    return inside

path = os.path.abspath(__file__)
with open(path, "rb") as f:
    seed = hashlib.sha256(f.read()).hexdigest()

def clean_lint_memoize(grammar_point, path: str = None, all_grammars_summary: dict = { "all-grammar-points": {"known":{}} }):
    # return memoize_to_disk_seeded("clean_lint", seed, clean_lint, grammar_point, path, all_grammars_summary)
    return clean_lint(grammar_point, path, all_grammars_summary)
    
def clean_lint(grammar_point, path: str = None, all_grammars_summary: dict = { "all-grammar-points": {"known":{}} }):
    lint = []
    if not grammar_point:
        grammar_point = {}
    grammar_point = copy.deepcopy(grammar_point)
    if path is not None:
        filename = os.path.basename(path)
        basename = os.path.splitext(filename)[0]
        try:
            id, name = basename.split("-", 1)
        except Exception:
            print(f"Error splitting {basename} into id and name")
            raise
        grammar_point['id'] = id
        grammar_point['grammar_point'] = name

    if 'lint-errors' in grammar_point:
        del grammar_point['lint-errors']

    # Ensure japanese fields are lists
    for example in grammar_point.get('examples', []):
        japanese_val = example.get('japanese')
        if isinstance(japanese_val, str):
            example['japanese'] = [japanese_val]
        for c in example.get('competing_grammar', []):
            comp_j = c.get('competing_japanese')
            if isinstance(comp_j, str):
                c['competing_japanese'] = [comp_j]
            
    def fn(value, type_name, path):
        # print(f"fn: {type_name=}, {path=}")
        result = value.strip() if isinstance(value, str) else value
        try:
            result = false_friends_unknown_grammar_type_to_suggest(result, type_name, all_grammars_summary)

            if type_name == "grammarType":
                result = strip_matching_quotes(result)

            if type_name == None:
                grammar_point = value
                if 'better_grammar_point_name' in grammar_point:
                    better_grammar_point_names = value['better_grammar_point_name']
                    new_better_names = []
                    for better_name in better_grammar_point_names:
                        if better_name not in all_grammars_summary['all-grammar-points'].keys():
                            new_better_names.append(better_name)
                    if new_better_names:
                        grammar_point['better_grammar_point_name'] = new_better_names
                    else: 
                        del grammar_point['better_grammar_point_name']
                
                # Clean and sort learn_before array
                for field_name in ['learn_before']:
                    if field_name in grammar_point:
                        field_value = grammar_point[field_name]
                        if isinstance(field_value, list):
                            # Remove duplicates and sort
                            cleaned = sorted(list(set(field_value)))
                            grammar_point[field_name] = cleaned

            if type_name == "japanese":
                result = strip_matching_quotes(value)
                result = replace_japanese_characters(result)
                result = japanese_with_space(result)
                return result
            if type_name == "exampleEnglish":
                result = strip_matching_quotes(value)
                return result

            if result == value:
                return None
            else:
                return result
        finally:
            lv_required_fields(result, type_name, path, lint)
            lv_quotes(result, type_name, path, lint)
            lv_english_brackets(result, type_name, path, lint)
            lv_japanese_braces(result, type_name, path, lint)
            lv_missing_competing_grammar(result, type_name, path, lint)
            lv_example_count(result, type_name, path, lint)
            lv_competing_grammar_count(result, type_name, path, lint)
            lv_japanese_count(result, type_name, path, lint)
            lv_better_grammar_name(result, type_name, path, lint)
            lv_validate_parenthetical_meaning(result, type_name, path, lint)
            lv_false_friends_grammar_point(result, type_name, path, lint, all_grammars_summary)
            lv_known_grammar(result, type_name, path, lint, all_grammars_summary)
            lv_grammar_point_special_characters(result, type_name, path, lint)
            lv_check_grammar_matcher(result, type_name, path, lint)
    visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

    lint.extend(lint_schema_enums_with_jsonschema(grammar_point, GRAMMAR_SCHEMA))
    
    grammar_point['lint-errors'] = lint
    # Prune empty fields and items
    prune_empty(grammar_point)
    # Reorder fields to match schema
    grammar_point = reorder_keys(grammar_point, GRAMMAR_SCHEMA)
    return grammar_point
