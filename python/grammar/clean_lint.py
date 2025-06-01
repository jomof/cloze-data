import copy
from jsonschema import Draft7Validator

def lint_schema_enums_with_jsonschema(instance, schema):
    """
    Validate `instance` against `schema` and return a list of all enum‐violation messages.
    
    Each message is formatted as:
        "<path> had an invalid enum value: <value>"
    where <path> is dotted/bracket notation into `instance`.
    """
    validator = Draft7Validator(schema)
    errors = []
    
    for error in validator.iter_errors(instance):
        # Only care about enum violations
        if error.validator == "enum":
            # Build a human‐readable path (e.g. "items[2].status")
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

    Args:
        obj (dict or list or primitive): The JSON-like object to process.
        schema (dict): The JSON schema describing the structure of `obj`.
        type_name (str): The name of the definition in the schema (e.g., "japanese").
        fn (callable): A function that takes (value) and returns a replacement value.

    Returns:
        A new object (deep copy of `obj`) with all matching values replaced.
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

QUOTE_PAIRS = [
        ('"', '"'),
        ("'", "'"),
        ('「', '」'),
        ('『', '』'),
        ('“', '”'),
        ('‘', '’'),
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
        # Check for double or single quote characters
        if '"' in english:
            messages.append(f"[rule-1] warning examples[{idx}].english has quotes and probably should not: {english}")
    return messages

def lint_mecab_spaces(grammar_point):
    messages = []
    examples = grammar_point.get("examples", [])
    for idx, example in enumerate(examples):
        japanese = example.get("japanese", "")
        if ' ' not in japanese:
            messages.append(f"[rule-2] warning examples[{idx}].japanese does not have spaces to aid mecab parsing: {japanese}")
    return messages

def clean_lint(grammar_point, schema):
    lint = []
    grammar_point = copy.deepcopy(grammar_point)
    if 'lint-errors' in grammar_point:
        del grammar_point['lint-errors']
    if 'change' in grammar_point:
        del grammar_point['change']
    grammar_point = type_replace(grammar_point, schema, "japanese", strip_matching_quotes)
    grammar_point = type_replace(grammar_point, schema, "english", strip_matching_quotes)
    lint.extend(lint_quotes(grammar_point))
    lint.extend(lint_mecab_spaces(grammar_point))
    lint.extend(lint_schema_enums_with_jsonschema(grammar_point, schema))
    if len(lint) > 0:
        grammar_point['lint-errors'] = lint
    return grammar_point
