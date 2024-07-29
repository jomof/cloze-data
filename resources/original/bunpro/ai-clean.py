#!/usr/bin/env python3
import sys
import time
import yaml
import json
from google.cloud.logging.handlers import CloudLoggingHandler

import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
)


PROJECT_ID = "jomof-sandbox"  # @param {type:"string"}
LOCATION = "us-west1"  # @param {type:"string"}
MODEL_ID = "gemini-1.5-pro-001"  # @param {type:"string"}

def ai_clean(data, file):
    data = json.dumps(yaml.safe_load(data), indent=2, ensure_ascii=False)
    prompt = f"""
Here is a Japanese grammar point encoded between BEGIN_GRAMMAR_POINT_JSON/BEGIN_GRAMMAR_POINT_JSON.
BEGIN_GRAMMAR_POINT_JSON
{data}
BEGIN_GRAMMAR_POINT_JSON

Please clean it up and give me just the the json content as an answer. Don't wrap in ```json``` or anything like that.
- "writeup:" should be factually correct and well-formatted. Keep in mind that any formatting needs to follow json escaping rules.
- "writeup:" text that quotes things, should use double-quotes (") rather than single-quotes (') or double single-quotes('').
   - For example, "This is a quote." is correct, but 'This is a quote.' or ''This is a quote.'' are not.
- In "examples:" if the japanese sentence has japanese-style quotes (like「 and 」), then the English sentence should have double quotes (like ").
  If you see some questionable speech or potential hate speech, please rewrite the sentence so that it is grammatically equivalent.
- English contractions should have a single tick (like '), not double ticks (like '').
- Use '\\n' rather than <br/> for line breaks.
- If there are synonyms, then add a "nuance" field that describes how and when this synonym is used instead of the main grammar point.
  Be abstract and terse. Nuance for each of the synonyms should be orthogonal to the others.
  Don't use the phrase 'This synonym'. Instead, refer to the point by name. Be sure to punctuate correctly.
  Don't add nuance to antonyms.
"""

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    example_model = GenerativeModel(
        MODEL_ID,
        system_instruction=[
            "You are an experienced Japanese language teacher and you are writing a book or database that summarizes and teaches Japanese grammar points.",
        ],
    )
    # Set model parameters
    generation_config = GenerationConfig(
        temperature=0.9,
        top_p=1.0,
        top_k=32,
        candidate_count=1,
        max_output_tokens=8192,
    )

    # Set safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    # Set contents to send to the model
    contents = [prompt]

    # Prompt the model to generate content
    for _ in range(2):
        try:
            response = example_model.generate_content(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            if response.text:
                break
        except:
            time.sleep(15)

    try:
        readback = json.loads(response.text)
        return yaml.dump(readback, sort_keys=False, default_flow_style=False, allow_unicode=True, indent=4, width = 150)
    except Exception as e:
        print(f"PROBLEM WITH RESPONSE: {output_file} ")
        return f"{e}\n{response.text}"



def main(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = file.read()

        result = ai_clean(data, output_file)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(result)
        
    except Exception as e:
        print(f"Error processing file {input_file}: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        main(input_file, output_file)
