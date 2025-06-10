import time
import json
from google.genai import types
from google import genai
import python.gcp
from python.ai.util import parse_and_validate_schema


def aigen(
    prompt: str,
    model: str,
    schema: str,  # JSON5-formatted schema string
    log_file: str = None,  # Ignored for backwards compatibility
    retries: int = 10,
    backoff_seconds: int = 60,
) -> str:
    """
    Generate AI content using specified Gemini 2.5 model with retry logic.

    Args:
        prompt: Input text prompt
        model: Gemini 2.5 model identifier
        schema: JSON5-formatted schema string
        log_file: Ignored (kept for backwards compatibility)
        retries: Maximum retry attempts
        backoff_seconds: Delay between retries

    Returns:
        Generated text content
    """
    parsed_schema = parse_and_validate_schema(schema)

    for attempt in range(retries):
        try:
            if not model.startswith("gemini-2.5"):
                raise ValueError(f"Unsupported model: {model}")
            return generate_and_validate(model, prompt, parsed_schema)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                time.sleep(backoff_seconds)
            else:
                if attempt == retries - 1:  # Last attempt
                    raise

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
        import jsonschema
        data = json.loads(cleaned)
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        if errors:
            msgs = "; ".join(e.message for e in errors)
            raise ValueError(f"Response does not comply with schema: {msgs}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")

    return cleaned
