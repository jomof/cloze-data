import json

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find the section between BEGIN_RECORDS and END_RECORDS
    begin_marker = "BEGIN_RECORDS"
    end_marker = "END_RECORDS"
    start_index = content.find(begin_marker)
    end_index = content.find(end_marker)

    if start_index != -1 and end_index != -1:
        # Extract the JSON content between the markers
        start_index += len(begin_marker)
        json_content = content[start_index:end_index].strip()
    else:
        # No markers found, assume entire content is JSON
        json_content = content.strip()

    if not json_content:
        raise ValueError("No JSON content found")

    # Parse the JSON content
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON: {e}")

    return data

def merge_lists(list1, list2):
    merged_dict = {item['term']: item for item in list1}
    merged_dict.update({item['term']: item for item in list2})
    return list(merged_dict.values())

def write_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

original = read_json_file('resources/curated/grammar-by-jlpt-level.json')
new_content = read_json_file('outputfile.txt')

write_json_file(merge_lists(original, new_content), 'resources/curated/grammar-by-jlpt-level.json')

