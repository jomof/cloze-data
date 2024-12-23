import os
from google.genai import types
from google import genai

import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "jomof-sandbox"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}

def aigen(prompt, model):
    if model == "gemini-2.0-flash-thinking-exp-1219": return generate_gemini_2_0(prompt)
    if model == "gemini-1.5-flash-002": return generate_gemini_1_5(prompt)
    raise ValueError(f"Unknown model: {model}")

def generate_gemini_2_0(prompt):
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

    # model = "gemini-2.0-flash-exp"
    model = "gemini-2.0-flash-thinking-exp-1219"
    contents = [
        types.Content(
        role="user",
        parts=[
            types.Part.from_text(prompt)
        ]
        )
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature = 1,
        top_p = 0.95,
        max_output_tokens = 8192,
        response_modalities = ["TEXT"],
        safety_settings = [types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="OFF"
        ),types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="OFF"
        ),types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="OFF"
        ),types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="OFF"
        )],
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model = model,
        contents = contents,
        config = generate_content_config,
        ):
       # print(chunk.text)
        if chunk.text is not None:
            result += chunk.text
    return result.removeprefix("```json").removesuffix("\n").removesuffix("```")


def generate_gemini_1_5(prompt):
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(
        "gemini-1.5-flash-002",
    )
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    safety_settings = [
        # SafetySetting(
        #     category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        #     threshold=SafetySetting.HarmBlockThreshold.OFF
        # ),
        # SafetySetting(
        #     category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        #     threshold=SafetySetting.HarmBlockThreshold.OFF
        # ),
        # SafetySetting(
        #     category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        #     threshold=SafetySetting.HarmBlockThreshold.OFF
        # ),
        # SafetySetting(
        #     category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        #     threshold=SafetySetting.HarmBlockThreshold.OFF
        # ),
    ]

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
    
