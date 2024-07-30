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
- Don't change the content of "grammar_point" field.
- Add a "parameters" field that is a list of the parameters to the grammar point (like X, Y, etc).
- If possible, add a "literally" field that describes, in English, the literal meaning of the grammar point. This is to help the user understand the grammar point better. 
- "writeup:" should be factually correct and well-formatted. Keep in mind that any formatting needs to follow json escaping rules.
- "writeup:" text that quotes things, should use double-quotes (") rather than single-quotes (') or double single-quotes('').
   - For example, "This is a quote." is correct, but 'This is a quote.' or ''This is a quote.'' are not.
- Rewrite "writeup:" so the content is different without losing important details. If this grammar point takes parameters from other parts of the sentence, then name those parameters X, Y, etc.
  For example, "just because (X), it doesn't mean that (Y)".
- In "examples:" if the japanese sentence has japanese-style quotes (like「 and 」), then the English sentence should have double quotes (like ").
  If you see some questionable speech or potential hate speech, please rewrite the sentence so that it is grammatically equivalent.
  Add to each a "parameters" list that describes the value of X, Y, etc. for that example.
- English contractions should have a single tick (like '), not double ticks (like '').
- Japanese in "examples" should sound smooth and natural to a native Japanese speaker. The english should be a natural translation.
- Add additional "examples" if some are needed to fully explore all of the nuances of the grammar point.
- If there are proper person names in the examples, then replace them with other person names. Be sure to respect gender with the names.
- Use '\\n' rather than <br/> for line breaks.
- If there are synonyms, then add a "nuance" field that describes conditions of when this synonym is used instead of the main grammar point.
  Be abstract and terse. Nuance for each of the synonyms should be orthogonal to the others.
  Also add a top-level "nuance", that describes the nuance of this grammar point compared with synonyms.
  Don't add nuance to antonyms.
- If there are parameters like X, Y, etc. Then use them all in the "nuance" and "literally" fields. You must use *all* of the parameters in each nuance and literally field.
- Top level "nuance" should go after the "literally" field.
- You may correct "details", but don't add new details.
"""

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    example_model = GenerativeModel(
        MODEL_ID,
        system_instruction=[
            "You are an experienced Japanese language teacher and you are writing a book or database that summarizes and teaches Japanese grammar points. The emphasis should be on the reader learning how to produce the natural grammar when speaking (as opposed to academic concerns).",
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
    for _ in range(10):
        try:
            response = example_model.generate_content(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            if response and response.text:
                break
        except Exception as e:
            print(f"PROBLEM WITH RESPONSE: {e} ")
            time.sleep(15)

    try:
        readback = json.loads(response.text)
        return yaml.dump(readback, sort_keys=False, default_flow_style=False, allow_unicode=True, indent=4, width = 150)
    except Exception as e:
        print(f"PROBLEM WITH RESPONSE: {e} ")
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
