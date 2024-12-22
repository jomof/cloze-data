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
    prompt = """
You are a Japanese teacher. You speak native Japanese that is natural and fluent. You are explaining a Japanese grammar point to a student.

A Japanese grammar point will appear between:
BEGIN_GRAMMAR_POINT_YAML
[input]
BEGIN_GRAMMAR_POINT_YAML
(Where [input] is the raw grammar point data you will be given.)

When you answer, do not wrap your output in code fences or additional commentary. Provide only valid JSON, which will be converted into YAML later.

Follow these rules:

0. If the grammar point contains a verb or adjective, add a new array field at the top, called "conjugations". It should list all of the possible conjugations of grammar_point, including the grammar point itself. 
   For example, if the grammar point was, then the array should be: dictionary (plain non-past): とみえる [commonly used], polite (non-past): とみえます [commonly used], negative (plain): とみえない [commonly used], negative (polite): とみえません [commonly used], past (plain): とみえた [commonly used], past (polite): とみえました [commonly used], negative past (plain): とみえなかった [commonly used], negative past (polite): とみえませんでした [commonly used], te-form: とみえて [rare in everyday speech], conditional (provisional ば-form): とみえれば [uncommon], conditional (tara-form): とみえたら [uncommon], volitional (plain): とみえよう [very rare], volitional (polite): とみえましょう [very rare], imperative (plain): とみえろ [unnatural], imperative (polite): とみえてください [unnatural], potential: とみえられる [rare], passive: とみえられる [rare], causative: とみえさせる [extremely unusual]
   Place this array immediately after the "grammar_point" field.
1. Do not modify the "grammar_point" text from [input]; output it exactly as provided.
2. Avoid Unicode escape sequences like \\u3051, just emit the Unicode.
3. If "meaning_warning" is empty or null, omit it entirely.
4. If applicable and interesting, add an "etymology" field here that discusses the etymology of this grammar point.
5. The "writeup" field should:
    - Be primarily in English, supplemented by natural Japanese expressions as needed.
    - Incorporate essential details from the input while rephrasing for clarity.
    - Use markdown-style formatting (e.g., **important**).
    - Omit any example sentences here; examples go in the "examples" array.
    - Use double-quotes " for English quotes.
    - Refrain from quoting Japanese fragments such as なさい or なくてもいい.
    - You may include bullet points or sections like "Important Considerations" for clarity.
    - Don't mention the meaning_warning if there is one.
6. Provide an "examples" array with multiple entries. Each should have:
    - Each example **must** use the grammar_point, though it may be in conjugated form.
      - If there are other conjugated forms of the grammar point that are commonly used, then some of the example sentences **must** include those conjugated forms.
    - "japanese": a natural-sounding Japanese sentence using this grammar point.
    - "english": a natural-sounding English translation.
    - "register": register of the sentence. One of: casual, formal, semi-formal, sonkeigo (respectful), kenjōgo (humble), teineigo (polite), shitashii kuchō (intimate), bijinesu nihongo (business), bungo (literary), hōgen (dialectical), surangu (slang), gun-go (military), wakamono kotoba (youth), meirei-kei no teineigo (polite imperative)
      - Example sentences **should** exhibit a wide variety of registers.
      - If possible, include one of the keigo registers in example sentences.
      - If possible, include a shitashii kuchō (intimate) example
    - "setting": setting of the sentence: One of: flirty, first-date, professional, academic, humorous, sarcastic, serious, persuasive, apologetic, informative, interrogative, storytelling, instructional, commanding, friendly, condescending, supportive, sympathetic, inspirational, intimate, negotiating, technical, legal, religious, creative, casual slang, emergency/alarm, reflective, optimistic, pessimistic, cautious, excited, melancholic
      - ** Don't invent new settings** Just use the list provided.
      - Example sentences should exhibit a wide variety of settings.
      - There should always be at least one flirty sentence. This teaches the learner to flirt.
      - There should always be at least one first-date sentence. This teaches the learner to date.
    - "conjugation": If the grammar point is conjugatable, then specify which congugation is used.
      - The content of this "conjugation" field must be taken from the top-level list of conjugations you generated earlier. Use the 'type' field.
      - Please include example sentences with a variety of conjugations, especially the ones encountered in common usage.
      - "conjugation" **must** be about the main grammar point and not other parts of the sentence. 
    - "speaker_gender": (optional) gender of the speaker. One of: male, female. **Use only if this sentence would typically only be spoken by this gender**
      - Example sentences should include at least one male and one female speaker_gender.
    - "listener_gender": (optional) gender of the listener. One of: male, female (can omit if it doesn't matter in this sentence)
      - Example sentences should include at least one male and one female listener_gender.
    - "speaker_age": (optional) One of: younger, older (can omit if it doesn't matter)
      - Example sentences should include at least one younger and one older speaker_age.
    - "listener_age": (optional) One of: younger, older (can omit if it doesn't matter)
      - Example sentences should include at least one younger and one older listener_age.
    - "nuance":  Explain, in English with Japanese references to the sentence, how this sentence exhibits the interplay between the "speaker_age" vs "listener_age", "speaker_gender" vs "listener_gender", why the "register" applies.
      - If there is a "speaker_gender", then "nuance" **must** mention the specific Japanese, in 「quotes」, that would only be spoken by that gender. 
      - Nuance **must** refer to parts of the japanese sentence in 「quotes」.
    - "etymology": If there is something etymologically interesting in the Japanese sentence, then mention it here in English.
        
7. At least one example should include a flirty innuendo. It should be phrased as the speaker (male or female) flirting with the listener (female or male).
8. At least one example should suit an early romantic or first-meeting context (without using the word "date"). It should be phrased as the speaker (male or female) flirting with the listener (female or male).
9. If the input examples contain dialogue (A: ... B: ...), rewrite them into single-sentence statements that preserve the lesson but remove direct dialogue format.
10. Order examples from simpler to more advanced usage.
11. For English contractions, use a single apostrophe ' (e.g., "don't").
12. You may include a "post_example_writeup" section after "examples" if more clarification is helpful, but don't reference examples by any numeric label.
13. If "false_friends" are present, each entry should have:
    - "false_friend": the term.
    - "nuance": a concise contrast to the main grammar point (e.g., "Unlike [grammar_point], [false_friend]...").
14. You may add a "post_false_friends_writeup" to clarify further differences between the grammar point and these similar expressions. Do not call them "false friends" in that section—just provide a short explanation of how to avoid mixing them up.
15. You may fix minor inaccuracies in "details", but do not invent new details.
16. Ensure the JSON is valid and properly escaped for YAML conversion. Avoid additional formatting or code fences.

** Template of the Expected Output JSON **
Below is a minimal template demonstrating how the final JSON structure should look. You will output something like this, without code fences:

```
{
    "grammar_point": "...",
    "conjugations": [
        { type: "dictionary form",
          form: "とみえる",
          rarity: "common"
        },
        // etc.
    ],
    "jlpt": "...",
    "meaning": "...", // English
    "meaning_warning": "...", // English
    "details": {
        "Register": "...",
        // etc
    },
    "writeup": "...", // English
    "examples": [
        {
            "japanese": "...", // Japanese
            "english": "...", // English
            "conjugation": "dictionary form", // From top-level conjugation 'types'
            "register": "...", // Required
            "setting": "...", // Required
            "speaker_gender": "...", // Only if required for the sentence
            "listener_gender": "...", // Only if required for the sentence
            "speaker_age": "...", // Only if required for the sentence
            "listener_age": "...", // Only if required for the sentence
            "nuance": "..." // English
        },
        // etc
    ],
    "post_example_writeup": "", // English
    "false_friends": [
        {
            "term": "...",
            "meaning": "...",
            "kind": "...",
            "nuance": "" // English
        },
        // etc
    ],
    "post_false_friends_writeup": "..." // English
}```
    - If "meaning_warning" is null or empty, you omit it entirely.
    - The same goes for "false_friends", "post_example_writeup", and "post_false_friends_writeup" if they do not apply.

BEGIN_GRAMMAR_POINT_YAML
[input_replace]
BEGIN_GRAMMAR_POINT_YAML

Once you have the JSON content in mind, please do the following steps and make corrections as needed:
1. Are the sections that require English as the main language actually in English? Those sections are "nuance", "meaning", "meaning_warning", "etymology".
2. If the grammar_point is something conjugatable, like a verb, do the example sentences demonstrate the different conjugations?

That is all.
""".replace("[input_replace]", json.dumps(json.loads(repair_json(data)), ensure_ascii=False, indent=4))

    # Write the prompt to disk based on 'file'
    # with open(file + ".prompt", 'w', encoding='utf-8') as prompt_file:
    #     print(f"Writing prompt to {file}.prompt")
    #     prompt_file.write(prompt)
    backoff = 60
    N = 10
    response = ""
    for i in range(N):
        try:
            result = memoize_to_disk(generate_gemini_2_0, prompt)
            response = result.removeprefix("```json").removesuffix("\n").removesuffix("```")
            response = repair_json(response)
            response = json.loads(response)
            response = json.dumps(response, ensure_ascii=False, indent=4)
            # response = yaml.dumps(response, ensure_ascii=False, indent=4)
            return response
        except Exception as e:
            print("---prompt:")
            print(prompt)
            print("--response")
            print(response)
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
