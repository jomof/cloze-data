import logging
from google.genai import types
from google import genai
import time
from python.gcp import PROJECT_ID, LOCATION
import vertexai
from vertexai.generative_models import GenerativeModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def aigen(prompt: str, model: str, retries: int = 10, backoff_seconds: int = 60) -> str:
    """
    Generate AI content using specified model with retry logic.
    
    Args:
        prompt: Input text prompt
        model: Model identifier string
        retries: Maximum number of retry attempts
        backoff_seconds: Seconds to wait between retries
    
    Returns:
        Generated text content
    
    Raises:
        ValueError: If model is not recognized
        Exception: If generation fails after all retries
    """
    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{retries} generating content with model {model}")
            if model == "gemini-2.5-flash-preview-05-20":
                return generate_gemini_2_0(model, prompt)
            if model == "gemini-2.5-pro-preview-05-06":
                return generate_gemini_2_0(model, prompt)
            if model == "gemini-2.0-flash-001":
                return generate_gemini_2_0(model, prompt)
            if model == "gemini-2.0-flash-thinking-exp-1219":
                return generate_gemini_2_0(model, prompt)
            if model == "gemini-1.5-flash-002":
                return generate_gemini_1_5(model, prompt)
            
            raise ValueError(f"Unknown model: '{model}'")
            
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in f"{e}":
                logger.warning(f"Resource exhausted, sleeping for {backoff_seconds}s before retry")
                time.sleep(backoff_seconds)
            else:
                logger.error(f"Generation failed with error: {e}")
                raise e

    raise Exception(f"Failed to generate content after {retries} retries")

def generate_gemini_2_0(model_name: str, prompt: str) -> str:
    """
    Generate content using Gemini 2.0 model.
    
    Args:
        model_name: Gemini 2.0 model identifier
        prompt: Input text prompt
    
    Returns:
        Generated text content
    """
    logger.info("Initializing Gemini 2.0 client")
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

    # Configure content generation settings
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(prompt)]
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        #max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="OFF"
            )
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

def generate_gemini_1_5(model_name: str, prompt: str) -> str:
    """
    Generate content using Gemini 1.5 model.
    
    Args:
        model_name: Gemini 1.5 model identifier
        prompt: Input text prompt
    
    Returns:
        Generated text content
    """
    logger.info("Initializing Vertex AI with Gemini 1.5")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(model_name)
    
    # Configure generation parameters
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    safety_settings = []  # Safety settings commented out in original code

    # Stream and accumulate generated content
    logger.info("Starting content generation stream")
    responses = model.generate_content(
        [prompt],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    result = ""
    for response in responses:
        result += response.text
    return result