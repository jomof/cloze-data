import json5
import pkgutil

_grammar_schema = None

def grammar_schema():
    global _grammar_schema
    if _grammar_schema is None:
        # Retrieve the JSON schema as bytes
        content_bytes = pkgutil.get_data(__name__, "grammar-schema.json")
        if content_bytes is None:
            raise FileNotFoundError("grammar-schema.json not found in package")

        # Decode bytes to a string
        content_str = content_bytes.decode("utf-8")

        # Parse the JSON5 content into a Python object
        parsed_schema = json5.loads(content_str)

        # Store both the raw string and the parsed object
        _grammar_schema = (content_str, parsed_schema)
    return _grammar_schema

# Usage
# GRAMMAR_SCHEMA_WITH_COMMENTS will be a string containing the JSON with comments
# GRAMMAR_SCHEMA will be the parsed JSON object (dict)
GRAMMAR_SCHEMA_WITH_COMMENTS, GRAMMAR_SCHEMA = grammar_schema()
