import json
import sys
import re

def reformat_sentences(input_file, output_file, special_output_file):
    # Read the data from the input file
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Initialize lists for reformatted data and special records
    reformatted_data = []
    special_records = []

    # Reformat the data
    for record in data:
        # Check if the record is a special record (where englishTermMeaning is blank)
        if not record.get("englishTermMeaning"):
            special_records.append(record)
            continue

        meanings = []
        levels = {k: v for k, v in record.items() if re.match(r'^level\d*$', k)}
        base_level = levels.get("level")
        
        i = 1
        while f"japaneseSentence{i}" in record or (i == 1 and "japaneseSentence" in record):
            jap_key = f"japaneseSentence{i}" if i > 1 else "japaneseSentence"
            eng_key = f"englishSentenceMeaning{i}" if i > 1 else "englishSentenceMeaning"
            term_key = f"englishTermMeaning{i}" if i > 1 else "englishTermMeaning"
            audio_key = f"audioLink{i}" if i > 1 else "audioLink"
            level_key = f"level{i}" if i > 1 else "level"
            
            if jap_key in record and eng_key in record:
                meaning = {
                    "Level": levels.get(level_key, base_level) or "",
                    "Japanese": record.pop(jap_key, ""),
                    "English": record.pop(eng_key, ""),
                    "EnglishTermMeaning": record.pop(term_key, ""),
                    "AudioLink": record.pop(audio_key, "")
                }
                meanings.append(meaning)
            i += 1

        # Rename the term key to Term
        record["Term"] = record.pop("term")
        record["Meanings"] = meanings
        
        # Remove all top-level keys except "Term" and "Meanings"
        for key in list(record.keys()):
            if key not in ["Term", "Meanings"]:
                record.pop(key)
        
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
