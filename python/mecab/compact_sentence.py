import json
from python.mecab.tagger import get_mecab_tagger
from dataclasses import dataclass

pos_map = {
    "名詞": "n",  # Noun
    "普通名詞": "cn",  # Common noun
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
}

pos1_map = {
    "括弧開": 'bracket_open',  # Opening bracket
    "括弧閉": 'bracket_close',  # Closing bracket
    "読点": 'comma',  # Comma
    "固有名詞": 'proper_noun',  # Proper noun
    "格助詞": 'case_particle',  # Case particle
    "普通名詞": 'common_noun',  # Common noun
    "準体助詞": 'pre_noun_particle',  # Pre-noun particle
    "終助詞": 'sentence_final_particle',  # Sentence-final particle
    "句点": 'period',  # Period
    "係助詞": 'binding_particle',  # Binding particle
    "非自立可能": 'non_self_reliant',  # Non-self-reliant
    "一般": 'general',  # General
    "助動詞語幹": 'auxiliary_verb_stem',  # Auxiliary verb stem
    "形容詞的": 'adjectival',  # Adjectival
    "副助詞": 'adverbial_particle',  # Adverbial particle
    "接続助詞": 'conjunctive_particle',  # Conjunctive particle
    "数詞": 'numeral',  # Numeral
    "名詞的": 'noun_like',  # Noun-like
    "フィラー": 'filler',  # Filler
    "形状詞的": 'shape_word_like',  # Shape word-like
    "タリ": 'tari',  # tari (a form of auxiliary verb)
    "動詞的": 'verb_like',  # Verb-like
    "": ''
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

@dataclass
class Token:
    surface: str
    pos: str = ''  # Part of speech, e.g., "n" for noun, "v" for verb
    base_form: str = ''
    reading: str = ''

    def to_dict(self):
        return {
            'surface': self.surface, 
            'pos': self.pos, 
            'base_form': self.base_form, 
            'reading': self.reading, 
            }

# Example input: ⌈ˢ今日ᵖnʳキョウ⌉は⌈ˢいいᵖadjʳヨイ⌉⌈ˢ天気ᵖnʳテンキ⌉⌈ˢですᵖauxvʳデス⌉ね。
def compact_sentence_to_tokens(compact_sentence: str) -> list[Token]:
    i = 0
    tokens = []
    state = 'normal'
    field_type = ''
    field_types_map = {
        'ˢ' : 'surface',
        'ᵖ' : 'pos',
        'ᵇ' : 'base_form',
        'ʳ' : 'reading'
    }
    field_types = field_types_map.keys()
    field_value = ''
    token_fields = {}

    def add_field():
        nonlocal field_value, field_type
        token_fields[field_type] = field_value
        field_type = ''
        field_value = ''
    
    def add_token():
        nonlocal token_fields, tokens, state
        if 'surface' not in token_fields:
            raise ValueError("Token must have a surface field")
        token = Token(
            surface=token_fields.get('surface', ''),
            pos=token_fields.get('pos', ''),
            base_form=token_fields.get('base_form', ''),
            reading=token_fields.get('reading', ''),
        )
        tokens.append(token)
        token_fields = {}
        state = 'normal'

    while i < len(compact_sentence):
        ch = compact_sentence[i]
    
        if state == 'normal':
            if ch == '⌈':
                state = 'in_token'
                token_fields = {}
            else:
                tokens.append(Token(surface=ch, pos=char_to_pos.get(ch, ''), base_form=ch, reading=ch))
            i += 1
        elif state == 'in_token':
            if ch in field_types:
                state = 'in_field'
                field_type = field_types_map[ch]
                field_value = ''
                i += 1
            else:
                raise ValueError(f"Expected field type but found '{ch}' at position {i}")
        elif state == 'in_field':
            if ch in field_types :
                add_field()
                state = 'in_token'
            elif ch == '⌉':
                add_field()
                add_token()
                state = 'normal'
                i += 1
            else:
                field_value += ch
                i += 1
                
        else:
            raise ValueError(f"Unexpected state '{state}'")
    return tokens


def tokens_to_compact_sentence(tokens):
    result = ''
    for token in tokens:
        # If single-character prt, sym, or auxs, emit bare surface
        if token.pos in ['prt', 'sym', 'auxs'] and len(token.surface) == 1:
            result += token.surface
            continue
        if not (token.pos or token.base_form):
            result += token.surface
            continue
        result += '⌈'
        if token.surface:
            result += 'ˢ' + token.surface
        if token.pos:
            result += 'ᵖ' + token.pos
        if token.base_form and token.base_form != token.surface:
            result += 'ᵇ' + token.base_form
        if token.reading and token.reading != token.surface:
            result += 'ʳ' + token.reading
        result += '⌉'
    return result

def tokens_to_japanese(tokens: list[Token], spaces=False) -> str:
    if spaces:
        result = ''
        for token in tokens:
            if (len(result) > 0 
                and last_token.surface != '{' 
                and (token.pos != 'auxs' or token.surface == '{') 
                and (last_token.pos != 'auxs' or last_token.surface == '}')):
                result += ' '
            result += token.surface
            last_token = token
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
        }
        def add(field, value):
            if value == '""':
                return
            if value == "":
                return
            token[field] = value
        add("pos", pos_map[features[0]])
        add("pos_detail_1", pos1_map[features[1]])
        add("pos_detail_2", features[2])
        add("pos_detail_3", features[3])
        add("conjugated_type", features[4])
        add("conjugated_form", features[5])
        add("reading", features[6])
        add("unknown_7", features[7])
        add("unknown_8", features[8])
        add("pronunciation", features[9])
        add("basic_form", features[10])
        add("unknown_11", features[11])
        add("unknown_12", features[12])
        add("unknown_13", features[13])
        add("unknown_14", features[14])
        add("unknown_15", features[15])
        tokens.append(token)
    return tokens

def raw_tokens_to_compact_sentence(tokens: list[dict]) -> str:
    recombined = ""
    for token in tokens:
        surface = token["surface"]
        pos = token["pos"]
        pos_code = pos_map.get(pos, pos)
        if pos_code in ['prt', 'sym', 'auxs'] and len(surface) == 1:
            recombined += surface
        else:
            recombined += f"⌈ˢ{surface}ᵖ{pos_code}"
            base = token.get("basic_form", None)
            if base and base != surface:
                recombined += f"ᵇ{base}"
            reading = token.get("reading", None)
            if reading and reading != surface:
                recombined += f"ʳ{reading}"
            recombined += "⌉"
    return recombined

def mecab_raw_to_compact_sentence(raw: str) -> str:
    tokens = parse_raw_mecab_output(raw)
    return raw_tokens_to_compact_sentence(tokens)

def mecab_raw_to_tokens(raw):
    return compact_sentence_to_tokens(mecab_raw_to_compact_sentence(raw))

def japanese_to_japanese_with_spaces(japanese: str) -> str:
    wakati = get_mecab_tagger()
    try:
        # Fix for special case seen
        japanese = japanese.replace(' っ', 'っ').replace('っ ', 'っ')
        raw = wakati.parse(japanese)
        compact_sentence = mecab_raw_to_compact_sentence(raw)
        result = compact_sentence_to_japanese(compact_sentence, spaces=True)

        # # Round trip check
        # reconstructed = wakati.parse(result)
        # reconstructed_compact_sentence = mecab_raw_to_compact_sentence(reconstructed)
        # if compact_sentence != reconstructed_compact_sentence:
        #     raise ValueError(f"Reconstructed compact sentence does not match original\n{japanese}=>{compact_sentence}\n{result}=>{reconstructed_compact_sentence}")

        return result
    except Exception as e:
        raise Exception(f"Failed to convert Japanese '{japanese}' to spaced Japanese: {e}")

def japanese_to_tokens(japanese: str) -> list[Token]:
    wakati = get_mecab_tagger()
    raw = wakati.parse(japanese)
    return parse_raw_mecab_output(raw)

