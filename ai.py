PROJECT_ID = "jomof-sandbox"  # @param {type:"string"}
LOCATION = "us-west1"  # @param {type:"string"}

import vertexai

import os

def find_and_trim_files(directory, file_extension):
    """
    Recursively search for files with a specific extension in the given directory
    and return their paths with the extension trimmed.

    Args:
        directory (str): The directory to search in.
        file_extension (str): The file extension to search for.

    Returns:
        list: A list of paths with the file extension trimmed.
    """
    trimmed_file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(file_extension):
                full_path = os.path.join(root, file)
                trimmed_path = full_path[:-len(file_extension)]
                trimmed_file_paths.append(trimmed_path)
    return trimmed_file_paths

source_files = find_and_trim_files(".", ".ai.txt")

prompt = f"""
My prompt:
I'm working on a software project that involves teaching Japanese to native English speakers.
I'm asking you to look at the code and data that I have and to suggest improvements. 

First, I'm gonna give you the content of each file in the project. These are the files I'm asking you to modify and improve.

"""

for source_file in source_files:
    with open(source_file, 'r') as file:
        file_contents = file.read()


    prompt += f"""
BEGIN_FILE_CONTENT:{source_file}
{file_contents}
END_FILE_CONTENT
"""

prompt += f"""
Please improve 10 grammar point records from grammar-by-jlpt-level.json. Pick the ones most in need of improvement to make them more correct, more complete, and more interesting.
Priorities:
- Having 8+ sentences that orthogonally cover all of the main nuances of the grammar point.
- Japanese should sound natural to a native speaker.
- Inaccurate, incomplete, or inconsistent englishTermMeaning.
- Correcting English spelling or grammar.
- Correcting Japanese spelling or grammar.
- Incorrect translation between English and Japanese.
- Prefer grammar point records that have no provenance or have provenance not set to "vertexai".
- Japanese should use kanji, hiragana, or katakana when it is the most natural for the circumstance.
- Sentences inside a single grammar point should have a variety of lengths and complexities.
- Sentences inside a single grammar point should have a variety of politeness levels, negative/non-negative, past/non-past.
- More advanced grammar points--n3, n2, n1--should display more complex conjugations (volitional, passive etc).
- Earlier grammar points--n5, n4, n3--should mostly stick with simpler  conjugations (past, negative).
- When possible, sentences should sounds as if spoken by someone happy, confident, flirtatious, and cool. 
- Good first date sentences may make good example sentences.
- Pick sentences spread evenly across the jlpt levels--n5, n4, n3, n2, n1.
- It's okay to add new grammar points if you see something that makes sense.
- If englishTermMeaning has multiple sub-meanings separated by semicolons, then there should be at least one sentence that covers each sub-meaning. The nuance for that sentence should call out the sub-meaning deployed.
Revise the record and provide the revised grammar point records in json format. Nuances should be fairly abstract and should serve to distinguish the different sentences from each other.
Set the provenance of the records you pick to "vertexai".  
Please don't use quotation marks in nuances. This is a sign that it's not abstract enough.

Please start with BEGIN_RECORDS and end with END_RECORDS to make it easier for me to parse. Don't write anything before BEGIN_RECORDS.
After END_RECORDS, give me a written summary that explains why these were the most important grammar points to fix first.
Summarize the changes you made and why they improve the situation.
If you think any grammar points should be split into two distinct points, then let me know in the summary section.

Answer:
"""


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
        "You are a helpful language translator.",
        "Your mission is to translate text in English to Japanese.",
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




