import re
import unicodedata
from python.mecab.tagger import get_mecab_tagger

pos_map = {
    "名詞": "n",  # Noun
    "動詞": "v",  # Verb
    "形容詞": "adj",  # Adjective
    "副詞": "adv",  # Adverb
    "助詞": "prt",  # Particle
    "接続詞": "conj",  # Conjunction
    "感動詞": "int",  # Interjection
    "記号": "sym",  # Symbol
    "助動詞": "auxv",  # Auxiliary verb
    "補助記号": "auxs",  # Auxiliary symbol
    "代名詞": "pron",  # Pronoun
    "接頭辞": "pref",  # Prefix
    "接尾辞": "suff",  # Suffix
    "形状詞": "shp",  # Shape word
    "連体詞": "at",  # Attributive
    "空白": "sp",  # Space
}

pos_to_chars = {
    "prt": ['は', 'が', 'を', 'に', 'へ', 'と', 'で', 'か', 'の', 'ね', 'よ', 'て', 'わ', 'も', 'ぜ', 'ん', 'な', 'ば', 'ぞ', 'し', 'さ', 'や', 'ら', 'ど', 'い', 'つ', 'べ', 'け', 'ょ'],
    "sym": [], 
    "auxs": ['。', '、', '・', '：', '；', '？', '！', '…', '「', '」', '『', '』', '{', '}', '.', 'ー', ':', '?', 'っ', '-', '々', '(', ')', '[', ']', '<', '>', '／', '＼', '＊', '＋', '＝', '＠', '＃', '％', '＆', '＊', 'ぇ', '〇', '（', '）', '* ', '*', '～', '”', '◯'],
}

char_to_pos = {
    ch: pos
    for pos, chars in pos_to_chars.items()
    for ch in chars
}

class Token:
    def __init__(self, surface='', pos='', base_form='', grammar=None, start_pos=0, end_pos=0):
        self.surface = surface
        self.pos = pos
        self.base_form = base_form
        self.grammar = grammar if grammar is not None else []
        self.start_pos = start_pos
        self.end_pos = end_pos

    def add_grammar(self, grammar_point):
        if not isinstance(grammar_point, str):
            raise TypeError(f"grammar_point must be a string, but was {grammar_point}")
        if grammar_point not in self.grammar:
            self.grammar.append(grammar_point)

# Regex pattern to match bracketed tokens: ⌈ˢsurfaceᵖposᵇbase(ʳreading)?(ᵍgrammar…)*⌉
_TOKEN_PATTERN = re.compile(
    r'⌈'
    r'(?:ˢ(?P<surface>[^ˢᵖᵇʳᵍ⌉]+))?'
    r'(?:ᵖ(?P<pos>[^ˢᵖᵇʳᵍ⌉]+))?'
    r'(?:ᵇ(?P<base_form>[^ˢᵖᵇʳᵍ⌉]+))?'
    r'(?:ʳ(?P<reading>[^ˢᵖᵇʳᵍ⌉]+))?'
    r'(?P<grammars>(?:ᵍ[^ˢᵖᵇʳᵍ⌉]+)*)'
    r'⌉'
)

def compact_sentence_to_tokens(input_string):
    tokens = []
    last_end = 0
    for match in _TOKEN_PATTERN.finditer(input_string):
        if match.start() > last_end:
            for i, ch in enumerate(input_string[last_end:match.start()]):
                pos = char_to_pos.get(ch, '')
                tokens.append(Token(surface=ch, pos=pos, start_pos=last_end + i, end_pos=last_end + i + 1))
        surface = match.group('surface') or ''
        pos = match.group('pos') or ''
        base_form = match.group('base_form') or ''
        reading = match.group('reading') or ''
        grammars_raw = match.group('grammars') or ''
        grammars = re.findall(r'ᵍ([^ˢᵖᵇʳᵍ⌉]+)', grammars_raw)
        start_pos = match.start()
        end_pos = match.end()
        surface = surface.strip()
        pos = pos.strip()
        token = Token(surface=surface, pos=pos, base_form=base_form.strip(), grammar=[g.strip() for g in grammars], start_pos=start_pos, end_pos=end_pos)
        if reading:
            token.add_grammar(f"reading={reading.strip()}")
        tokens.append(token)
        last_end = match.end()
    if last_end < len(input_string):
        for i, ch in enumerate(input_string[last_end:]):
            pos = char_to_pos.get(ch, '')
            tokens.append(Token(surface=ch, pos=pos, start_pos=last_end + i, end_pos=last_end + i + 1))
    return tokens


def tokens_to_compact_sentence(tokens):
    result = ''
    for token in tokens:
        # If single-character prt, sym, or auxs, emit bare surface
        if token.pos in ['prt', 'sym', 'auxs'] and len(token.surface) == 1:
            result += token.surface
            continue
        if not (token.pos or token.base_form or token.grammar):
            result += token.surface
            continue
        result += '⌈'
        if token.surface:
            result += 'ˢ' + token.surface
        if token.pos:
            result += 'ᵖ' + token.pos
        if token.base_form and token.base_form != token.surface:
            result += 'ᵇ' + token.base_form
        reading_items = [g.split('=',1)[1] for g in token.grammar if g.startswith('reading=')]
        if reading_items:
            result += 'ʳ' + reading_items[0]
        for grammar in token.grammar:
            if not grammar.startswith('reading='):
                result += 'ᵍ' + grammar
        result += '⌉'
    return result


def tokens_to_japanese(tokens, spaces=False):
    if spaces:
        result = ''
        for token in tokens:
            if len(result) > 0:
                if token.surface not in pos_to_chars['auxs'] or token.surface == '{':
                    prior = result[-1]
                    if prior == '}':
                        result += ' '
                    elif prior not in pos_to_chars['auxs']:
                        result += ' '
            result += token.surface
        return result
    return ''.join(token.surface for token in tokens)


def compact_sentence_to_japanese(input_string, spaces=False):
    tokens = compact_sentence_to_tokens(input_string)
    return tokens_to_japanese(tokens, spaces=spaces)


def parse_raw_mecab_output(raw_output):
    tokens = []
    for line in raw_output.split("\n"):
        if line == "EOS":
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        surface = parts[0]
        features = parts[1].split(",")
        features += [""] * (20 - len(features) - 1)
        token = {
            "surface": surface,
            "pos": features[0],
            "pos_detail_1": features[1],
            "pos_detail_2": features[2],
            "pos_detail_3": features[3],
            "conjugated_type": features[4],
            "conjugated_form": features[5],
            "reading": features[6],
            "unknown_7": features[7],
            "unknown_8": features[8],
            "pronunciation": features[9],
            "basic_form": features[10],
            "unknown_11": features[11],
            "unknown_12": features[12],
            "unknown_13": features[13],
            "unknown_14": features[14],
            "unknown_15": features[15],
        }
        tokens.append(token)
    return tokens


def mecab_raw_to_compact_sentence(raw: str) -> str:
    tokens = parse_raw_mecab_output(raw)
    recombined = ""
    for token in tokens:
        surface = token["surface"]
        pos = token["pos"]
        pos_code = pos_map.get(pos, pos)
        if pos_code in ['prt', 'sym', 'auxs'] and len(surface) == 1:
            recombined += surface
        else:
            recombined += f"⌈ˢ{surface}ᵖ{pos_code}"
            base = token["basic_form"]
            if base and base != surface:
                recombined += f"ᵇ{base}"
            reading = token["reading"]
            if reading and reading != surface:
                recombined += f"ʳ{reading}"
            recombined += "⌉"
    return recombined


def mecab_raw_to_tokens(raw):
    return compact_sentence_to_tokens(mecab_raw_to_compact_sentence(raw))


def mecab_raw_to_compact_sentence_with_grammar(raw: str) -> str:
    tokens = parse_raw_mecab_output(raw)
    recombined = ""
    for token in tokens:
        surface = token["surface"]
        pos = token["pos"]
        recombined += f"⌈ˢ{surface}ᵖ{pos}"
        base = token["basic_form"]
        if base and base != surface:
            recombined += f"ᵇ{base}"
        for feature in [token["pos_detail_1"], token["pos_detail_2"], token["pos_detail_3"], token["conjugated_type"], token["conjugated_form"]]:
            if feature:
                recombined += f"ᵍ{feature}"
        recombined += "⌉"
    return recombined


def japanese_to_japanese_with_spaces(japanese: str) -> str:
    wakati = get_mecab_tagger()
    raw = wakati.parse(japanese)
    compact_sentence = mecab_raw_to_compact_sentence(raw)
    return compact_sentence_to_japanese(compact_sentence, spaces=True)


def mecab_raw_to_tokens_with_grammar(raw):
    return compact_sentence_to_tokens(mecab_raw_to_compact_sentence_with_grammar(raw))
