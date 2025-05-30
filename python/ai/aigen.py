import logging
import time
from google.genai import types
from google import genai
import python.gcp

# Attempt to use color logging if available
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler with optional color
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
logger.addHandler(console_handler)

def aigen(
    prompt: str,
    model: str,
    log_file: str,
    retries: int = 10,
    backoff_seconds: int = 60,
) -> str:
    """
    Generate AI content using specified Gemini 2.5 model with retry logic.

    Args:
        prompt: Input text prompt
        model: Gemini 2.5 model identifier (e.g., 'gemini-2.5-flash-preview-05-20')
        retries: Maximum number of retry attempts
        backoff_seconds: Seconds to wait between retries
        log_file: Path to a log file. Logs will also be written to this file.

    Returns:
        Generated text content

    Raises:
        ValueError: If model is not a Gemini 2.5 variant
        Exception: If generation fails after all retries
    """
    file_handler = None
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(file_handler)

    try:
        for attempt in range(retries):
            logger.info(f"Attempt {attempt + 1}/{retries} generating content with model {model}")
            if not model.startswith("gemini-2.5"):
                raise ValueError(
                    f"Unsupported model: '{model}'. Only Gemini 2.5 models are supported."
                )
            return generate_gemini_2_5(model, prompt)
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            logger.warning(
                f"Resource exhausted, sleeping for {backoff_seconds}s before retry"
            )
            time.sleep(backoff_seconds)
        else:
            logger.error(f"Generation failed with error: {e}")
            raise
    finally:
        if file_handler:
            logger.removeHandler(file_handler)

    raise Exception(
        f"Failed to generate content after {retries} retries"
    )

def generate_gemini_2_5(model_name: str, prompt: str) -> str:
    """
    Generate content using Gemini 2.5 model.

    Args:
        model_name: Gemini 2.5 model identifier
        prompt: Input text prompt

    Returns:
        Generated text content
    """
    logger.info("Initializing Gemini 2.5 client")
    client = genai.Client(
        vertexai=True,
        project=python.gcp.PROJECT_ID,
        location=python.gcp.LOCATION
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    )

    # Stream and accumulate generated content
    result = ""
    logger.info("Starting content generation stream")
    for chunk in client.models.generate_content_stream(
        model=model_name,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            result += chunk.text

    # Clean up response formatting
    return result.removeprefix("```json").removesuffix("\n").removesuffix("```")
