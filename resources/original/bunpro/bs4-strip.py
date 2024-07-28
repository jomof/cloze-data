#!/usr/bin/env python3
import sys
import yaml
import re
import os
from bs4 import BeautifulSoup


strip_by_class = [
    ("p", "order-2 text-detail font-bold text-secondary-fg md:order-1 md:justify-self-start"),
    ("a", "bp-anchor"),
    ("a", "block undefined"),
    ("p", "min-w-[2.75rem] select-none text-center")
]

combine_content_spaces = [
    ("p", None),
    ("div", "writeup-example--english"),
    ("p", "bp-sdw undefined"),
    #("div", "writeup-body")
]

combine_content_no_spaces = [
    ("div", "writeup-example--japanese"),
    ("p", "bp-ddw prose text-large md:text-subtitle")
]

def strip_html(soup):

    # Remove specific tags entirely
    for tag_name in ['rt', 'rp', 'script', 'button', 'svg', 'style', 'noscript']:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Unwrap specific tags.
    for tag_name in ['ruby', 'span']:
        for tag in soup.find_all(tag_name):
            tag.replace_with(tag.text)

    # # Remove specific tags entirely
    # for tag_name in ['meta', 'script', 'style', 'link', 'svg', 'rt', 'rp', 'button', 'noscript', 'footer']:
    #     for tag in soup.find_all(tag_name):
    #         tag.decompose()

    # # Unwrap specific tags.
    # for tag_name in ['ruby', 'span', 'strong']:
    #     for tag in soup.find_all(tag_name):
    #         tag.replace_with(tag.text)

    # Paste fragments back together with spaces.
    for (tag_name, class_name) in combine_content_spaces:
        for tag in soup.find_all(tag_name, class_=class_name):
            collapsed_text = ' '.join(tag.stripped_strings)
            tag.string = collapsed_text

    # Paste fragments back together with no spaces.
    for (tag_name, class_name) in combine_content_no_spaces:
        for tag in soup.find_all(tag_name, class_=class_name):
            collapsed_text = ''.join(tag.stripped_strings)
            tag.string = collapsed_text

    # # Strip specific tags and classes
    # for (tag_name, class_name) in strip_by_class:
    #     for tag in soup.find_all(tag_name, class_=class_name):
    #         tag.decompose() 

    # # Strip if empty
    for tag_name in ['li', 'div', 'ul', 'section', 'header']:
        for tag in soup.find_all(tag_name):
            if len(tag.text.strip()) == 0:
                tag.decompose()
    
    # Remove class and id attributes from all tags
    # for tag in soup.find_all(True):
        # if 'class' in tag.attrs:
        #     del tag.attrs['class']
        # if 'id' in tag.attrs:
        #     del tag.attrs['id']
        # if 'style' in tag.attrs:
        #     del tag.attrs['style']
    

    return soup.prettify()

def extract_grammar_info(name, html):
    soup = BeautifulSoup(html, 'html.parser')
    examples = []
    
    # Find all example sentences and extract them
    for li in soup.find_all('li', class_='writeup-example'):
        japanese = li.find('div', class_='writeup-example--japanese').text.strip()
        english = li.find('div', class_='writeup-example--english').text.strip()
        examples.append({
            'japanese': japanese,
            'english': english.replace("( ", "(").replace(" )", ")").replace(" .", ".")
        })
        li.decompose() 

    for li in soup.find_all('div', class_='relative z-1 flex flex-grow flex-col justify-center gap-4 text-center'):
        japanese = li.find('p', class_='bp-ddw prose text-large md:text-subtitle').text.strip()
        english = li.find('p', class_='bp-sdw undefined').text.strip()
        examples.append({
            'japanese': japanese,
            'english': english.replace("( ", "(").replace(" )", ")").replace(" .", ".")
        })
        li.decompose() 

    soup.find(id='examples').decompose()

    # Strip any orphaned tags
    strip_html(soup)

    # Writeup body
    writeup_body = soup.find('div', class_='writeup-body')
    if writeup_body is None:
        writeup_body = soup.find('div', class_='bp-ddw bp-writeup-body prose')
    if writeup_body is None:
        about_tag = soup.find('h3', string=lambda t: t and t.strip().startswith('About'))
        if about_tag:
            writeup_body = about_tag.find_next('div', class_='bp-sdw undefined')
            about_tag.find_parent().decompose
                
    if writeup_body is not None:
        writeup = ' '.join([s.strip() for s in writeup_body.get_text(strip=True).strip().split("\n") if s.strip()])
        writeup_body.decompose()
    else:
         raise ValueError("Writeup not found")
    soup.find(id='about').decompose()

    # Strip any orphaned tags
    strip_html(soup)
    for tag in soup.find_all("div", class_="writeup-body"):
        collapsed_text = ' '.join(tag.stripped_strings)
        tag.string = collapsed_text

    # Find the <title> tag
    title_tag = soup.find('title')

    if title_tag:
        # Extract the text content of the <title> tag
        title_text = title_tag.get_text(strip=True)
        
        # Use regular expression to extract ～てこそ and N2
        match = re.search(r'(.+?) \(JLPT (N\d+)\)', title_text)
        if match:
            grammar_point = match.group(1).strip()
            jlpt_level = match.group(2).strip()
        else:
            raise ValueError(f"Couldn't extract grammar point and jlpt_level")
    else:
        raise ValueError(f"No <title> tag")
    title_tag.decompose()

    # Find the tag containing grammar_point (like '～てこそ')
    grammar_point_tag = soup.find('h1', string=lambda t: t and t.strip() == grammar_point)
    if grammar_point_tag is None:
        grammar_point_tag = soup.find('p', string=lambda t: t and t.strip() == grammar_point)
    if grammar_point_tag is None:
        grammar_point_tag = soup.find('h1', class_="bp-text-shadow-reviewable-header text-reviewable-header-mobile font-bold text-primary-accent md:text-reviewable-header-desktop")
    meaning = None
    if grammar_point_tag:
        meaning_tag = grammar_point_tag.find_next('h2')
        if meaning_tag is None:
            meaning_tag = grammar_point_tag.find_next('p')
        
        if meaning_tag:
            # Extract and print the text content of the <h2>
            meaning = meaning_tag.get_text(strip=True)
    if meaning is None:
        raise ValueError(f"Could find meaning for grammar point '{grammar_point}'")
    grammar_point_tag.decompose()
    meaning_tag.decompose()

    # Find the warning tag for meaning if present
    meaning_warning_tag = soup.find('p', class_='text-small text-warning md:text-body')
    if meaning_warning_tag:
        meaning_warning = meaning_warning_tag.get_text(strip=True)
        meaning_warning_tag.decompose()
    else:
        meaning_warning = None

    # Strip any orphaned tags
    strip_html(soup)


    # Find the "Details" section
    details_section = soup.find('div', id='details')

    if details_section:
        # Find the following <ul> element that contains the details list
        details_list = details_section.find_next('ul')
        
        # Extract all <li> elements within the details list
        details_items = details_list.find_all('li') if details_list else []
        
        # Extract and print the heading and value of each detail
        details = {}
        for item in details_items:
            heading = item.find('h4').get_text(strip=True)
            value = item.find('p').get_text(strip=True)
            details[heading] = value
        
        details_section.find_parent().decompose()
    else:
        raise ValueError("No 'Details' section found")
    
    # Find the "Synonyms" section
    antonyms_section = soup.find('div', id='antonyms')
    antonyms = None

    if antonyms_section:
        antonyms_list = antonyms_section.find_next('ul')
        antonyms_items = antonyms_list.find_all('li') if antonyms_list else []
        antonyms = []
        for item in antonyms_items:
            term = item.find('p', class_='text-left text-small font-bold text-primary-fg sm:text-body').get_text(strip=True)
            meaning = item.find('p', class_='line-clamp-1 text-left text-detail font-bold text-secondary-fg sm:text-small').get_text(strip=True)
            antonyms.append([term, meaning])
        antonyms_section.decompose()
    
    # Find the "Synonyms" section
    synonyms_section = soup.find('div', id='synonyms')
    synonyms = None

    if synonyms_section:
        # Find the following <ul> element that contains the synonyms list
        synonyms_list = synonyms_section.find_next('ul')
        
        # Extract all <li> elements within the synonyms list
        synonyms_items = synonyms_list.find_all('li') if synonyms_list else []
        
        # Extract and print the text content of each synonym
        synonyms = []
        for item in synonyms_items:
            term = item.find('p', class_='text-left text-small font-bold text-primary-fg sm:text-body').get_text(strip=True)
            meaning = item.find('p', class_='line-clamp-1 text-left text-detail font-bold text-secondary-fg sm:text-small').get_text(strip=True)
            synonyms.append([term, meaning])
        synonyms_section.decompose()

    # Remove some unused sections
    soup.find(id='self-study').decompose()
    soup.find(id='discussion').decompose()
    soup.find(id='js-rev-header').decompose()
    elements_with_id = soup.find_all(id=re.compile(r'^discourse-post-id'))
    for element in elements_with_id:
        element.decompose()
    del soup.find(id='__next')['id']
    del soup.find(id='js-page-top')['id']
    del soup.find(id='structure')['id']
    del soup.find(id='online')['id']
    del soup.find(id='offline')['id']
    # del soup.find(id='antonyms')['id']

    # Strip any orphaned tags
    strip_html(soup)

    # Make a grammar object
    grammar = {
        "grammar_point": grammar_point,
        "jlpt": jlpt_level,
        "meaning": meaning,
        "details": details,
        "writeup": writeup,
        "examples": examples
    }

    if meaning_warning is not None:
        grammar["meaning_warning"] = meaning_warning

    if synonyms is not None:
        grammar["synonyms"] = synonyms

    if antonyms is not None:
        grammar["antonyms"] = antonyms

    # Dump the object to a YAML string, preserving multi-line strings and UTF-8 characters
    grammar_yaml = yaml.dump(grammar, default_flow_style=False, allow_unicode=True)

    if len(examples) < 2:
        raise ValueError("Not enough sentences found")

    # Embed the JSON data back into the HTML in a <script> tag
    script_tag = soup.new_tag('script', type='application/json')
    script_tag.string = grammar_yaml
    soup.body.append(script_tag)

    return soup.prettify()



def main(filename, input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()

        grammar_info = extract_grammar_info(os.path.basename(input_file), html_content)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(grammar_info)
        
        
    except Exception as e:
        print(f"Error processing file {filename}: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python script.py <filename> <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        filename = sys.argv[1]
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        main(filename, input_file, output_file)
