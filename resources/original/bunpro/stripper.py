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