import json
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <output_file> <input_file1> <input_file2> ...")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    concatenated_array = []

    for input_file in input_files:
        with open(input_file, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    concatenated_array.extend(data)
                else:
                    print(f"Warning: {input_file} does not contain a JSON array. Skipping.")
            except json.JSONDecodeError as e:
                print(f"Error reading {input_file}: {e}. Skipping.")

    with open(output_file, 'w') as f:
        json.dump(concatenated_array, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
