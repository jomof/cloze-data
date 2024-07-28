#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import argparse

def extract_sentences_to_json(input_file, output_file):
    # Define the namespaces
    namespaces = {'xml': 'http://www.w3.org/XML/1998/namespace'}

    # Load and parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()

    sentence_pairs = []

    # Iterate through each entry
    for entry in root.findall('entry'):
        for sense in entry.findall('sense'):
            for example in sense.findall('example'):
                # Extract Japanese and English sentences using the namespaces
                japanese_sentence = example.find("./ex_sent[@xml:lang='jpn']", namespaces)
                english_sentence = example.find("./ex_sent[@xml:lang='eng']", namespaces)
                
                if japanese_sentence is not None and english_sentence is not None:
                    jap_text = japanese_sentence.text.strip() if japanese_sentence.text else ""
                    eng_text = english_sentence.text.strip() if english_sentence.text else ""
                    
                    # Store the sentence pairs
                    sentence_pairs.append({'Japanese': jap_text, 'English': eng_text})

    # Write the sentence pairs to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sentence_pairs, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract sentence pairs from JMDict XML and save to JSON.')

    parser.add_argument('input_file', help='Input XML file name')
    parser.add_argument('output_file', help='Output JSON file name')

    args = parser.parse_args()

    extract_sentences_to_json(args.input_file, args.output_file)
