import json5
import jsonref
import jsonschema

# Set of JSON Schema keywords to identify actual schema nodes
SCHEMA_KEYWORDS = {
    "properties", "items", "required", "additionalProperties",
    "patternProperties", "allOf", "anyOf", "oneOf", "not",
    "enum", "minimum", "maximum", "minLength", "maxLength",
    "pattern", "format", "const", "$ref"
}


def _strip_proxies(node):
    """
    Recursively convert any proxy or JsonRef types into plain Python types.
    """
    if isinstance(node, dict):
        return {k: _strip_proxies(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_strip_proxies(item) for item in node]
    return node


def validate_schema_types(schema_node):
    """
    Recursively ensure that 'type' keywords in actual schema nodes are valid strings.
    Skips user-defined property mappings that are not true schema definitions.
    Raises ValueError if any 'type' in a schema node is not a string or list-of-strings.
    """
    if isinstance(schema_node, dict):
        keys = set(schema_node.keys())
        if 'type' in keys and keys.intersection(SCHEMA_KEYWORDS):
            t = schema_node['type']
            if not (isinstance(t, str) or (isinstance(t, list) and all(isinstance(x, str) for x in t))):
                raise ValueError(f"Invalid schema 'type': {t}")
        for value in schema_node.values():
            validate_schema_types(value)
    elif isinstance(schema_node, list):
        for item in schema_node:
            validate_schema_types(item)


def parse_and_validate_schema(schema: str) -> dict:
    """
    Parse and validate a JSON5 schema string.
    
    Args:
        schema: JSON5-formatted schema string
        
    Returns:
        Parsed and validated schema dictionary
        
    Raises:
        ValueError: If schema is invalid
    """
    try:
        raw_schema = json5.loads(schema)
        jsonschema.Draft7Validator.check_schema(raw_schema)
        resolved = jsonref.JsonRef.replace_refs(raw_schema)
        parsed_schema = _strip_proxies(resolved)
    except Exception as e:
        raise ValueError(f"Schema setup error: {e}")

    # Remove unsupported GenAI keys
    parsed_schema.pop("$schema", None)
    parsed_schema.pop("definitions", None)

    try:
        validate_schema_types(parsed_schema)
    except ValueError as e:
        raise ValueError(f"Schema type validation error: {e}")
    
    return parsed_schema