import json
import sys
import re

def reformat_sentences(input_file, output_file, special_output_file):
    """
    Reformats the input JSON data containing Japanese and English sentences with their meanings
    into a structured format suitable for further processing. Handles special cases where certain 
    fields may be missing or need to be propagated forward.

    Args:
    - input_file: Path to the input JSON file.
    - output_file: Path to the output JSON file for reformatted data.
    - special_output_file: Path to the output JSON file for special records where 'englishTermMeaning' is blank.
    """
    # Read the data from the input file
    with open(input_file, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    # Initialize lists for reformatted data and special records
    reformatted_data = []
    special_records = []
    seen_terms = set()
    seen_japanese_sentences = set()
    seen_english_sentences = set()

    # Validate that the input data is a list of dictionaries
    if not isinstance(data, list):
        raise ValueError("The input JSON must be a list of dictionaries.")
    if not all(isinstance(record, dict) for record in data):
        raise ValueError("Each item in the input JSON list must be a dictionary.")

    # Reformat the data
    for record in data:
        # Validate required keys in each record
        if 'term' not in record:
            raise ValueError("Each record must contain a 'term' key.")
        if 'englishTermMeaning' not in record:
            raise ValueError("Each record must contain an 'englishTermMeaning' key.")

        # Check if the record is a special record (where englishTermMeaning is blank)
        if not record["englishTermMeaning"]:
            special_records.append(record)
            continue

        # Check for missing nuance
        if 'nuance' not in record:
            term = record.get("term", "Unknown term")
            raise ValueError(f"Missing 'nuance' key in record for term: {term}")

        # Check for duplicate terms
        term = record["term"]
        if term in seen_terms:
            raise ValueError(f"Duplicate term found: {term}")
        seen_terms.add(term)

        meanings = []
        levels = {k: v for k, v in record.items() if re.match(r'^level\d*$', k)}
        base_level = levels.get("level")
        base_term_meaning = record["englishTermMeaning"]

        # Iterate through the possible sentences
        i = 1
        while f"japaneseSentence{i}" in record or (i == 1 and "japaneseSentence" in record):
            jap_key = f"japaneseSentence{i}" if i > 1 else "japaneseSentence"
            eng_key = f"englishSentenceMeaning{i}" if i > 1 else "englishSentenceMeaning"
            term_key = f"englishTermMeaning{i}" if i > 1 else "englishTermMeaning"
            nuance_key = f"nuance{i}" if i > 1 else "nuance"
            level_key = f"level{i}" if i > 1 else "level"

            # Ensure required keys are present
            if jap_key not in record or eng_key not in record:
                raise ValueError(f"Record missing required keys: {jap_key} or {eng_key}")

            # Check for duplicate Japanese sentences
            japanese_sentence = record[jap_key]
            if japanese_sentence in seen_japanese_sentences:
                raise ValueError(f"Duplicate Japanese sentence found: {japanese_sentence}")
            seen_japanese_sentences.add(japanese_sentence)

            # Check for duplicate English sentences
            english_sentence = record[eng_key]
            if english_sentence in seen_english_sentences:
                raise ValueError(f"Duplicate English sentence found: {english_sentence}")
            seen_english_sentences.add(english_sentence)

            # Handle levels and propagate forward if not explicitly specified
            level = levels.get(level_key, base_level) or ""
            base_level = level  # Update base level to current level if present

            # Handle term meaning and propagate forward if not explicitly specified
            term_meaning = record.get(term_key, base_term_meaning)
            if term_meaning:
                base_term_meaning = term_meaning  # Update base term meaning if present

            # Get the nuance and check for double single quotes
            nuance = record.get(nuance_key, "")
            if nuance.count("'") > 1:
                raise ValueError(f"Nuance contains more than one single quote: {nuance}")

            # Create the meaning dictionary
            meaning = {
                "Level": level,
                "Japanese": record[jap_key],
                "English": record[eng_key],
                "EnglishTermMeaning": term_meaning,
                "Nuance": nuance
            }
            meanings.append(meaning)
            i += 1

        # Rename the term key to Term
        record["Term"] = record.pop("term")
        record["Meanings"] = meanings

        # Keep only "Term", "Meanings", and any additional metadata (excluding 'audioLink')
        record = {k: record[k] for k in ["Term", "Meanings", "provenance"] if k in record}

        reformatted_data.append(record)

    # Write the reformatted data to the output file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(reformatted_data, file, ensure_ascii=False, indent=2)

    # Write the special records to the special output file
    with open(special_output_file, 'w', encoding='utf-8') as file:
        json.dump(special_records, file, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_file> <output_file> <special_output_file>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    special_output_file = sys.argv[3]

    reformat_sentences(input_file, output_file, special_output_file)

if __name__ == "__main__":
    main()
