import sys 
import json

def build_sentence_to_tokens_dict(file_path):
    # Read the JSON file
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Build the dictionary
    sentence_to_tokens = {}
    for entry in data:
        japanese_sentence = entry["Japanese"]
        tokens = entry["Tokens"]
        sentence_to_tokens[japanese_sentence] = tokens
    
    return sentence_to_tokens

def grammar_compliance_report(grammar_points, tokenized_sentences, report_file):
    tokenized_sentences = build_sentence_to_tokens_dict(tokenized_sentences)

    with open(grammar_points, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Open the output file for writing
    with open(report_file, 'w', encoding='utf-8') as output_file:
        # Iterate over each term and its meanings
        for term_entry in data:
            term = term_entry["Term"]
            meanings = term_entry["Meanings"]
            for meaning in meanings:
                japanese_sentence = meaning["Japanese"]
                tokens = tokenized_sentences[japanese_sentence]
                check_term = f"ₔ{term}"
                if check_term not in tokens:
                    output_file.write(f"Classification failure\n")
                    output_file.write(f'Grammar Point: {term}\n')
                    output_file.write(f'Japanese Sentence: {japanese_sentence}\n')
                    output_file.write(f'Tokens: {tokens}\n\n')

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python add_tokens_field.py <input_file> <output_file>")
        sys.exit(1)

    grammar_points = sys.argv[1]
    tokenized_sentences = sys.argv[2]
    report_file = sys.argv[3]
    grammar_compliance_report(grammar_points, tokenized_sentences, report_file)