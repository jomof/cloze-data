import json
import sys
import MeCab
import unidic
import re
from typing import List, Dict
import re

pattern_classifiers = {
    "と|いう|の|は": "というのはx",
    "と|いう|と": "というと",
    "という": "という",
    "て|も|かまい|ませ|ん": "てもかまわない/てもかまいません",
    "て|も|かまわ|ない": "てもかまわない/てもかまいません",
    "て|初めて": "て初めて",
    "て|ごらん": "てごらん",
    "つまり": "つまり",
    ".*っぽい": "っぽい",
    ".*っぱなし": "っぱなし",
    ".*っけ": "っけ",
    "ついで|に": "ついでに",
    "だらけ": "だらけx",
    "たら|いい": "たらいい/といいx",
    "と|いい": "たらいい/といいx",
    "ため|に": "ためにx",
    "たび|に": "たびに",
    "た|とたん": "たとたん",
    "たとえば": "たとえば",
    "たとえ|○○|て|も": "たとえ○○ても",
    "確か|に": "確かに",
    "だ|けど": "だけど",
    "た|結果": "た結果/の結果",
    "の|結果": "た結果/の結果",
    "その|結果": "その結果",
    "そう|も|ない": "そうもない",
    "せい|で": "せいで",
    "ず|に|は|い|られ|なかっ|た": "ずにはいられない",
    "ず|に|は|い|られ|ない": "ずにはいられない",
    "ず|に": "ずに",
    "しか|ない": "しかない",
    "さえ|○○|ば": "さえ○○ば/さえすれば/さえいれば",
    "さえ": "さえ",
    "こと|は|ない": "ことはない",
    "こと|に": "ことに",
    "こと|だ": "ことだ",
    "こと|か": "ことか",
    "こそ": "こそ",
    "決して|○○|ない": "決して○○ない",
    "くせ|に": "くせに",
    ".*切れ|ない": "切れない",
    "きり": "きり",
    "気味": "ぎみ",
    "代わり|に": "代わりに",
    "がち": "がち",
    "がたい": "がたい",
    "かけ": "かけ",
    "おそらく": "おそらく",
    "おかげ|で": "おかげで",
    "うち|に": "うちに",
    "一方|で": "一方で",
    "一方|だ": "一方だ",
    "いくら|○○|て|も": "いくら○○ても/いくら○○でも",
    "いくら|○○|で|も": "いくら○○ても/いくら○○でも",
    "あまりに": "あまりに",
    "あまり": "あまり",
    ".*らしい": "らしい",
    "より": "より",
    "予定|です": "よていだ",
    "予定|だ": "よていだ",
    "よう|に": "ように/ような",
    "よう|な": "ように/ような",
    ".*よ|う|と|思う": "ようと思う",
    "よう|だ": "ようだ",
    "やすい": "やすい",
    "みたい|に": "みたいに/みたいな",
    "みたい|な": "みたいに/みたいな",
    "みたい": "みたい",
    "まで|に": "までに",
    "ほしい": "ほしい",
    "必要": "必要",
    "はず|だ": "はずだ",
    "はず|が|ない": "はずがない",
    "ばかり": "ばかりx",
    "場合|は": "場合は",
    "ば": "ば",
    ".*の|よう|に": "のように/のような",
    ".*の|よう|な": "のように/のような",
    "のに": "のにx",
    "の|中|で": "の中で",
    "にくい": "にくい",
    "なら": "なら",
    "など": "など",
    "なさい": "なさい",
    "なけれ|ば|いけ|ない": "なければいけない/なければならない",
    "なけれ|ば|なら|ない": "なければいけない/なければならない",
    "なく|て|も|いい": "なくてもいい",
    "なく|て|は|いけ|ない": "なくてはいけない/なくてはならない",
    "なく|て|は|なら|ない": "なくてはいけない/なくてはならない",
    "ながら": "ながら",
    "ない|で": "ないで",
    "ところ": "ところ",
    "とき": "とき",
    "とか|○○|とか": "とか○○とか",
    "という|こと": "ということ",
    "て|よかっ|た": "てよかった",
    "て|ほしい": "てほしい",
    "て|すみません": "てすみません",
    "ちゃう": "てしまう/ちゃう",
    "で|ござい|ます": "でございます",
    "て|おく": "ておく/とく",
    "て|いる|ところ": "ているところ",
    "て|い|た|だけ|ませ|ん|か": "ていただけませんか",
    "たり|○○|たり": "たり○○たり",
    "たら|どう": "たらどう",
    "たら": "たら",
    "た|ばかり": "たばかり",
    "た|ところ": "たところ",
    "だけ|で": "だけで",
    "そんなに": "そんなに",
    "それでも": "それでも",
    "そう|に": "そうに/そうな",
    "そう|な": "そうに/そうな",
    "そう|だ": "そうだx",
    "ぜんぜん": "ぜんぜん",
    "じゃ|ない|か": "じゃないか",
    "しか|○○|ない": "しか○○ない",
    "こと": "こと",
    "急|に": "急に",
    "かも|しれ|ない": "かもしれない",
    "か|な": "かな",
    "か|どう|か": "かどうか",
    "の|.*方": "方",
    "かしら": "かしら",
    "おき|に": "おきに",
    "お.*|に|なる": "お○○になる",
    "お.*|に|なり": "お○○になる",
    "お|○○|ください": "お○○ください",
    "あまり|○○|ない": "あまり○○ない",
    "後で": "後で",
    "くらい": "くらい/ぐらい",
    "ぐらい": "くらい/ぐらい",
    "て|は|いけ|ませ|ん": "てはいけない",
    "ついては|いけ|ませ|ん": "てはいけない",
    "て|は|いけ|ない": "てはいけない",
    "で|は|いけ|ない": "てはいけない",
    "て|も|いい": "てもいい",
    "で|も|いい": "てもいい",
    "と": "とx",
    "ない|で|ください": "ないでください",
    "に": ["に", "に/へ"],
    "へ": ["へ", "に/へ"],
    "の": "のx",
    "の|が|下手": "のが下手",
    "の|が|上手": "のが上手",
    "の|が|好き": "のが好き",
    "ので": "ので",
    "は": "は",
    "ほう|が|いい": "ほうがいいx",
    "前|に": "前に",
    "まだ": "まだ",
    "まで": "まで",
    "も": "も",
    "もう": "もう",
    "や": "や",
    "より|○○|の|ほう|が|○○": "より○○のほうが○○",
    "より|○○|ほう|が|○○": "より○○のほうが○○",
}


def get_compiled_pattern_classifiers():
    compiled_pattern_classifiers = []
    for pattern, gp in pattern_classifiers.items():
        parts = pattern.split("|")
        matcher = "".join(f"⌈ₛ{part}ₚ[^⌉]*⌉" for part in parts)
        grammar_points = gp
        if isinstance(grammar_points, str):
            grammar_points = [gp]
        for grammar_point in grammar_points:
            compiled_pattern_classifiers.append([grammar_point, re.compile(matcher, flags=0)])
    return compiled_pattern_classifiers


compiled_pattern_classifiers = get_compiled_pattern_classifiers()


class Token:
    def __init__(self, surface, pos, grammar, start_pos, end_pos):
        self.surface = surface
        self.pos = pos
        self.grammar = grammar
        self.start_pos = start_pos
        self.end_pos = end_pos

    def add_grammar(self, grammar_point):
        if not isinstance(grammar_point, str):
            raise TypeError(f"grammar_point must be a string, but was {grammar_point}")
        if grammar_point not in self.grammar:
            self.grammar.append(grammar_point)

def sentence_to_tokens(input_string):
    """
    Parses a tokenized sentence string into a list of Token objects.

    Each token starts with "⌈" and ends with "⌉". Within each token:
    - The text after "ₛ" is the surface form.
    - The text after "ₚ" is the part-of-speech (POS).
    - The text after "ₔ" represents grammar attributes, and there can be zero or more grammar attributes.

    The function also captures the starting and ending positions of each token within the original string.

    Parameters:
    input_string (str): The tokenized sentence string.

    Returns:
    list: A list of Token objects.
    """
    tokens = []
    i = 0
    length = len(input_string)

    while i < length:
        if input_string[i] == '⌈':
            # Start of a token
            start_pos = i
            i += 1
            surface = ''
            pos = ''
            grammars = []

            # Find the end of the surface part
            while i < length and input_string[i] != 'ₛ':
                i += 1
            i += 1  # Skip 'ₛ'

            # Read the surface form of the token
            while i < length and input_string[i] != 'ₚ':
                surface += input_string[i]
                i += 1
            i += 1  # Skip 'ₚ'

            # Read the part-of-speech tag of the token
            while i < length and input_string[i] not in ('ₔ', '⌉'):
                pos += input_string[i]
                i += 1

            # Read the grammar attributes (if any)
            while i < length and input_string[i] == 'ₔ':
                i += 1  # Skip 'ₔ'
                grammar = ''
                while i < length and input_string[i] not in ('ₔ', '⌉'):
                    grammar += input_string[i]
                    i += 1
                grammars.append(grammar.strip())

            # If the token ends with '⌉', finalize the token and add it to the list
            if i < length and input_string[i] == '⌉':
                end_pos = i + 1
                tokens.append(Token(surface.strip(), pos.strip(), grammars, start_pos, end_pos))
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
        # Start the token with '⌈ₛ'
        result += '⌈ₛ' + token.surface + 'ₚ' + token.pos

        # Add each grammar attribute with the 'ₔ' delimiter
        for grammar in token.grammar:
            result += 'ₔ' + grammar

        # Close the token with '⌉'
        result += '⌉'

    return result

def annotate_with_grammar(sentence):
    result = sentence
    for grammar_point, pattern in compiled_pattern_classifiers:
        match = pattern.search(result)
        if match:
            start = match.start()
            end = match.end()
            tokens = sentence_to_tokens(result)
            for token in tokens:
                if token.start_pos >= start and token.end_pos <= end:
                    token.add_grammar(grammar_point)
            result = tokens_to_sentence(tokens)
    return result

def parse_mecab_output(tokens: str) -> List[Dict[str, str]]:
    fields = ["POS", "Subcategory1", "Subcategory2", "Subcategory3",
              "ConjugationType", "ConjugationForm", "BaseForm", "Reading", "Pronunciation"]

    result = []

    # Split the input by lines
    lines = tokens.strip().split('\n')
    
    # Iterate over each line and parse the token details
    for line in lines:
        if line == "EOS":
            continue
        parts = line.split('\t')
        surface = parts[0]
        details = parts[1].split(',')

        # Create a dictionary for each token
        token_dict = {field: (details[i - 1] if i - 1 < len(details) else "") 
                      for i, field in enumerate(fields, 1)}
        token_dict["Surface"] = surface
        
        result.append(token_dict)

    recombined = ""
    for token in result:
        surface = token["Surface"] # Preceded by ₛ (Latin Subscript Small Letter 's')
        pos = token["POS"] # Preceded by ₚ (Latin Subscript Small Letter 'p')
                        
        recombined += f"⌈ₛ{surface}ₚ{pos}⌉"

    return recombined

def add_empty_tokens_field(input_file: str, output_file: str):
    wakati = MeCab.Tagger('-d "{}"'.format(unidic.DICDIR))

    # Read the JSON data from the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Add an empty "Tokens" field to each record
    for record in data:
        mecab = wakati.parse(record["Japanese"]).replace('"', "'").replace("'',", ",")
        #record["Mecab"] = mecab
        record["Tokens"] = annotate_with_grammar(parse_mecab_output(mecab))

    # Write the updated data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_tokens_field():
    if len(sys.argv) != 3:
        print("Usage: python add_tokens_field.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    add_empty_tokens_field(input_file, output_file)

if __name__ == '__main__':
    add_tokens_field()
