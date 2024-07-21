import json
import sys

def flatten_japanese_english_pairs(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    flattened_list = []
    for entry in data:
        for meaning in entry.get("Meanings", []):
            japanese = meaning.get("Japanese", "").strip()
            english = meaning.get("English", "").strip()

            if not japanese and not english:
                continue  # Skip entries with both fields blank
            elif not japanese or not english:
                print(f"Error: Incomplete entry found - Japanese: '{japanese}', English: '{english}'", file=sys.stderr)
            else:
                flattened_list.append({"Japanese": japanese, "English": english})

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(flattened_list, f, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    flatten_japanese_english_pairs(input_file, output_file)

if __name__ == '__main__':
    main()
