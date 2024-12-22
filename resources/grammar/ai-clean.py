#!/usr/bin/env python3
import sys
import time
import yaml
import json
import os
from dumpyaml import dump_yaml
from google.genai import types
from google import genai

import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
from json_repair import repair_json
import hashlib
import requests

#genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PROJECT_ID = "jomof-sandbox"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}


def get_hash(func_name, *args):
    # Use MD5 to generate a unique hash combining function name and inputs
    combined_args = ":".join(map(str, args))
    return hashlib.md5(f"{func_name}:{combined_args}".encode()).hexdigest()

def memoize_to_disk(func, *args):
    """
    Memoize the result of 'func(*args)' using a local Flask caching service.
    """
    base_url="http://127.0.0.1:5000"

    # Step 1: Create the cache key (MD5 hash).
    hash_key = get_hash(func.__name__, *args)
    
    # Step 2: Attempt to retrieve the memoized result from the cache service
    get_endpoint = f"{base_url}/cache/{hash_key}"
    try:
        response = requests.get(get_endpoint)
        if response.status_code == 200:
            data = response.json()
            if data["value"] is not None:
                print(f"Reading from service: {hash_key}")
                return data["value"]
    except requests.RequestException as e:
        # If something goes wrong (e.g. service is down), we simply compute anew
        print(f"Error contacting cache service: {e}")

    # Step 3: Compute the result if not found in cache
    result = func(*args)

    # Step 4: Store in the cache
    post_endpoint = f"{base_url}/cache/{hash_key}"
    try:
        response = requests.post(post_endpoint, json={"value": result})
        if response.status_code != 200:
            print(f"Warning: Could not store value in cache. Status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error storing value in cache: {e}")

    return result

def ai_clean(data, file):
    data = repair_json(json.dumps(yaml.safe_load(data), indent=2, ensure_ascii=False))
    prompt = f"""
You are a kind and funny Japanese teacher. You speak native Japanese that is natural and fluent. 
You are explaining a Japanese grammar point to a student.
Here is a Japanese grammar point encoded between BEGIN_GRAMMAR_POINT_JSON/BEGIN_GRAMMAR_POINT_JSON.
BEGIN_GRAMMAR_POINT_JSON
{data}
BEGIN_GRAMMAR_POINT_JSON
"""
    prompt += """
Please clean it up and give me just the the json content as an answer. Don't wrap in ```json``` or anything like that.
- This JSON will eventually be converted to YAML. Please avoid characters that need escaping in YAML.
- Don't change the content of "grammar_point" field.
- Output of japanese characters should be in kanji, hiragana, or katakana. Don't use encodings like \\u3051.
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
- If an example of dialog between two people, then replace it with a different sentence with no dialog. As much as possible, try to keep the lesson or point of the original example.
- Add additional "examples" if some are needed to fully explore all of the nuances of the grammar point.
- If appropriate, add a "post_example_writeup" field after examples. This is will be displayed after the examples and is a continuation of the writeup after the context of example sentences has been absorbed by the reader. "post_example_writeup" may refer to example sentences and example sentences may be added if it aids the "post_example_writeup". Don't refer to example sentences by number since they won't be numbered when displayed.
- If there are proper person names in the examples, then replace them with other person names. Be sure to respect gender with the names.
- "examples" should be roughly in order of difficulty, with easier examples first.
- Use '\\n' rather than <br/> for line breaks.
- If there's a "false_friends" section, this is for terms that can easily be confused with the main grammar point. 
- If there are "false_friends", then add a "nuance" field to each that describes the functional difference between the false_friend and the main grammar point. Nuance should be terse and fairly abstract. Save more detailed comparisons for "post_false_friends_writeup" below.
- If appropriate, add a "post_false_friends_writeup" field after "false_friends". This section should generally discuss how to avoid confusion between the main grammar point and the false friends. Don't mention the term "false friends" in this section.
- You may correct "details", but don't add new details.
- Don't forget to escape double-quotes(") and generally make sure the json is well formatted.
"""

    # Write the prompt to disk based on 'file'
    # with open(file + ".prompt", 'w', encoding='utf-8') as prompt_file:
    #     print(f"Writing prompt to {file}.prompt")
    #     prompt_file.write(prompt)
    backoff = 60
    N = 10
    error = ""
    for i in range(N):
        error += f"Attempt {i+1}/{N}\n"
        try:
            result = memoize_to_disk(generate_gemini_2_0, prompt)
            response = repair_json(result.removeprefix("```json").removesuffix("\n").removesuffix("```"))
            error += f"  Before checking response\n"
            # if not response or not response.text: continue
            error += f"  Before readback\n"
            readback = json.loads(response)
            error += f"  Before yaml dump\n"
            result = dump_yaml(readback)
            error += f"  After yaml dump\n"
            return response
        except Exception as e:
            prompt += f"\nMAKE SURE IT IS WELL FORMATTED JSON THAT CAN BE CONVERTED TO YAML!!!\nThe error from your last attempt was: {e}\n"
            print(f"Error: {e}")
            if backoff > 600:
                raise e
            time.sleep(backoff)
            backoff *= 2
            
    return error + prompt

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


def generate_1_5(prompt):
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
    


def main(input_file, output_file):
    # try:
        # print(f"IN:  {input_file}")
        # print(f"OUT: {output_file}")
        with open(input_file, 'r', encoding='utf-8') as file:
            data = file.read()
        result = ai_clean(data, f"{output_file}")

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(result)
        
    # except Exception as e:
    #     print(f"Error processing file {input_file}: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        main(input_file, output_file)
