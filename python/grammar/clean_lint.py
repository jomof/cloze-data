import copy
from collections import OrderedDict
from jsonschema import Draft7Validator
from .grammar_schema import GRAMMAR_SCHEMA
import os
from python.mecab.compact_sentence import japanese_to_japanese_with_spaces
import re
from typing import Optional

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

def strip_matching_quotes(text, _):
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


def lint_quotes(grammar_point):
    """
    Walks over the given data object and checks each example's English text for quotes.
    Returns a list of lint-style messages indicating which examples contain quotes.
    """
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        english = example.get("english", "")
        # Don't check for single quotes, because they are common in English contractions
        if '"' in english:
            messages.append(f"[rule-1] warning examples[{idx}].english has quotes and probably should not: {english}")
    return messages


def lint_english_brackets(grammar_point):
    """
    Walks over the given data object and checks each example's English text for bracket characters: {}, (), [], or <>.
    Returns a list of lint-style messages indicating which examples contain brackets.
    """
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        english = example.get("english", "")
        for left, right in BRACKET_PATTERNS:
            if left in english or right in english:
                messages.append(f"[rule-4] warning examples[{idx}].english has bracket characters {left}{right}: {english}")
                break
    return messages


def lint_japanese_braces(grammar_point):
    """
    Walks over the given data object and checks that each Japanese example string contains both '{' and '}'.
    Returns a list of lint-style messages indicating missing braces for bolding the grammar point.
    """
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        jap_list = example.get("japanese", [])
        # Only proceed if japanese field is a list
        if isinstance(jap_list, list):
            for j_idx, jap in enumerate(jap_list):
                if not isinstance(jap, str):
                    continue
                if '{' not in jap or '}' not in jap:
                    messages.append(f"[rule-5] warning examples[{idx}].japanese[{j_idx}] missing {{bold}} grammar point': {jap}")
    return messages


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


def type_replace(obj, schema, type_name, fn):
    new_obj = copy.deepcopy(obj)
    ref_pointer = f"#/definitions/{type_name}"

    def resolve_ref(ref):
        if not ref.startswith("#/definitions/"):
            return None
        key = ref.split("/")[-1]
        return schema["definitions"].get(key)

    def _traverse(current_obj, current_schema, path):
        # If schema is not a dict, nothing to do
        if not isinstance(current_schema, dict):
            return current_obj

        # Handle $ref nodes
        if "$ref" in current_schema:
            if current_schema["$ref"] == ref_pointer:
                # Found a match—call fn with (value, path)
                return fn(current_obj, path)
            resolved = resolve_ref(current_schema["$ref"])
            if resolved:
                return _traverse(current_obj, resolved, path)

        schema_type = current_schema.get("type")

        # Object: recurse into each property
        if schema_type == "object":
            props = current_schema.get("properties", {})
            if isinstance(current_obj, dict):
                for key, prop_schema in props.items():
                    if key in current_obj:
                        # Build new path: "parent.child" or just "child" at root
                        new_path = f"{path}.{key}" if path else key
                        current_obj[key] = _traverse(current_obj[key], prop_schema, new_path)
            return current_obj

        # Array: recurse into each element
        if schema_type == "array":
            items_schema = current_schema.get("items")
            if isinstance(current_obj, list) and items_schema:
                new_list = []
                for i, item in enumerate(current_obj):
                    # Build new path: "parent[index]" or "[index]" at root
                    new_path = f"{path}[{i}]" if path else f"[{i}]"
                    new_list.append(_traverse(item, items_schema, new_path))
                return new_list
            return current_obj

        # Anything else: leave as-is
        return current_obj

    return _traverse(new_obj, schema, "")


def prune_empty(obj):
    """
    Recursively remove any fields (in dicts) or items (in lists) where the value is:
        - empty string ""
        - empty list []
        - empty dict {}
        - None
        - string "null"
    Returns a new structure with those fields/items removed.
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            pruned_v = prune_empty(v)
            if pruned_v in ("", [], {}, None, "null"):
                continue
            new_dict[k] = pruned_v
        return new_dict

    if isinstance(obj, list):
        pruned_list = []
        for item in obj:
            pruned_item = prune_empty(item)
            if pruned_item in ("", [], {}, None, "null"):
                continue
            pruned_list.append(pruned_item)
        return pruned_list

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


def japanese_with_space(japanese, _):
    return japanese_to_japanese_with_spaces(japanese)


def replace_japanese_characters(japanese, _):

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


def lint_missing_competing_grammar(grammar_point):
    """
    For every example in grammar_point["examples"], warn if competing_grammar is
    missing or empty. Returns a list of lint‐style messages:
        "[rule-X] warning examples[i] has no competing_grammar"
    """
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        # If there's no competing_grammar key, or it's an empty list, warn.
        cg = example.get("competing_grammar")
        if cg is None or (isinstance(cg, list) and len(cg) == 0):
            messages.append(
                f"[rule-4] warning examples[{idx}] has no competing_grammar"
            )
    return messages

def lint_example_count(grammar_point):
    """
    Warn if there are fewer than 10 examples.
    Returns a list containing one warning string when len(examples) < 10.
    """
    messages = []
    examples = grammar_point.get("examples", [])
    count = len(examples)
    if count < 10:
        messages.append(f"[rule-6] only {count} example(s); should have at least 10")
    return messages

def lint_japanese_count(grammar_point):
    """
    Walks over each example and warns if there are fewer than 2 'japanese' entries.
    """
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        jap_list = example.get("japanese", [])
        # If it's not a list or has fewer than 2 items, warn
        if not isinstance(jap_list, list) or len(jap_list) < 2:
            count = len(jap_list) if isinstance(jap_list, list) else 0
            messages.append(
                f"[rule-7] warning examples[{idx}].japanese only has {count} element(s); should should be every way of saying 'english' that adheres to the grammar point"
            )
    return messages

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

    first_char = inside[0]
    if first_char == "I" or first_char == '~' or ('a' <= first_char <= 'z'):
        return inside

    return None


def lint_better_grammar_name(grammar_point):
    """
    [rule-8] Warn if:
      - grammar_point has no valid “(meaning)” section according to get_meaning(...), or
      - better_grammar_point_name is missing or none of its entries yield a non-None from get_meaning(...).
    """
    messages = []
    gp_name = grammar_point.get("grammar_point", "")
    if get_meaning(gp_name) is None:
        found_valid = False
        for b in grammar_point.get("better_grammar_point_name", []):
            if get_meaning(b) is not None:
                found_valid = True
                break
        if not found_valid:
            messages.append(
                f"[rule-8] warning grammar_point '{gp_name}' lacks a valid “(meaning)” section; "
                f"better_grammar_point_name should include a name with parentheses starting with a lowercase English letter or ~"
            )
    return messages


def _check_paren_lowercase(name: str, field_label: str):
    """
    [rule-9] If get_meaning(name) returns a non-None string,
    ensure that inside that meaning, all ASCII letters remain lowercase,
    except 'I ' where applicable. Returns a warning listing uppercase letters found.
    """
    messages = []
    meaning = get_meaning(name)
    if not meaning:
        return messages

    uppercase_chars = []
    for i, c in enumerate(meaning):
        if c.isascii() and c.isalpha() and c == c.upper():
            # Allow 'I' only if followed by a space
            if c == "I" and i + 1 < len(meaning) and meaning[i + 1] == " ":
                continue
            uppercase_chars.append(c)

    if uppercase_chars:
        unique = sorted(set(uppercase_chars))
        chars_str = ", ".join(unique)
        messages.append(
            f"[rule-9] warning {field_label} '{name}' has uppercase letters inside parentheses ({chars_str}); "
            f"text inside parentheses must be all lowercase (except 'I ')"
        )
    return messages


def lint_parentheses_lowercase(grammar_point):
    """
    Apply the “all lowercase inside (meaning)” check on:
      1. grammar_point
      2. each entry in better_grammar_point_name (if present)
    Only runs when get_meaning(...) is non-None.
    """
    messages = []
    gp_name = grammar_point.get("grammar_point", "")
    messages.extend(_check_paren_lowercase(gp_name, "grammar_point"))

    for bn in grammar_point.get("better_grammar_point_name", []):
        messages.extend(_check_paren_lowercase(bn, "better_grammar_point_name"))

    return messages

def lint_learn_before(grammar_point):
    """
    [rule-10] Warn if:
      - learn_before is missing, or
      - learn_before is not a list with at least two items.
    """
    messages = []
    lb = grammar_point.get("learn_before")
    if not isinstance(lb, list) or len(lb) < 2:
        count = len(lb) if isinstance(lb, list) else 0
        messages.append(
            f"[rule-10] warning learn_before has {count} item(s); must have at least 2"
        )
    return messages


def lint_learn_after(grammar_point):
    """
    [rule-11] Warn if:
      - learn_after is missing, or
      - learn_after is not a list with at least two items.
    """
    messages = []
    la = grammar_point.get("learn_after")
    if not isinstance(la, list) or len(la) < 2:
        count = len(la) if isinstance(la, list) else 0
        messages.append(
            f"[rule-11] warning learn_after has {count} item(s); must have at least 2"
        )
    return messages

def lint_false_friends_grammar_point(grammar_point):
    """
    [rule-12] Warn if any entry in false_friends is missing the 'grammar_point' field
    or if it’s not a non-empty string.
    """
    messages = []
    ff_list = grammar_point.get("false_friends", [])
    if isinstance(ff_list, list):
        for idx, ff in enumerate(ff_list):
            gp = ff.get("grammar_point")
            if not isinstance(gp, str) or not gp.strip():
                messages.append(
                    f"[rule-12] warning false_friends[{idx}].grammar_point is missing or empty"
                )
    return messages

def lint_known_grammar(grammar_point, all_grammars_summary):
    """
    [rule-13] For every field whose schema type is '#/definitions/knownGrammarType',
    call is_known_grammar(value). If False, append a warning.
    Uses type_replace(...) to traverse all such fields.
    """
    messages = []

    def _check(val, path):
        # `val` is the value of a knownGrammarType field
        if not val in all_grammars_summary['all-grammar-points'].keys():
            # raise ValueError(' '.join(all_grammars_summary['all-grammar-points'].keys()))
            messages.append(f"[rule-13] unknown grammar at '{path}': '{val}'")
        return val

    # Traverse grammar_point with type_replace targeting "knownGrammarType"
    type_replace(grammar_point, GRAMMAR_SCHEMA, "knownGrammarType", _check)

    return messages
def clean_lint(grammar_point, path: str, all_grammars_summary: dict):
    lint = []
    grammar_point = copy.deepcopy(grammar_point)
    if path is not None:
        filename = os.path.basename(path)
        basename = os.path.splitext(filename)[0]
        id, name = basename.split("-", 1)
        grammar_point['id'] = id
        grammar_point['grammar_point'] = name

    if 'lint-errors' in grammar_point:
        del grammar_point['lint-errors']
    if 'change' in grammar_point:
        del grammar_point['change']

    # Ensure japanese fields are lists
    for example in grammar_point.get('examples', []):
        japanese_val = example.get('japanese')
        if isinstance(japanese_val, str):
            example['japanese'] = [japanese_val]
        for c in example.get('competing_grammar', []):
            comp_j = c.get('competing_japanese')
            if isinstance(comp_j, str):
                c['competing_japanese'] = [comp_j]
            
    grammar_point = type_replace(grammar_point, GRAMMAR_SCHEMA, "japanese", strip_matching_quotes)
    grammar_point = type_replace(grammar_point, GRAMMAR_SCHEMA, "japanese", replace_japanese_characters)
    grammar_point = type_replace(grammar_point, GRAMMAR_SCHEMA, "japanese", japanese_with_space)
    grammar_point = type_replace(grammar_point, GRAMMAR_SCHEMA, "exampleEnglish", strip_matching_quotes)
    lint.extend(lint_quotes(grammar_point))
    lint.extend(lint_english_brackets(grammar_point))
    lint.extend(lint_schema_enums_with_jsonschema(grammar_point, GRAMMAR_SCHEMA))
    lint.extend(lint_missing_competing_grammar(grammar_point))
    lint.extend(lint_japanese_braces(grammar_point))
    lint.extend(lint_example_count(grammar_point))
    lint.extend(lint_japanese_count(grammar_point))
    lint.extend(lint_better_grammar_name(grammar_point))
    lint.extend(lint_parentheses_lowercase(grammar_point))
    lint.extend(lint_learn_before(grammar_point))
    lint.extend(lint_learn_after(grammar_point))
    lint.extend(lint_false_friends_grammar_point(grammar_point))
    lint.extend(lint_known_grammar(grammar_point, all_grammars_summary))
    grammar_point['lint-errors'] = lint
    # Prune empty fields and items
    grammar_point = prune_empty(grammar_point)
    # Reorder fields to match schema
    grammar_point = reorder_keys(grammar_point, GRAMMAR_SCHEMA)
    return grammar_point
