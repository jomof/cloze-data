import json
import sys
import MeCab
import unidic
import re
from typing import List, Dict
import re
from mecab.compact_sentence import Token, sentence_to_tokens, tokens_to_sentence


pattern_classifiers = {
    "を|禁じえ|な": "を禁じえない",
    "を|もの|と|も|せ|ず": "をものともせず",
    "を|もっ|て": "をもって",
    "を|おい|て": "をおいて",
    "を|余儀|なく|さ|れ|た": "を余儀なくされる",
    "を|余儀|なく|さ|れ|る": "を余儀なくされる",
    "を|よそ|に": "をよそに",
    "思い|を|し": "思いをする",
    "思い|を|する": "思いをする",
    "折|に": "折に",
    "およそ": "およそ",
    "さも|ない|と": "さもないと",
    "さぞ": "さぞ",
    "始末|だ": "始末だ",
    "そば|から": "そばから",
    "さも": "さも",
    "それ|なり|に": "それなりに",
    "そう|に|も|ない": "そうにもない",
    "ただ|○○|のみ|だ": "ただ○○のみだ",
    "だ|拍子|に": "た拍子に",
    "た|拍子|に": "た拍子に",
    "ためし|が|ない": "ためしがない",
    "たり|とも": "たりとも",
    "た|瞬間|に": "た瞬間に",
    "てっ|きり": "てっきり",
    "た|ところ|で": "たところで",
    "て|から|と|いう|もの": "てからというもの",
    "て|かなわ|ない": "てかなわない",
    "て|まで": "てまで",
    "て|みせる": "てみせる",
    "て|も|どう|に|も|なら|ない": "てもどうにもならない",
    "て|も|始まら|ない": "ても始まらない",
    "て|も|差し支え|ない": "ても差し支えない",
    "て|しかる|べき|だ": "てしかるべきだ",
    "って|ば": "ってば",
    "て|やま|ない": "てやまない",
    "も|相|まっ|て": "と相まって",
    "と|○○|が|相|まっ|て": "と相まって",
    "と|相|まっ|て": "と相まって",
    "と|あれ|ば": "とあれば",
    "と|あっ|て": "とあって",
    "と|ばかり|に": "とばかりに",
    "と|いえ|ど|も": "といえども",
    "と|いい|○○|と|いい": "といい○○といい",
    "と|いっ|たら|ない": "といったらない",
    "と|いう|か|○○|と|いう|か": "というか○○というか",
    "と|いう|ところ|だ": "というところだ/といったところだ",
    "と|いっ|た|ところ|だ": "というところだ/といったところだ",
    "と|いう|もの": "というもの",
    "と|いう|わけ|です": "というわけだ",
    "と|いう|わけ|だ": "というわけだ",
    "と|いう|わけ|で|は|ない": "というわけではない",
    "と|いわ|ず": "といわず",
    "と|き|たら": "ときたら",
    "と|き|て|いる": "ときている",
    "ところ|が|ある": "ところがある",
    "ところ|から": "ところから",
    "と|み|られる": "とみられる",
    "と|見る|や": "と見るや",
    "と|も|なく": "ともなく",
    "と|も|なる|と": "ともなると/ともなれば",
    "と|も|なれ|ば": "ともなると/ともなれば",
    "と|も|すれ|ば": "ともすれば",
    "と|思い|き|や": "と思いきや",
    "とりわけ": "とりわけ",
    "と|さ|れ|て": "とされる",
    "と|さ|れる": "とされる",
    "とっさ|に": "とっさに",
    "と|し|た|ところ|で": "としたって/としたところで",
    "と|し|たって": "としたって/としたところで",
    "と|し|て|○○|ない": "として○○ない",
    "とて": "とて",
    "とても|○○|ない": "とても○○ない",
    "と|は": "とは",
    "と|は|いえ": "とはいえ",
    "と|は|いう|もの|の": "とはいうものの",
    "つ|○○|つ": "つ○○つ",
    "は|おろか": "はおろか",
    "は|さておき": "はさておき",
    "や|否|や": " や否や",
    "や|し|ない": "やしない",
    ".*う|と": "(よ)うが/(よ)うと",
    ".*う|が": "(よ)うが/(よ)うと",
    ".*う|が|○○|まい|が": "(よ)うが○○まいが/(よ)うと○○まいと",
    ".*う|と|○○|まい|と": "(よ)うが○○まいが/(よ)うと○○まいと",
    ".*う|か|○○|まい|か": "(よ)うか○○まいか",
    ".*う|もの|なら": "(よ)うものなら",
    ".*う|に|も|○○|ない": "(よ)うにも○○ない",
    ".*よう|に|よっ|て|は": "ようによっては",
    "ゆえ|に": "ゆえに",
    "ざる": "ざる",
    "ず|じまい": "ずじまい",
    "ずくめ": "ずくめ",
    "ず|と|も": "ずとも",
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
        parts = [".*" if element == '○○' else element for element in parts]
        matcher = "".join(f"⌈ˢ{part}ᵖ[^⌉]*⌉" for part in parts)
        grammar_points = gp
        if isinstance(grammar_points, str):
            grammar_points = [gp]
        for grammar_point in grammar_points:
            compiled_pattern_classifiers.append([grammar_point, re.compile(matcher, flags=0)])
    return compiled_pattern_classifiers


compiled_pattern_classifiers = get_compiled_pattern_classifiers()

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
        surface = token["Surface"] # Preceded by ˢ (Latin Subscript Small Letter 's')
        pos = token["POS"] # Preceded by ᵖ (Latin Subscript Small Letter 'p')
        recombined += f"⌈ˢ{surface}ᵖ{pos}"
        base = token["BaseForm"] # Preceded by ᵇ (superscript 'b') 
        if base is not None and base != "":
            recombined += f"ᵇ{base}"
        recombined += "⌉"

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
        print("Usage: python tokenize_sentences.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    add_empty_tokens_field(input_file, output_file)

if __name__ == '__main__':
    add_tokens_field()
