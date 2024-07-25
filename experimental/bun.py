PROJECT_ID = "jomof-sandbox"  # @param {type:"string"}
LOCATION = "us-west1"  # @param {type:"string"}

import vertexai

import os

files = ["-てこそ", "-に-ない", "-よう--う-まい - が-と", "-んです-のです", 
         "adjective-て-noun-で", "１-りとも-ない", "～るまでだ", "-なり-なり", "-のうち-で", "-ようとしない",             
         "adjective-て-b", "adjective-の-は", "～ところに・～ところへ"]

pairs = []
for file in files:
    input = f"tmp/stripped/sample/{file}"
    with open(input, 'r', encoding='utf-8') as file:
        data = file.read()
    pairs.append([input, data])



prompt = f"""
My prompt:
I'm gonna give you some HTML content that I'll ask some questions about below.
"""

for pair in pairs:
    prompt += f"""
HTML_CONTENT:{pair[0]}
{pair[1]}
HTML_CONTENT
"""

prompt += """
Please explain the data available in this kind of page.

Describe a yaml schema that will work for all of them. Make sure the "structure:" section is expressive enough.
The schema should be heavily commented so that a future reader can understand how to use the fields.
The "meaning:" part of the schema is for the english translations of the grammar point. It should be a list:
Surround the schema with BEGIN_SCHEMA/END_SCHEMA.

Pick three interesting grammar points and render them in the yaml. 
- All three points should have a consistent schema. Especially with respect to "structure:"
- The 'grammar_point:' name should be the original and not converted to something else (so "～てこそ" rather than "-te koso")
- The html source has japanese text with <Ruby> tags to encode furigana. Please strip the furigana and just present the readable Japanese sentences.
- Under "synonyms:" don't emit a list of "meanings:" for each. Those meanings will be present in the yaml for that other point.
- You may correct mistakes you find. 
- If the Japanese sounds stiff or unnatural, please adjust it.
- You may also augment the output with additional relevant information. 
    - You may add new example sentences.
    - You may add additional online or offline resources.
- For example sentences, add a 'nuance:' field which abstractly describes the nuance of this sentence. 
  Nuance serves to distinguish sentences from each other. Nuances should be orthogonal from each other.
  Sentence-level nuance should not contain quotes or restate the grammar_point name. These are signs it's not abstract enough.
  Sentence-level nuance should not just rephrase the sentence in some one. It should be more abstract and serve to distinguish the usage pattern in this sentence from the other example sentences.
  Sentence-level nuance should not reference specific nouns from the sentence. That's a sign it's not abstract enough.
- For example sentences, you may optionally add a 'trivia:' tag that describes interesting trivia related to the sentence. Trivia may be current or historical, but it shouldn't portray Japan negatively such as mentioning low birth rate. Also avoid stereotypes like hard-working.
- There should typically be 8+ example sentences. Add them if needed. Or at least enough to cover every nuance a Japanese language learner should learn.
- Example sentences should definitely cover each aspect listed under 'structure:'.
- Example sentences should have a variety of different lengths and shouldn't sound repetitive.
- Example sentences should definitely cover each English translation of the grammar point. The nuance text should mention which English translation the sentence covers.
- Good sentences sound confident, a little flirty, and fun to be around. They may reference culturally interesting aspects of Japan. They should be suitable for questions or answers on a first date.
- For each synonym, add a 'nuance:' field that describes how the current grammar point is distinguished from the synonym.
- Add a top level 'uance:' section that descrives the vibe of this grammar point. What feeling or mood does it convey. Example: '～てこそ has a strong literary and philosophical feel to it and is often used when expressing a deeply held belief or conviction.'
- If there is a 'discussion:' section, you may augment the other fields with advice from the discussion. However, don't include the actual 'discussion:' tag.
- Generally, you can add 'nuance:' or 'trivia:' at any level.
- Put a 'notes:' section in the yaml that describes the augmentations, additions, corrections, and changes you made.
- Don't generate you own fields if they would have empty meaning. For example, "notes: No special notes." or "glossary_terms: []"

Surround the record yaml with BEGIN_YAML/END_YAML.

"""

print(prompt)

vertexai.init(project=PROJECT_ID, location=LOCATION)


from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
)

MODEL_ID = "gemini-1.5-pro-001"  # @param {type:"string"}

# Initialize the generative model
model = GenerativeModel(MODEL_ID)

# Load an example model with system instructions
example_model = GenerativeModel(
    MODEL_ID,
    system_instruction=[
        "You are an experienced Japanese language teacher and you are writing a book or database that summarizes Japanese grammar points.",
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
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}

# Set contents to send to the model
contents = [prompt]


# Prompt the model to generate content
response = example_model.generate_content(
    contents,
    generation_config=generation_config,
    safety_settings=safety_settings,
)

with open('outputfile.txt', 'w') as file:
    # Write the string to the file
    file.write(response.text)




