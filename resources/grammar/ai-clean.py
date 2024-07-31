#!/usr/bin/env python3
import sys
import time
import yaml
import json
from dumpyaml import dump_yaml

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
"""
    prompt += """
Please clean it up and give me just the the json content as an answer. Don't wrap in ```json``` or anything like that.
- This JSON will eventually be converted to YAML. Please avoid characters that need escaping in YAML.
- Don't change the content of "grammar_point" field.
- "writeup:" should be factually correct and well-formatted. Keep in mind that any formatting needs to follow json escaping rules.
- "writeup:" should not quote the grammar point name. Don't quote japanese fragments like "なさい" or "なくてもいい".
- "writeup:" should use markdown-style formatting. For example, use **bold** for emphasis.
- "writeup:" text that quotes things, should use double-quotes (") rather than single-quotes (') or double single-quotes('').
   - For example, "This is a quote." is correct, but 'This is a quote.' or ''This is a quote.'' are not.
- Don't put examples directly in "writeup:" since there's a dedicated "examples:" field for that.
- Rewrite "writeup:" so the content is different without losing important details. If this grammar point takes parameters from other parts of the sentence, then name those parameters X, Y, etc.
  For example, "just because (X), it doesn't mean that (Y)". Don't create parameters if there would be only one.
- In "examples:" if the japanese sentence has japanese-style quotes (like「 and 」), then the English sentence should have double quotes (like ").
  If you see some questionable speech or potential hate speech, please rewrite the sentence so that it is grammatically equivalent.
- English contractions should have a single tick (like '), not double ticks (like '').
- Japanese in "examples" should sound smooth and natural to a native Japanese speaker. The english should be a natural translation.
- Add additional "examples" if some are needed to fully explore all of the nuances of the grammar point.
- If appropriate, add a "post_example_writeup" field after examples. This is will be displayed after the examples and is a continuation of the writeup after the context of example sentences has been absorbed by the reader. "post_example_writeup" may refer to example sentences and example sentences may be added if it aids the "post_example_writeup". Don't refer to example sentences by number since they won't be numbered when displayed.
- If there are proper person names in the examples, then replace them with other person names. Be sure to respect gender with the names.
- Use '\\n' rather than <br/> for line breaks.
- If there's a "false_friends" section, this is for terms that can easily be confused with the main grammar point. 
- If there are "false_friends", then add a "nuance" field to each that describes the functional difference between the false_friend and the main grammar point. Nuance should be terse and fairly abstract. Save more detailed comparisons for "post_false_friends_writeup" below.
- If appropriate, add a "post_false_friends_writeup" field after "false_friends". This section should generally discuss how to avoid confusion between the main grammar point and the false friends. Don't mention the term "false friends" in this section.
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
    N = 3
    error = ""
    for i in range(N):
        error += f"Attempt {i+1}/{N}\n"
        try:
            response = example_model.generate_content(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            error += f"  Before checking response\n"
            if not response or not response.text: continue
            error += f"  Before readback\n"
            readback = json.loads(response.text)
            error += f"  Before yaml dump\n"
            result = dump_yaml(readback)
            error += f"  After yaml dump\n"
            return result
        except Exception as e:
            error += f"PROBLEM WITH RESPONSE: {e}\n"
            if i == N - 1:
                raise e
            time.sleep(15)
    return error + prompt

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
