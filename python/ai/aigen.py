import logging
import time
import json5
import jsonref
import jsonschema
import json
from google.genai import types
from google import genai
import python.gcp

# Set of JSON Schema keywords to identify actual schema nodes
SCHEMA_KEYWORDS = {
    "properties", "items", "required", "additionalProperties",
    "patternProperties", "allOf", "anyOf", "oneOf", "not",
    "enum", "minimum", "maximum", "minLength", "maxLength",
    "pattern", "format", "const", "$ref"
}

# Attempt to use color logging if available
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler with optional color (only WARN+ level shown in console)
if COLORLOG_AVAILABLE:
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s"
    ))
else:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    ))
# Only show warnings and above in console to reduce Bazel log verbosity
console_handler.setLevel(logging.WARNING)
logger.addHandler(console_handler)

# File handler will include INFO+ logs if log_file provided later

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


def aigen(
    prompt: str,
    model: str,
    schema: str,  # JSON5-formatted schema string
    log_file: str,
    retries: int = 10,
    backoff_seconds: int = 60,
) -> str:
    """
    Generate AI content using specified Gemini 2.5 model with retry logic.

    Args:
        prompt: Input text prompt
        model: Gemini 2.5 model identifier
        schema: JSON5-formatted schema string
        log_file: Path to a log file
        retries: Maximum retry attempts
        backoff_seconds: Delay between retries

    Returns:
        Generated text content
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

    file_handler = None
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(file_handler)

    try:
        for attempt in range(retries):
            # Log attempts at info level
            logger.info(f"Attempt {attempt+1}/{retries} with model {model}")
            # Log the prettified schema being sent to GenAI at info level
            prettified = json.dumps(parsed_schema, indent=2, ensure_ascii=False)
            logger.info("Sending schema to GenAI:\n%s", prettified)
            if not model.startswith("gemini-2.5"):
                raise ValueError(f"Unsupported model: {model}")
            return generate_and_validate(model, prompt, parsed_schema)
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            logger.warning(f"Resource exhausted: retrying in {backoff_seconds}s")
            time.sleep(backoff_seconds)
        else:
            logger.error(f"Generation failed: {e}")
            raise
    finally:
        if file_handler:
            logger.removeHandler(file_handler)

    raise Exception("Failed after retries")


def generate_and_validate(
    model_name: str,
    prompt: str,
    schema: dict,
) -> str:
    """
    Generate content and ensure it matches the provided JSON Schema.
    """
    client = genai.Client(
        vertexai=True,
        project=python.gcp.PROJECT_ID,
        location=python.gcp.LOCATION
    )

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        response_modalities=["TEXT"],
        responseMimeType="application/json",
        response_schema=schema,
        max_output_tokens=65536,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=model_name,
        contents=contents,
        config=config,
    ):
        if chunk.text:
            result += chunk.text

    cleaned = result.removeprefix("```json").removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")

    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        msgs = "; ".join(e.message for e in errors)
        raise ValueError(f"Response does not comply with schema: {msgs}")

    return cleaned
