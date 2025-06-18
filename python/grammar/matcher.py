import re
from python.mecab.compact_sentence import japanese_to_compact_sentence, compact_sentence_to_japanese


class Matcher:
    def __init__(
        self,
        matcher: str,
        regex_string: str,
    ):
        self.matcher = matcher
        self.regex_string = regex_string
        self.regex = re.compile(regex_string)

    def match_japanese(self, japanese: str):
        if '⌈' not in japanese:
            japanese = japanese.replace('{','').replace('}', '')
            japanese = japanese_to_compact_sentence(japanese)
        return _flatten_search_results(self.regex.search(japanese))
    
def _flatten_search_results(search):
    if not search: return None
    return compact_sentence_to_japanese(search.group(0), spaces=True)

def compile_matcher(matcher: str) -> Matcher:
    # Replace standalone "~" with with "[^⌈ˢᵖᵇʳ⌉]*".
    regex = matcher.replace('\n','').replace(' ', '')
    regex = regex.replace('{noun}', '(⌈ˢ~ᵖpron~⌉|⌈ˢ~ᵖnʳ~⌉⌈~ᵖsuffʳ~⌉|⌈~ᵖnʳ~⌉|⌈~ᵖn⌉)')
    regex = regex.replace("~", '[^⌉]*?')
    return Matcher(matcher, regex)
