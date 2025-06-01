import re

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

# Regex pattern to match bracketed tokens: ⌈ˢsurfaceᵖposᵇbase(ᵍgrammar…)*⌉
_TOKEN_PATTERN = re.compile(
    r'⌈'
    r'(?:ˢ(?P<surface>[^ˢᵖᵇᵍ⌉]+))?'
    r'(?:ᵖ(?P<pos>[^ˢᵖᵇᵍ⌉]+))?'
    r'(?:ᵇ(?P<base_form>[^ˢᵖᵇᵍ⌉]+))?'
    r'(?P<grammars>(?:ᵍ[^ˢᵖᵇᵍ⌉]+)*)'
    r'⌉'
)

def compact_sentence_to_tokens(input_string):
    """
    Parses a compact sentence (mix of bracketed and single-character tokens) into a list of Token objects.

    Bracketed segments (⌈…⌉) are parsed for surface, pos, base_form, and grammars.
    Unbracketed characters (e.g., particles, punctuation) are each treated as a Token with only surface filled.

    Returns:
        list[Token]: All tokens in order.
    """
    tokens = []
    last_end = 0
    for match in _TOKEN_PATTERN.finditer(input_string):
        # Handle any single-character tokens between last_end and match.start()
        if match.start() > last_end:
            for i, ch in enumerate(input_string[last_end:match.start()]):
                tokens.append(Token(surface=ch, start_pos=last_end + i, end_pos=last_end + i + 1))
        # Extract bracketed token
        surface = match.group('surface') or ''
        pos = match.group('pos') or ''
        base_form = match.group('base_form') or ''
        grammars_raw = match.group('grammars') or ''
        grammars = re.findall(r'ᵍ([^ˢᵖᵇᵍ⌉]+)', grammars_raw)
        start_pos = match.start()
        end_pos = match.end()
        tokens.append(Token(surface=surface.strip(), pos=pos.strip(), base_form=base_form.strip(), grammar=[g.strip() for g in grammars], start_pos=start_pos, end_pos=end_pos))
        last_end = match.end()
    # Handle any trailing single-character tokens
    if last_end < len(input_string):
        for i, ch in enumerate(input_string[last_end:]):
            tokens.append(Token(surface=ch, start_pos=last_end + i, end_pos=last_end + i + 1))
    return tokens


def tokens_to_compact_sentence(tokens):
    """
    Converts a list of Token objects back into a compact sentence string.

    - Tokens with only surface (no pos, no base_form, no grammar) are output as their surface character.
    - Otherwise, tokens are bracketed with ⌈…⌉ including ˢ, ᵖ, ᵇ, ᵍ delimiters.
    """
    result = ''
    for token in tokens:
        # If no pos, base_form, and no grammars, output surface directly
        if not token.pos and not token.base_form and not token.grammar:
            result += token.surface
            continue
        result += '⌈'
        if token.surface:
            result += 'ˢ' + token.surface
        if token.pos:
            result += 'ᵖ' + token.pos
        if token.base_form:
            result += 'ᵇ' + token.base_form
        for grammar in token.grammar:
            result += 'ᵍ' + grammar
        result += '⌉'
    return result


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
    """
    Converts MeCab raw token output into a compact sentence format.
    
    Each MeCab token is either output as a bracketed segment or as a single character:
      - Content words (surface != base or reading present) become bracketed: ⌈ˢsurfaceᵖposᵇbaseʳreading⌉
      - Particles/single-character symbols become unbracketed.
    """
    tokens = parse_raw_mecab_output(raw)
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
    recombined = ""
    for token in tokens:
        surface = token["surface"]
        pos = token["pos"]
        pos_code = pos_map.get(pos, pos)
        # If particle or symbol (prt or sym) and single char, output directly
        if pos_code in ['prt', 'sym'] and len(surface) == 1:
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
    """
    Converts MeCab raw token output into a compact sentence format with grammar attributes.
    """
    tokens = parse_raw_mecab_output(raw)
    recombined = ""
    for token in tokens:
        surface = token["surface"]
        pos = token["pos"]
        recombined += f"⌈ˢ{surface}ᵖ{pos}"
        base = token["basic_form"]
        if base:
            recombined += f"ᵇ{base}"
        for feature in [token["pos_detail_1"], token["pos_detail_2"], token["pos_detail_3"], token["conjugated_type"], token["conjugated_form"]]:
            if feature:
                recombined += f"ᵍ{feature}"
        recombined += "⌉"
    return recombined


def mecab_raw_to_tokens_with_grammar(raw):
    return compact_sentence_to_tokens(mecab_raw_to_compact_sentence_with_grammar(raw))
