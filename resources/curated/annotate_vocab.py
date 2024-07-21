import json
import csv
import argparse

def convert_to_json(
        jlpt,
        input_file, 
        output_file):
    data = []
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            entry = {
                'jlpt': jlpt,
                'wanikani': row['wanikani'],
                'word': row['word'],
                'reading': row['reading'],
                'senses': [row['sense 1'], row['sense 2'], row['sense 3']],
                'url': row['url']
            }
            # Remove empty senses
            entry['senses'] = [sense for sense in entry['senses'] if sense]
            data.append(entry)

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert TSV file to JSON.')

    parser.add_argument('input_file', help='Input TSV file name')
    parser.add_argument('output_file', help='Output JSON file name')
    parser.add_argument('jlpt', help='JLPT level')

    args = parser.parse_args()

    convert_to_json(args.jlpt, args.input_file, args.output_file)
