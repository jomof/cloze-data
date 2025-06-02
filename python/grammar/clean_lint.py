import copy
from collections import OrderedDict
from jsonschema import Draft7Validator
from .grammar_schema import GRAMMAR_SCHEMA
import os
from python.mecab.compact_sentence import japanese_to_japanese_with_spaces

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

def strip_matching_quotes(text):
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


def lint_mecab_spaces(grammar_point):
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        japaneses = example.get("japanese", [])
        # if isinstance(japaneses, list):
        for jidx, japanese in enumerate(japaneses):
            if ' ' not in japanese and '、' not in japanese:
                messages.append(f"[rule-2] warning examples[{idx}].japanese[{jidx}] does not have spaces to aid mecab parsing: {japanese}")
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
    """
    Traverse the given object `obj` according to the provided JSON `schema`,
    find all instances where the schema references the definition named `type_name`,
    and apply the function `fn` to the corresponding value in `obj`.
    """
    new_obj = copy.deepcopy(obj)
    ref_pointer = f"#/definitions/{type_name}"

    def _traverse(current_obj, current_schema):
        # If this schema node references our target type, apply fn
        if isinstance(current_schema, dict) and current_schema.get("$ref") == ref_pointer:
            return fn(current_obj)

        schema_type = current_schema.get("type")
        if schema_type == "object":
            props = current_schema.get("properties", {})
            for key, prop_schema in props.items():
                if isinstance(current_obj, dict) and key in current_obj:
                    current_obj[key] = _traverse(current_obj[key], prop_schema)
            return current_obj

        if schema_type == "array":
            items_schema = current_schema.get("items")
            if isinstance(current_obj, list) and items_schema:
                return [_traverse(item, items_schema) for item in current_obj]
            return current_obj

        return current_obj

    return _traverse(new_obj, schema)


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

def japanese_with_space(japanese):
    if ' ' in japanese:
        return japanese
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

def clean_lint(grammar_point, path: str = None):
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
    grammar_point = type_replace(grammar_point, GRAMMAR_SCHEMA, "english", strip_matching_quotes)
    lint.extend(lint_quotes(grammar_point))
    lint.extend(lint_english_brackets(grammar_point))
    lint.extend(lint_mecab_spaces(grammar_point))
    lint.extend(lint_schema_enums_with_jsonschema(grammar_point, GRAMMAR_SCHEMA))
    grammar_point['lint-errors'] = lint
    # Prune empty fields and items
    grammar_point = prune_empty(grammar_point)
    # Reorder fields to match schema
    grammar_point = reorder_keys(grammar_point, GRAMMAR_SCHEMA)
    return grammar_point
