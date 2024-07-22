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

def sentence_to_tokens(input_string):
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

def tokens_to_sentence(tokens):
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
