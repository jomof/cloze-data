import json
import sys
import MeCab
import unidic

def parse_mecab_output(tokens):
    fields = ["Surface", "POS", "Subcategory1", "Subcategory2", "Subcategory3",
              "ConjugationType", "ConjugationForm", "BaseForm", "Reading", "Pronunciation"]

    result = []

    # Split the input by lines
    lines = tokens.strip().split('\n')
    
    # Iterate over each line and parse the token details
    for line in lines:
        if line == "EOS":
            continue
        parts = line.split('\t')
        surface = parts[0]
        details = parts[1].split(',')

        # Create a dictionary for each token
        token_dict = {"Surface": surface}
        for i, field in enumerate(fields[1:], 1):
            token_dict[field] = details[i - 1] if i - 1 < len(details) else ""
        
        result.append(token_dict)
    
    return result

def add_empty_tokens_field(input_file, output_file):
    wakati = MeCab.Tagger('-d "{}"'.format(unidic.DICDIR))

    # Read the JSON data from the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Add an empty "Tokens" field to each record
    for record in data:
        record["Tokens"] = wakati.parse(record["Japanese"]).replace('"', "'").replace("'',", ",")

    # Write the updated data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_tokens_field():
    if len(sys.argv) != 3:
        print("Usage: python add_tokens_field.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    add_empty_tokens_field(input_file, output_file)

if __name__ == '__main__':
    add_tokens_field()
