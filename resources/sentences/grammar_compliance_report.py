#!/usr/bin/env python3
import sys 
import json
import MeCab
import unidic
from mecab.compact_sentence import mecab_raw_to_tokens
from mecab.tagger import get_mecab_tagger

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
    wakati = get_mecab_tagger()
    tokenized_sentences = build_sentence_to_tokens_dict(tokenized_sentences)

    with open(grammar_points, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Open the output file for writing
    with open(report_file, 'w', encoding='utf-8') as output_file:
        # Iterate over each term and its meanings
        seen = []
        for term_entry in data:
            point_name = term_entry["Term"]
            terms = point_name.split("/")
            meanings = term_entry["Meanings"]
            for meaning in meanings:
                japanese_sentence = meaning["Japanese"]
                tokens = tokenized_sentences[japanese_sentence]
                has_term = False
                for term in terms:
                    check_term = f"ᵍ{term}"
                    if check_term in tokens:
                        has_term = True
                if has_term: continue
                for term in terms:
                    raw_mecab = wakati.parse(term.replace("○○", "XXX")).replace('"', "'").replace("'',", ",")
                    term_tokens = mecab_raw_to_tokens(raw_mecab)
                    term_guess = ""
                    for term_token in term_tokens:
                        if term_guess != "":
                            term_guess += "|"
                        if term_token.pos == "動詞":
                            term_guess += "ᵇ"
                            term_guess += term_token.base_form
                        else: 
                            term_guess += term_token.surface

                    term_guess = term_guess.replace("XXX", "○○")

                    if term_guess not in seen:
                        #seen.append(term_guess)
                        output_file.write(f"Classification failure\n")
                        #output_file.write(f'GDebug: "{raw_mecab}"\n')
                        output_file.write(f'"{term_guess}": "{point_name}", #  {tokens}\n')
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