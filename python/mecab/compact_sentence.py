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

def read_until_delimiter(input_string, i, delimiters):
    result = ''
    while i < len(input_string) and input_string[i] not in delimiters:
        result += input_string[i]
        i += 1
    return result, i

def compact_sentence_to_tokens(input_string):
    """
    Parses a tokenized sentence string into a list of Token objects.

    Each token starts with "⌈" and ends with "⌉". Within each token:
    - The text after "ˢ" is the surface form.
    - The text after "ᵖ" is the part-of-speech (POS).
    - The text after "ᵇ" is the base form.
    - The text after "ᵍ" represents grammar attributes, and there can be zero or more grammar attributes.

    The function also captures the starting and ending positions of each token within the original string.

    Parameters:
    input_string (str): The tokenized sentence string.

    Returns:
    list: A list of Token objects.
    """
    tokens = []
    i = 0
    length = len(input_string)
    delimiters = ('ˢ', 'ᵖ', 'ᵇ', 'ᵍ', '⌉')

    while i < length:
        if input_string[i] == '⌈':
            # Start of a token
            start_pos = i
            i += 1
            surface = ''
            pos = ''
            base_form = ''
            grammars = []

            while i < length and input_string[i] != '⌉':
                if input_string[i] == 'ˢ':
                    i += 1
                    surface, i = read_until_delimiter(input_string, i, delimiters)
                elif input_string[i] == 'ᵖ':
                    i += 1
                    pos, i = read_until_delimiter(input_string, i, delimiters)
                elif input_string[i] == 'ᵇ':
                    i += 1
                    base_form, i = read_until_delimiter(input_string, i, delimiters)
                elif input_string[i] == 'ᵍ':
                    i += 1
                    grammar, i = read_until_delimiter(input_string, i, delimiters)
                    grammars.append(grammar.strip())
                else:
                    i += 1

            if i < length and input_string[i] == '⌉':
                end_pos = i + 1
                tokens.append(Token(surface.strip(), pos.strip(), base_form.strip(), grammars, start_pos, end_pos))
                i += 1  # Skip '⌉'
        else:
            i += 1  # Move to next character if not the start of a token

    return tokens

def tokens_to_compact_sentence(tokens):
    """
    Converts a list of Token objects back into the original tokenized string format.

    Each token is represented by a Token object.

    The function reconstructs the string by concatenating each token's components
    with the appropriate delimiters.

    Parameters:
    tokens (list): A list of Token objects.

    Returns:
    str: The reconstructed tokenized string.
    """
    result = ''

    for token in tokens:
        # Start the token with '⌈'
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
    
    Parameters:
    raw (str): Raw output from MeCab, with each token on a new line and fields separated by tabs and commas.
    
    Returns:
    str: A compact sentence string with each token enclosed in brackets and annotated with part-of-speech (POS) and base form.
    """
    # Define the fields present in the MeCab output details

    tokens = parse_raw_mecab_output(raw)

    pos_map = {
        "名詞": "n", # Noun 
        "動詞": "v", # Verb
        "形容詞": "adj", # Adjective
        "副詞": "adv", # Adverb
        "助詞": "prt", # Particle
        "接続詞": "conj", # Conjunction
        "感動詞": "int", # Interjection
        "記号": "sym", # Symbol
        "助動詞": "auxv", # Auxiliary verb
        "補助記号": "auxs", # Auxiliary symbol
        "代名詞": "pron", # Pronoun
        "接頭辞": "pref", # Prefix
        "接尾辞": "suff", # Suffix
        "形状詞": "shp", # Shape word
        "連体詞": "at", # Attributive
        "空白": "sp", # Space
    }

    # Recombine the tokens into the desired compact format
    recombined = ""
    for token in tokens:
        surface = token["surface"]  # Preceded by ˢ (Latin Subscript Small Letter 's')
        pos = token["pos"]  # Preceded by ᵖ (Latin Subscript Small Letter 'p')
        pos_code = pos_map[pos]
        if pos_code in ['auxs', 'prt'] and len(surface) == 1:
            # Shortened versions for symbols and other things that can be determined
            # with a lookup table.
            recombined += surface
        else:
            recombined += f"⌈ˢ{surface}ᵖ{pos_code}"
            base = token["basic_form"]  # Preceded by ᵇ (superscript 'b')
            if base and base != surface:  # Only include base form if it's different from surface
                recombined += f"ᵇ{base}"
            reading = token["reading"]  # Preceded by ʳ (superscript 'r')
            if reading and reading != surface:
                recombined += f"ʳ{reading}"
            recombined += "⌉"

    return recombined

def mecab_raw_to_tokens(raw):
    return compact_sentence_to_tokens(mecab_raw_to_compact_sentence(raw))

def mecab_raw_to_compact_sentence_with_grammar(raw: str) -> str:
    """
    Converts MeCab raw token output into a compact sentence format, including grammar information.
    
    Parameters:
    raw (str): Raw output from MeCab, with each token on a new line and fields separated by tabs and commas.
    
    Returns:
    str: A compact sentence string with each token enclosed in brackets and annotated with 
         part-of-speech (POS), base form, and grammar information.
    """
    tokens = parse_raw_mecab_output(raw)

    recombined = ""
    for token in tokens:
        surface = token["surface"]  # Preceded by ˢ (Latin Subscript Small Letter 's')
        pos = token["pos"]  # Preceded by ᵖ (Latin Subscript Small Letter 'p')
        recombined += f"⌈ˢ{surface}ᵖ{pos}"
        base = token["basic_form"]  # Preceded by ᵇ (superscript 'b')
        if base:
            recombined += f"ᵇ{base}"
        # Add grammar features (using fields 1-4, 6, and 7)
        for feature in [token["pos_detail_1"], token["pos_detail_2"], token["pos_detail_3"], 
                         token["conjugated_type"], token["conjugated_form"]]:
            if feature:
                recombined += f"ᵍ{feature}"
        recombined += "⌉"

    return recombined

def mecab_raw_to_tokens_with_grammar(raw):
    return compact_sentence_to_tokens(mecab_raw_to_compact_sentence_with_grammar(raw))