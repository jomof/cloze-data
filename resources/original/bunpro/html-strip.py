#!/usr/bin/env python3
from bs4 import BeautifulSoup

def strip_html(content):
    soup = BeautifulSoup(content, 'html.parser')

    # Remove specific tags entirely
    for tag_name in ['meta', 'script', 'style', 'link', 'svg']:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    
    # Remove class and id attributes from all tags
    for tag in soup.find_all(True):
        # if 'class' in tag.attrs:
        #     del tag.attrs['class']
        # if 'id' in tag.attrs:
        #     del tag.attrs['id']
        # if 'style' in tag.attrs:
        #     del tag.attrs['style']
        if 'aria-hidden' in tag.attrs:
            del tag.attrs['aria-hidden']
        if 'aria-label' in tag.attrs:
            del tag.attrs['aria-label']
        if 'aria-labelledby' in tag.attrs:
            del tag.attrs['aria-labelledby']
        if 'aria-live' in tag.attrs:
            del tag.attrs['aria-live']
        if 'aria-modal' in tag.attrs:
            del tag.attrs['aria-modal']
        if 'aria-haspopup' in tag.attrs:
            del tag.attrs['aria-haspopup']
        if 'aria-valuemax' in tag.attrs:
            del tag.attrs['aria-valuemax']
        if 'aria-valuemin' in tag.attrs:
            del tag.attrs['aria-valuemin']
        if 'aria-controls' in tag.attrs:
            del tag.attrs['aria-controls']
        if 'aria-selected' in tag.attrs:
            del tag.attrs['aria-selected']
        if 'aria-valuenow' in tag.attrs:
            del tag.attrs['aria-valuenow']
        if 'href' in tag.attrs:
            del tag.attrs['href']
        if 'title' in tag.attrs:
            del tag.attrs['title']
        if 'role' in tag.attrs:
            del tag.attrs['role']
        if 'disabled' in tag.attrs:
            del tag.attrs['disabled']
        if 'rel' in tag.attrs:
            del tag.attrs['rel']
        if 'target' in tag.attrs:
            del tag.attrs['target']
        if 'alt' in tag.attrs:
            del tag.attrs['alt']
        if 'data-nimg' in tag.attrs:
            del tag.attrs['data-nimg']
        if 'decoding' in tag.attrs:
            del tag.attrs['decoding']
        if 'loading' in tag.attrs:
            del tag.attrs['loading']
        if 'src' in tag.attrs:
            del tag.attrs['src']
        if 'lang' in tag.attrs:
            del tag.attrs['lang']
        if 'data-gp-id' in tag.attrs:
            del tag.attrs['data-gp-id']
        if 'tabindex' in tag.attrs:
            del tag.attrs['tabindex']
        if 'data-n-css' in tag.attrs:
            del tag.attrs['data-n-css']
        if 'data-location' in tag.attrs:
            del tag.attrs['data-location']

    return soup.prettify()

def main(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = file.read()

        stripped_content = strip_html(data)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(stripped_content)
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        print("Usage: python script.py <filename> <input_file> <output_file>")
        print("But was", sys.argv)
    else:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        main(input_file, output_file)
