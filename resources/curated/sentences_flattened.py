import json
import sys
from typing import List, Dict

def flatten_japanese_english_pairs(input_file: str, output_file: str) -> None:
    """
    Flattens a JSON file containing Japanese-English pairs into a list of dictionaries.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output JSON file.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data: List[Dict] = json.load(f)

    flattened_list: List[Dict[str, str]] = []
    for entry in data:
        for meaning in entry.get("Meanings", []):
            japanese = meaning.get("Japanese", "").strip()
            english = meaning.get("English", "").strip()

            # Ensure both Japanese and English are strings
            if isinstance(japanese, list):
                japanese = ' '.join(japanese)
            elif not isinstance(japanese, str):
                japanese = str(japanese)

            if isinstance(english, list):
                english = ' '.join(english)
            elif not isinstance(english, str):
                english = str(english)

            if not japanese and not english:
                continue  # Skip entries with both fields blank
            elif not japanese or not english:
                print(f"Error: Incomplete entry found - Japanese: '{japanese}', English: '{english}'", file=sys.stderr)
            else:
                flattened_list.append({"Japanese": japanese, "English": english})

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(flattened_list, f, ensure_ascii=False, indent=2)

def main():
    """
    Main function for the script.
    """
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    flatten_japanese_english_pairs(input_file, output_file)

if __name__ == '__main__':
    main()