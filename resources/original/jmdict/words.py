#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import argparse


def extract_entries_to_json(input_file, output_file):
    # Define the XML namespace for xml:lang attributes
    namespaces = {'xml': 'http://www.w3.org/XML/1998/namespace'}

    # Parse the JMdict XML
    tree = ET.parse(input_file)
    root = tree.getroot()

    entries = []

    # Iterate through each entry
    for entry in root.findall('entry'):
        # Unique entry ID
        ent_seq_el = entry.find('ent_seq')
        ent_id = ent_seq_el.text.strip() if ent_seq_el is not None else None

        # Collect kanji forms (words)
        words = [keb.text.strip() for keb in entry.findall('k_ele/keb') if keb.text]

        # Collect readings
        readings = [reb.text.strip() for reb in entry.findall('r_ele/reb') if reb.text]

        # Collect usage frequency/priority markers
        frequencies = []
        for kp in entry.findall('k_ele/ke_pri'):
            if kp.text:
                frequencies.append(kp.text.strip())
        for rp in entry.findall('r_ele/re_pri'):
            if rp.text:
                frequencies.append(rp.text.strip())
        # Deduplicate and sort frequencies
        frequencies = sorted(set(frequencies))

        # Skip entries without any frequency markers
        if not frequencies:
            continue

        # Collect part-of-speech tags
        pos_tags = []
        for sense in entry.findall('sense'):
            for pos in sense.findall('pos'):
                if pos.text:
                    pos_tags.append(pos.text.strip())
        pos_tags = sorted(set(pos_tags))

        # Collect English translations (glosses)
        translations = []
        for sense in entry.findall('sense'):
            for gloss in sense.findall('gloss'):
                if gloss.text:
                    translations.append(gloss.text.strip())

        entries.append({
            'id': ent_id,
            'words': words,
            'readings': readings,
            'frequencies': frequencies,
            'pos': pos_tags,
            'translations': translations
        })

    # Write out to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract words, readings, part-of-speech, translations, and usage frequencies from JMdict XML.'
    )
    parser.add_argument('input_file', help='Path to the JMdict XML file')
    parser.add_argument('output_file', help='Path to write the output JSON')
    args = parser.parse_args()

    extract_entries_to_json(args.input_file, args.output_file)
