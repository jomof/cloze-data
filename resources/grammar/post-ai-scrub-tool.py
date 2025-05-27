import json
import yaml
import sys
import re
from python.mecab.compact_sentence import compact_sentence_to_tokens, tokens_to_compact_sentence, mecab_raw_to_compact_sentence, parse_raw_mecab_output
from python.mecab.tagger import get_mecab_tagger

# Example of input json structure:
# {
#     "grammar_point": "だ",
#     "id": "gp0001",
#     "rank": 0,
#     "conjugations": [
#         {
#             "type": "plain present affirmative",
#             "form": "だ",
#             "rarity": "common"
#         },
#         {
#             "type": "plain past affirmative",
#             "form": "だった",
#             "rarity": "common"
#         },
#         {
#             "type": "plain present negative",
#             "form": "ではない",
#             "rarity": "common"
#         },
#         {
#             "type": "plain past negative",
#             "form": "ではなかった",
#             "rarity": "common"
#         },
#         {
#             "type": "polite present affirmative",
#             "form": "です",
#             "rarity": "common"
#         },
#         {
#             "type": "polite past affirmative",
#             "form": "でした",
#             "rarity": "common"
#         },
#         {
#             "type": "polite present negative",
#             "form": "ではありません",
#             "rarity": "common"
#         },
#         {
#             "type": "polite past negative",
#             "form": "ではありませんでした",
#             "rarity": "common"
#         },
#         {
#             "type": "formal/literary present affirmative",
#             "form": "である",
#             "rarity": "common"
#         },
#         {
#             "type": "formal/literary past affirmative",
#             "form": "であった",
#             "rarity": "uncommon"
#         },
#         {
#             "type": "formal/literary present negative",
#             "form": "ではない",
#             "rarity": "common"
#         },
#         {
#             "type": "formal/literary past negative",
#             "form": "ではなかった",
#             "rarity": "uncommon"
#         }
#     ],
#     "jlpt": "N5",
#     "pronunciation": {
#         "katakana": "ダ",
#         "romaji": "da"
#     },
#     "formation": {
#         "[Noun] + だ": "Indicates a state of being or identity in casual speech.",
#         "[な-Adjective stem] + だ": "Links a な-adjective to the subject in casual speech."
#     },
#     "meaning": "To be, is",
#     "meaning_warning": "だ cannot be used directly with い-adjectives. Use です instead.",
#     "details": {
#         "Part of Speech": "Auxiliary verb (助動詞)",
#         "Register": "Casual, standard",
#         "品詞": "助動詞",
#         "単語の種類": "付属語",
#         "使用域": "一般"
#     },
#     "etymology": "The copula 「だ」 originates from the classical Japanese auxiliary verb 「なり」 (nari), which indicated existence or assertion. Over time, 「なり」 evolved into 「にあり」 (ni ari), then contracted to 「である」 (de aru), and eventually simplified to the modern 「だ」. This evolution reflects a shift from a broader sense of existence to a more direct assertion of identity or state.",
#     "writeup": "The grammar point 「だ」 is essentially the casual form of \"to be\" or \"is\" in Japanese. It's used to express a state of being, assert identity, or make definitive statements. Think of it as the backbone for simple sentences that describe what something *is*. It is primarily used in casual speech and writing. \n\nTechnically, 「だ」 is an auxiliary verb (助動詞), attaching itself to nouns and na-adjectives to give them meaning. \n\n*   **Important Considerations**\n    *   While often referred to as the casual form of 「です」, understand that 「です」 is simply a polite form. The more formal equivalent of 「だ」 is 「である」, often found in formal writing and articles.\n    *   You *cannot* directly attach 「だ」 to い-adjectives. Use 「です」 instead.",
#     "examples": [
#         {
#             "japanese": "私**だ**。",
#             "english": "It is me.",
#             "conjugation": "plain present affirmative",
#             "register": "casual",
#             "setting": "informative",
#             "nuance": "This is a simple statement of identity, typically used in casual conversation."
#         },
#         {
#             "japanese": "猫**だ**。",
#             "english": "(It) is a cat.",
#             "conjugation": "plain present affirmative",
#             "register": "casual",
#             "setting": "informative",
#             "nuance": "A straightforward statement identifying something as a cat."
#         },
#         {
#             "japanese": "学生**だ**。",
#             "english": "(I) am a student.",
#             "conjugation": "plain present affirmative",
#             "register": "casual",
#             "setting": "informative",
#             "nuance": "Declares one's status as a student. Common in self-introductions among peers."
#         },
#         {
#             "japanese": "明日晴れ**だ**。",
#             "english": "It's going to be sunny tomorrow.",
#             "conjugation": "plain present affirmative",
#             "register": "casual",
#             "setting": "informative",
#             "nuance": "States that the weather tomorrow will be sunny. Used among friends or family.",
#             "etymology": "「晴れ」 means sunny."
#         },
#         {
#             "japanese": "静か**だ**ね。",
#             "english": "It's quiet, isn't it?",
#             "conjugation": "plain present affirmative",
#             "register": "casual",
#             "setting": "reflective",
#             "nuance": "Expresses a casual observation that it's quiet. The 「ね」 particle seeks confirmation or agreement.",
#             "speaker_gender": "female",
#             "listener_gender": "male"
#         },
#         {
#             "japanese": "君は特別**だ**よ。",
#             "english": "You're special, you know.",
#             "conjugation": "plain present affirmative",
#             "register": "casual",
#             "setting": "flirty",
#             "nuance": "A slightly flirtatious way of saying someone is special. 「だよ」 at the end adds emphasis and warmth.",
#             "speaker_gender": "male",
#             "listener_gender": "female",
#             "etymology": "「特別」means special. Men often use 「だよ」 at the end of a sentence when speaking to a woman."
#         },
#         {
#             "japanese": "昨日は楽しかった**だ**ろう？",
#             "english": "You had fun yesterday, didn't you?",
#             "conjugation": "plain past affirmative",
#             "register": "casual",
#             "setting": "friendly",
#             "nuance": "Asking if the listener had fun yesterday. The speaker assumes they did. The 「だろう」 adds a sense of assumption or friendly inquiry. It's a mix of past tense and conjecture.",
#             "speaker_gender": "male",
#             "listener_gender": "female",
#             "etymology": "「昨日」 means yesterday. The 「だろう」 suggests 「で + あろう」. Men often use 「だろう」at the end of a sentence when speaking to a woman."
#         },
#         {
#             "japanese": "まさか、彼が犯人**だ**とは。",
#             "english": "I can't believe he's the culprit.",
#             "conjugation": "plain present affirmative",
#             "register": "semi-formal",
#             "setting": "serious",
#             "nuance": "Expresses disbelief or shock that someone is the culprit. Often used in storytelling or reflective moments.",
#             "etymology": "「まさか」 means \"no way\". 「犯人」 means criminal"
#         },
#         {
#             "japanese": "それは重要な問題**だ**った。",
#             "english": "That was an important issue.",
#             "conjugation": "plain past affirmative",
#             "register": "semi-formal",
#             "setting": "informative",
#             "nuance": "Declares that something was an important issue. 「だった」 is the past tense of 「だ」.",
#             "etymology": "「重要」means important. 「問題」means issue."
#         },
#         {
#             "japanese": "彼女は僕の理想の人**だ**ったんだ。",
#             "english": "She was my ideal woman.",
#             "conjugation": "plain past affirmative",
#             "register": "intimate",
#             "setting": "melancholic",
#             "nuance": "Expressing a past sentiment of considering someone as the ideal person. A nostalgic and slightly melancholic reflection. The 「んだ」 adds a sense of explanation or emphasis.",
#             "speaker_gender": "male",
#             "etymology": "「理想の人」 means ideal person. The 「んだ」 is a male speech pattern."
#         },
#         {
#             "japanese": "この計画は不可能**だ**と判断しました。",
#             "english": "I judged that this plan was impossible.",
#             "conjugation": "plain present affirmative",
#             "register": "business",
#             "setting": "professional",
#             "nuance": "Stating that a plan was judged to be impossible. Typically used in formal or professional settings.",
#             "etymology": "「不可能」means impossible. 「判断」 means judged."
#         },
#         {
#             "japanese": "この件については、詳細な調査が必要**だ**。",
#             "english": "Regarding this matter, a detailed investigation is necessary.",
#             "conjugation": "plain present affirmative",
#             "register": "formal",
#             "setting": "technical",
#             "nuance": "A formal statement indicating the need for a detailed investigation.",
#             "etymology": "「詳細な調査」means detailed investigation. 「必要」 means necessary."
#         },
#         {
#             "japanese": "そんなこと、嘘**だ**！",
#             "english": "That's a lie!",
#             "conjugation": "plain present affirmative",
#             "register": "casual slang",
#             "setting": "humorous",
#             "nuance": "Expresses disbelief or accusation of a lie. Often used in a playful or humorous context. The exclamation point adds emphasis.",
#             "speaker_gender": "male",
#             "listener_gender": "female"
#         }
#     ],
#     "post_example_writeup": "Remember that 「だ」 is a casual form, so use it with friends, family, or when a relaxed tone is appropriate. In more formal situations, opt for 「です」 or, in very formal writing, 「である」. Also, remember the い-adjective rule; don't directly attach 「だ」 to them!",
#     "false_friends": [
#         {
#             "term": "じゃない",
#             "meaning": "Is not, isn't",
#             "kind": "antonym",
#             "nuance": "Unlike 「だ」, 「じゃない」 indicates negation. It means 'is not' or 'isn't' and is used to deny a statement or characteristic."
#         },
#         {
#             "term": "です",
#             "meaning": "To be, is (polite)",
#             "kind": "synonym",
#             "nuance": "While 「だ」 is casual, 「です」 is the polite equivalent. Use 「です」 in formal settings or when speaking to someone you don't know well."
#         },
#         {
#             "term": "でございます",
#             "meaning": "To be, is (very polite)",
#             "kind": "synonym",
#             "nuance": "「でございます」 is an even more polite version of 「です」, used in very formal or humble situations. It's common in customer service or when addressing superiors."
#         },
#         {
#             "term": "がある",
#             "meaning": "There is",
#             "kind": "similar",
#             "nuance": "While 「だ」 indicates 'is,' 「がある」 indicates 'there is' or 'exists.' It refers to the existence of something, not its identity or state of being."
#         },
#         {
#             "term": "である",
#             "meaning": "To be, is (formal/literary)",
#             "kind": "synonym",
#             "nuance": "「である」 is the formal equivalent of 「だ」, often found in written materials, articles, or official documents. It has a more authoritative or impersonal tone."
#         },
#         {
#             "term": "だった・でした",
#             "meaning": "Was, were (past tense)",
#             "kind": "synonym",
#             "nuance": "「だった」 (casual) and 「でした」 (polite) are the past tense forms of 「だ」 and 「です」, respectively. They indicate that something *was* in a certain state or identity."
#         }
#     ],
#     "post_false_friends_writeup": "Be mindful of the register. Use 「だ」 in casual conversation, 「です」 in polite situations, and 「である」 in formal writing. Remember, 「がある」 indicates existence, while 「だ」 indicates a state of being. Using the wrong form can affect the perceived politeness or formality of your speech."
# }

def space_segmented(tokens: list):
    result = ''
    for token in tokens:
        surface = token['surface']
        pos = token['pos']
        adjacent = surface == ' ' or pos == "補助記号"
        if adjacent:
            result = result.strip(' ') + surface
        else:
            result += surface + ' '
    return result.strip()  

def katakana_to_hiragana(katakana: str) -> str:
    return ''.join(
        chr(ord(char) - 0x60) if 'ァ' <= char <= 'ン' else char
        for char in katakana)

def is_all_hiragana(s):
    return all('\u3040' <= ch <= '\u309F' for ch in s)

def is_all_katakana(s):
    return all('\u30A0' <= ch <= '\u30FF' for ch in s)

def make_key(word: str, reading: str) -> str:
    """
    Creates a key for the dictionary index based on the word and its reading.
    The key is in the format 'word|reading'.
    """
    def compute():
        if is_all_hiragana(word):
            return word
        if is_all_katakana(word):
            return katakana_to_hiragana(word)
        return f"{word}|{reading}"
    result = compute()

    return result

def split_sentence(sentence):
    pattern = r'(\s+|[^\w\s]|[\w]+)'
    return re.findall(pattern, sentence)

def get_annotated_english(mecab, index, english: str, japanese: str):
    raw = mecab.parse(japanese)
    tokens = parse_raw_mecab_output(raw)
    english_readings = { }
    for i,token in enumerate(tokens):
        reading = katakana_to_hiragana(token['reading'])
        key = make_key(token['basic_form'], reading)
        senses = index.get(key, None)
        if senses:
            for sense in senses:
                english_readings[sense] = key

    #print(f"Found {yaml.dump(english_readings, allow_unicode=True, default_flow_style=False, indent=4)}")
    
    english_words = split_sentence(english)
    new_english = ''
    for word in english_words:
        new_english += word
        word = word.lower()
        if word in english_readings:
            reading = english_readings[word]
            new_english += f'[{reading}]'
        elif word.endswith('s'):
            singular = word[:-1]
            if singular in english_readings:
                reading = english_readings[singular]
                new_english += f'[{reading}]'
        elif word.endswith('ing'):
            singular = word[:-3]
            if singular in english_readings:
                reading = english_readings[singular]
                new_english += f'[{reading}]'
    # compact = mecab_raw_to_compact_sentence(raw)
    return new_english

def annotate_english(mecab, index, grammar):
    for example in grammar['examples']:
        english = example['english']
        japanese = example['japanese']
        raw = mecab.parse(japanese)
        compact = mecab_raw_to_compact_sentence(raw)
        example['english'] = get_annotated_english(mecab, index, english, japanese)
        example['compact_japanese'] = compact
        # example['japanese'] = space_segmented(tokens)
        # print(f"Japanese: {example['japanese']}")
        # print(f"Compact: {example['compact_japanese']}")
        #print(f"English: {example['english']}")
        # def escape(s):
        #     return s.replace("'", "\\'")
        # print(f"check_annotate_english('{escape(example['english'])}', '{escape(english)}', '{escape(japanese)}')")


def augment_senses(senses:list):
    work = []
    result = []
    def push(sense):
        if sense not in result:
            work.append(sense)
    for sense in senses:
        for split in sense.split(','):
            split = split.strip().lower()
            split = re.sub(r'\s*\([^)]*\)', '', split)
            if sense.startswith('to '):
                split = split[3:]
            push(split)
    while len(work) > 0:
        sense = work.pop()
        if sense in result:
            continue
        result.append(sense)
        push(sense)
    result.sort()
    return result

additional_words = [
    {
        "word": "ぐらい",
        "reading": "くらい",
        "senses": [ "approximately"]
    },
    {
        "word": "暇",
        "reading": "ひま",
        "senses": ["free"]
    },
    {
        "word": "いい",
        "reading": "いい",
        "senses": ["good"]
    },
    {
        "word": "ホラー",
        "reading": "ホラー",
        "senses": ["horror"]
    },    
]

def augment_words(dictionary):

    for entry in additional_words:
        dictionary.append(entry)
    return dictionary

def index_dictionary(dictionary):
    index = { }
    dictionary = augment_words(dictionary)
    for entry in dictionary:
        def add_senses(key: str):
            if len(key.strip()) == 0:
                return
            if key not in index:
                index[key] = []
            index[key].extend(senses)
            index[key] = list(set(index[key]))
            

        word = entry['word']

        senses = augment_senses(entry['senses'])
        reading = entry['reading']
        key1 = make_key(word, reading)
        key2 = make_key(reading, reading)
        add_senses(key1)
        add_senses(key2)

    return index

def check_annotate_english(mecab, index, english, japanese, expected):
    annotated = get_annotated_english(mecab, index, english, japanese)
    if annotated != expected:
        print(f"Annotated English mismatch for '{english}' and '{japanese}':")
        print(f"Expected: {expected}")
        print(f"Got: {annotated}")
        sys.exit(1)

def test_annotate_english(mecab, index):
    def check_annotate_english(expected, english, japanese):
        annotated = get_annotated_english(mecab, index, english, japanese)
        if annotated != expected:
            print(f"Annotated English mismatch for '{english}' and '{japanese}':")
            print(f"Expected: {expected}")
            print(f"Got: {annotated}")
            sys.exit(1)
    check_annotate_english('I am a student[学生|がくせい].', 'I am a student.', '私は学生**だ**。')
    check_annotate_english('This[本|ほん] is a book[本|ほん].', 'This is a book.', 'これは本**だ**。')
    check_annotate_english('That is a cat[猫|ねこ].', 'That is a cat.', 'あれは猫**だ**。')
    check_annotate_english('She[彼女|かのじょ] is beautiful[綺麗|きれい], isn\'t she[彼女|かのじょ]?', 'She is beautiful, isn\'t she?', '彼女は綺麗**だ**ね。')
    check_annotate_english('I\'m free[ひま] today[今日|きょう], so why don\'t we go[行く|いく] see[見る|みる] a movie[映画|えいが]?', 'I\'m free today, so why don\'t we go see a movie?', '今日はひま**だ**から、映画でも見に行かない？')
    check_annotate_english('The party yesterday[昨日|きのう] was awesome.', 'The party yesterday was awesome.', '昨日、パーティーは最高**だった**。')
    check_annotate_english('It\'s as if what happened then was a dream[夢|ゆめ].', 'It\'s as if what happened then was a dream.', 'あの時のことは夢**だった**かのようだ。')
    check_annotate_english('This[この] plan[計画|けいかく] is not impossible.', 'This plan is not impossible.', 'この計画は不可能**ではない**。')
    check_annotate_english('What\'s important[重要|じゅうよう] isn\'t the result[結果|けっか], but the process.', 'What\'s important isn\'t the result, but the process.', '重要なのは結果**ではない**、プロセス**だ**。')
    check_annotate_english('The weather[天気|てんき] tomorrow will probably[たぶん] be rainy.', 'The weather tomorrow will probably be rainy.', '明日の天気は雨**でしょう**。たぶん。')
    check_annotate_english('It is a pen[ぺん].', 'It is a pen.', 'ペン**です**。')
    check_annotate_english('(I) am Sakura.', '(I) am Sakura.', 'さくら**です**。')
    check_annotate_english('(He/she) is a friend[友達|ともだち].', '(He/she) is a friend.', '友達**です**。')
    check_annotate_english('It is hot.', 'It is hot.', '暑い**です**。')
    check_annotate_english('It\'s beautiful[綺麗|きれい], isn\'t it?', 'It\'s beautiful, isn\'t it?', '綺麗**です**ね。')
    check_annotate_english('It is you[あなた].', 'It is you.', 'あなた**です**。')
    check_annotate_english('This[この] cake[けーき] is delicious[美味しい|おいしい], you know.', 'This cake is delicious, you know.', 'このケーキは美味しい**です**よ。')
    check_annotate_english('It was raining[雨|あめ] yesterday[昨日|きのう].', 'It was raining yesterday.', '昨日雨**でした**。')
    check_annotate_english('This[本|ほん] book[本|ほん] is not my personal property.', 'This book is not my personal property.', 'この本は私物ではあり**ません**。')
    check_annotate_english('I was not busy[忙しい|いそがしい] last week.', 'I was not busy last week.', '先週は忙しくあり**ませんでした**。')
    check_annotate_english('As for now[今|いま], there\'s a test[てすと].', 'As for now, there\'s a test.', '今**は**テストです。')
    check_annotate_english('As for today[今日|きょう], it\'s raining[雨|あめ].', 'As for today, it\'s raining.', '今日**は**、雨です。')
    check_annotate_english('As for me, I like Fridays[金曜|きんよう].', 'As for me, I like Fridays.', '私**は**、金曜日が好きです。')
    check_annotate_english('As for me, as for Fridays[金曜|きんよう], I like them (compared to other days).', 'As for me, as for Fridays, I like them (compared to other days).', '私**は**、金曜日**は**好きです。')
    check_annotate_english('As for me, I am Tom.', 'As for me, I am Tom.', '私**は**トムです。')
    check_annotate_english('As for you[あなた], you[あなた] are Jim.', 'As for you, you are Jim.', 'あなた**は**ジムです。')
    check_annotate_english('As for Tom, he is a teacher[先生|せんせい].', 'As for Tom, he is a teacher.', 'トム**は**先生です。')
    check_annotate_english('As for a calendar[かれんだー], it is necessary[必要|ひつよう].', 'As for a calendar, it is necessary.', 'カレンダー**は**必要です。')
    check_annotate_english('As for me, I am busy[忙しい|いそがしい].', 'As for me, I am busy.', '私**は**忙しいです。')
    check_annotate_english('I can drink sake[酒|さけ], but as for beer[びーる], not so much...', 'I can drink sake, but as for beer, not so much...', 'お酒**は**飲めますが、ビール**は**ちょっと…')
    check_annotate_english('As for her style[すたいる], it\'s good[良い|よい], but[けど] as for her personality[性格|せいかく], well...', 'As for her style, it\'s good, but as for her personality, well...', 'スタイル**は**良いけど、性格**は**ちょっとね。')
    check_annotate_english('This is a pen[ぺん].', 'This is a pen.', 'これはペンです。')
    check_annotate_english('This[本|ほん] is a book[本|ほん].', 'This is a book.', 'これは本です。')
    check_annotate_english('This is sushi[寿司|すし].', 'This is sushi.', 'これは寿司です。')
    check_annotate_english('This is also sushi[寿司|すし].', 'This is also sushi.', 'これも寿司です。')
    check_annotate_english('This is the sea[海|うみ].', 'This is the sea.', 'これは、海です。')
    check_annotate_english('Hey, isn\'t this cute[可愛い|かわいい]?', 'Hey, isn\'t this cute?', 'ねえ、これ、可愛くない？')
    check_annotate_english('Excuse me, how much is this?', 'Excuse me, how much is this?', 'すみません、これ、いくらですか？')
    check_annotate_english('We\'re meeting[会う|あう] for the first time. This is just a small token...', 'We\'re meeting for the first time. This is just a small token...', '初めてお会いしますね。これ、つまらない物ですが…。')
    check_annotate_english('It[それ]\'s that.', 'It\'s that.', '**それ**です。')
    check_annotate_english('That is also an air conditioner.', 'That is also an air conditioner.', '**それ**もエアコンです。')
    check_annotate_english('That is a book[本|ほん].', 'That is a book.', '**それ**は本です。')
    check_annotate_english('That is also a book[本|ほん].', 'That is also a book.', '**それ**も本です。')
    check_annotate_english('That is water.', 'That is water.', '**それ**は、水です。')
    check_annotate_english('It[それ]\'s beautiful[綺麗|きれい], isn\'t it[それ]? Where[どこ] did you buy[買う|かう] that?', 'It\'s beautiful, isn\'t it? Where did you buy that?', '綺麗だね。**それ**、どこで買ったの？')
    check_annotate_english('Nice to meet you. That\'s a lovely[素敵|すてき] tie[ねくたい]. What brand is it[それ]?', 'Nice to meet you. That\'s a lovely tie. What brand is it?', '初めまして。素敵なネクタイですね。**それ**はどちらのブランドですか。')
    check_annotate_english('Tanaka-san[さん], is that a new[新しい|あたらしい] computer? That\'s nice.', 'Tanaka-san, is that a new computer? That\'s nice.', '田中さん、**それ**は新しいパソコンですか。いいですね。')
    check_annotate_english('Sensei, is that in the textbook?', 'Sensei, is that in the textbook?', '先生、**それ**は教科書に載っていますか。')
    check_annotate_english('What[何|なに] is that[何|なに] over there?', 'What is that over there?', 'あれは何ですか。')
    check_annotate_english('That over there is a convenience store.', 'That over there is a convenience store.', 'あれはコンビニです。')
    check_annotate_english('That over there is a hotel[ほてる].', 'That over there is a hotel.', 'あれはホテルです。')
    check_annotate_english('That over there is a train[電車|でんしゃ].', 'That over there is a train.', 'あれは、電車です。')
    check_annotate_english('That over there is my older brother.', 'That over there is my older brother.', 'あれは、兄です。')
    check_annotate_english('That over there is my pen[ぺん].', 'That over there is my pen.', 'あれは私のペンです。')
    check_annotate_english('This is also my pen[ぺん].', 'This is also my pen.', 'これも私のペンです。')
    check_annotate_english('This is my cat[猫|ねこ].', 'This is my cat.', 'これは私の猫です。')
    check_annotate_english('It is the teacher[先生|せんせい]\'s umbrella[傘|かさ].', 'It is the teacher\'s umbrella.', '先生の傘です。')
    check_annotate_english('What is your name[名前|なまえ]?', 'What is your name?', 'あなたの名前は？')
    check_annotate_english('Mr. Yamada\'s car[車|くるま] is red[赤い|あかい].', 'Mr. Yamada\'s car is red.', '山田さんの車は赤いです。')
    check_annotate_english('I love her[彼女|かのじょ] smile[笑顔|えがお].', 'I love her smile.', '彼女の笑顔が大好きです。')
    check_annotate_english('It\'s nice to meet[会う|あう] you. I am a referral[紹介|しょうかい] from Mr. Tanaka.', 'It\'s nice to meet you. I am a referral from Mr. Tanaka.', '初めてお会いしますね。田中さんのご紹介です。')
    check_annotate_english('This is the plan[計画|けいかく] for the company[会社|かいしゃ]\'s new[新しい|あたらしい] project[計画|けいかく].', 'This is the plan for the company\'s new project.', 'これは会社の新しいプロジェクトの計画書です。')
    check_annotate_english('(It is) good[いい].', '(It is) good.', 'いいです。')
    check_annotate_english('This is good[いい].', 'This is good.', 'これは**いい**です。')
    check_annotate_english('This[本|ほん] is a good[いい] book[本|ほん].', 'This is a good book.', 'これは**いい**本です。')
    check_annotate_english('This[本|ほん] is also a good[いい] book[本|ほん].', 'This is also a good book.', 'これも**いい**本です。')
    check_annotate_english('This is a good[いい] sound[音|おと].', 'This is a good sound.', 'これは**いい**音だ。')
    check_annotate_english('If this[この] seat[席|せき] is good[いい], may I sit[座る|すわる] next to you?', 'If this seat is good, may I sit next to you?', 'この席で**よかった**ら、隣、座っても**いい**ですか？')
    check_annotate_english('If[もし] it\'s alright with you, would you like to go[行く|いく] get some tea[茶|ちゃ] after this[この]?', 'If it\'s alright with you, would you like to go get some tea after this?', 'この後、もし**よかった**ら、お茶でも飲みに行きませんか？')
    check_annotate_english('I don\'t think[思う|おもう] this[この] project[企画|きかく] is good[よい].', 'I don\'t think this project is good.', 'この企画は**よくない**と思います。')
    check_annotate_english('Japan\'s roads[みち] are narrow[せまい].', 'Japan\'s roads are narrow.', '日本のみちは、せまいです。')
    check_annotate_english('It is hot[あつい] today[きょう].', 'It is hot today.', '今日(きょう)は暑(あつ)いです。')
    check_annotate_english('It is cold.', 'It is cold.', '寒(さむ)いです。')
    check_annotate_english('This is fun.', 'This is fun.', '楽(たの)しいです。')
    check_annotate_english('A new[新|しん] car[くるま].', 'A new car.', '新(あたら)しい車(くるま)。')
    check_annotate_english('This[この] wine[わいん] is[おい] very[とても] delicious. You should try it.', 'This wine is very delicious. You should try it.', 'このワイン、とても美味(おい)しいです。ぜひ試(ため)してみてください。')
    check_annotate_english('Your eyes[め] are as beautiful[きれい] as stars[ほし]; when[と] I look[見る|みる] at them, I feel like I\'m being[いる] sucked in.', 'Your eyes are as beautiful as stars; when I look at them, I feel like I\'m being sucked in.', '君(きみ)の目(め)は、星(ほし)のように綺麗(きれい)で、見(み)ていると吸(す)い込(こ)まれそうだ。')
    check_annotate_english('From the moment[とき] we first[初|はつ] met, your kind smile[えがお] was very[とても] impressive.', 'From the moment we first met, your kind smile was very impressive.', '初(はじ)めて会(あ)った時(とき)から、君(きみ)の優(やさ)しい笑顔(えがお)がとても印象的(いんしょうてき)でした。')
    check_annotate_english('Very[とても] pretty[綺麗|きれい].', 'Very pretty.', 'とても**綺麗**。')
    check_annotate_english('Very[とても] outside[外|そと].', 'Very outside.', 'とても**外**。')
    check_annotate_english('A pretty[綺麗|きれい] painting[絵|え].', 'A pretty painting.', '**綺麗**な絵。')
    check_annotate_english('She is a beautiful[綺麗|きれい] woman[女性|じょせい], isn\'t she?', 'She is a beautiful woman, isn\'t she?', '**綺麗**な女性ですね。')
    check_annotate_english('It was a free[暇|ひま] day.', 'It was a free day.', '**暇**な一日だった。')
    check_annotate_english('It\'s a quiet[静か|しずか] room[部屋|へや], isn\'t it.', 'It\'s a quiet room, isn\'t it.', '**静か**な部屋ですね。')
    check_annotate_english('That over there is beautiful[綺麗|きれい].', 'That over there is beautiful.', 'あれは**綺麗**です。')
    check_annotate_english('When[と] I drink[飲む|のむ] alcohol[酒|さけ], I become[なる] bolder than[より] usual. Don\'t you think[思う|おもう] it\'s wonderful?', 'When I drink alcohol, I become bolder than usual. Don\'t you think it\'s wonderful?', 'お酒を飲むと、いつもより大胆になります。素敵だと思いませんか？')
    check_annotate_english('I\'m glad[嬉しい|うれしい] we could meet again[また] in such[こんな] a wonderful place[場所|ばしょ].', 'I\'m glad we could meet again in such a wonderful place.', 'こんな**素敵な**場所で、また会えて嬉しいです。')
    check_annotate_english('Is this[本|ほん] a book[本|ほん]?', 'Is this a book?', 'これは本**か**。')
    check_annotate_english('Is this[本|ほん] your book[本|ほん]?', 'Is this your book?', 'これはあなたの本**か**。')
    check_annotate_english('Is this[本|ほん] also your book[本|ほん]?', 'Is this also your book?', 'これもあなたの本**か**。')
    check_annotate_english('Is this a pen[ぺん]?', 'Is this a pen?', 'これ、ペン**か**？')
    check_annotate_english('Is what you said yesterday[昨日|きのう] true?', 'Is what you said yesterday true?', '昨日言ったことは本当**か**。')
    check_annotate_english('Is this good[いい]?', 'Is this good?', 'これ、いい**か**？')
    check_annotate_english('Hey, I wonder if you\'re free today[今日|きょう]?', 'Hey, I wonder if you\'re free today?', 'ねえ、今日、時間ある**か**な？')
    check_annotate_english('Could it be that you[僕|ぼく] like me[僕|ぼく]?', 'Could it be that you like me?', 'もしかして、僕のこと、好き**か**な…？')
    check_annotate_english('I was wondering if you\'d like to get tea[茶|ちゃ] after this[この]?', 'I was wondering if you\'d like to get tea after this?', 'この後、お茶でもどう**か**しら？')
    check_annotate_english('How old might your daughter be[いらっしゃる]?', 'How old might your daughter be?', 'お嬢様はおいくつでいらっしゃいます**か**。')
    check_annotate_english('It\'s raining[雨|あめ].', 'It\'s raining.', '雨**が**降っています。')
    check_annotate_english('The tea[茶|ちゃ] is cold[冷たい|つめたい].', 'The tea is cold.', 'お茶**が**冷たいです。')
    check_annotate_english('What[何|なに] is good[いい]? (What[何|なに] would you like?)', 'What is good? (What would you like?)', '何**が**いい？')
    check_annotate_english('That is good[いい]. (That is what I would like)', 'That is good. (That is what I would like)', 'それ**が**いいです。')
    check_annotate_english('The curry[かれー] is spicy. (The curry[かれー] is the thing that is spicy)', 'The curry is spicy. (The curry is the thing that is spicy)', 'カレー**が**辛い。')
    check_annotate_english('The tree[木|き] is tall[高い|たかい]. (The tree[木|き] is the thing that is tall[高い|たかい])', 'The tree is tall. (The tree is the thing that is tall)', '木**が**高い。')
    check_annotate_english('What[何|なに] is good at this[この] restaurant[れすとらん]? The steak[すてーき] is good.', 'What is good at this restaurant? The steak is good.', 'このレストランは何**が**美味しいですか。ステーキ**が**美味しいです。')
    check_annotate_english('Tom is a fast[早い|はやい] runner.', 'Tom is a fast runner.', 'トムは足が早い**よ**。')
    check_annotate_english('I am tall[高い|たかい].', 'I am tall.', '私は背が高い**よ**。')
    check_annotate_english('Baseball[野球|やきゅう] is fun[楽しい|たのしい].', 'Baseball is fun.', '野球は楽しい**よ**。')
    check_annotate_english('This is a cake[けーき].', 'This is a cake.', 'これはケーキ**だ****よ**。')
    check_annotate_english('That is good[いい].', 'That is good.', 'それはいい**よ**。')
    check_annotate_english('I want to know[知る|しる] more about you, you know[知る|しる].', 'I want to know more about you, you know.', '君のこと、もっと知りたい**よ**。')
    check_annotate_english('Starting today[今日|きょう], I[俺|おれ]\'ll protect[守る|まもる] you, you know.', 'Starting today, I\'ll protect you, you know.', '今日から、俺がお前のこと守る**よ**。')
    check_annotate_english('This[この] apple pie is really delicious[美味しい|おいしい], you know!', 'This apple pie is really delicious, you know!', 'このアップルパイ、本当に美味しい**です****よ**。')
    check_annotate_english('Matsushita-san[さん] is cute[かわいい], isn\'t she?', 'Matsushita-san is cute, isn\'t she?', '松下さんはかわいい**ね**。')
    check_annotate_english('That\'s good[いい], right?', 'That\'s good, right?', 'いいです**ね**。')
    check_annotate_english('It\'s delicious[美味しい|おいしい], right?', 'It\'s delicious, right?', '美味しい**ね**。')
    check_annotate_english('It is cold[寒い|さむい], isn\'t it!', 'It is cold, isn\'t it!', '寒い**ね**！')
    check_annotate_english('That is a good[いい] question, right?', 'That is a good question, right?', 'いい質問です**ね**。')
    check_annotate_english('Bicycles are nice, aren\'t they?', 'Bicycles are nice, aren\'t they?', '自転車はいい**ね**。')
    check_annotate_english('Let\'s go home together[一緒|いっしょ] today[今日|きょう], okay?', 'Let\'s go home together today, okay?', '今日、一緒に帰ろう**ね**。')
    check_annotate_english('I\'m really happy[嬉しい|うれしい] to[と] have met someone as wonderful as you, you know?', 'I\'m really happy to have met someone as wonderful as you, you know?', '君みたいな素敵な人と出会えて、本当に嬉しい**ね**。')
    check_annotate_english('I like watching[見る|みる] movies[映画|えいが].', 'I like watching movies.', '映画を見るのが好きです。')
    check_annotate_english('I\'m not good at waking up early in the morning[朝|あさ].', 'I\'m not good at waking up early in the morning.', '朝早く起きるのが苦手です。')
    check_annotate_english('I try to drink[飲む|のむ] water every day.', 'I try to drink water every day.', '毎日、水を飲むようにしています。')
    check_annotate_english('Teacher[先生|せんせい], tell[教える|おしえる] me the meaning[意味|いみ] of this[この] kanji[漢字|かんじ].', 'Teacher, tell me the meaning of this kanji.', '先生、この漢字の意味を教えて。')
    check_annotate_english('Want to go[行く|いく] see[見る|みる] a movie[映画|えいが] tomorrow?', 'Want to go see a movie tomorrow?', '明日、映画を見に行かない？')
    check_annotate_english('How[どう] about we eat[食べる|たべる] together[一緒|いっしょ] at the new[新しい|あたらしい] restaurant[れすとらん]?', 'How about we eat together at the new restaurant?', '一緒に新しいレストランで食べるのはどう？')
    check_annotate_english('To attend the important[重要|じゅうよう] meeting[会議|かいぎ], it is necessary[必要|ひつよう] to leave[出る|でる] home early.', 'To attend the important meeting, it is necessary to leave home early.', '重要な会議に出るためには、早めに家を出る必要がある。')
    check_annotate_english('Reading[読む|よむ] this[本|ほん] book[本|ほん] might change[変わる|かわる] your life.', 'Reading this book might change your life.', 'この本を読むと、人生が変わるかもしれない。')
    check_annotate_english('If[と] you don\'t study[試験|しけん] properly[ちゃんと], you\'ll fail the exam.', 'If you don\'t study properly, you\'ll fail the exam.', 'ちゃんと勉強しないと、試験に落ちるよ。')
    check_annotate_english('I will read[読む|よむ] a book[本|ほん].', 'I will read a book.', '本を**読む**。')
    check_annotate_english('I will meet[会う|あう] a friend[友達|ともだち] tomorrow.', 'I will meet a friend tomorrow.', '明日、友達に**会う**。')
    check_annotate_english('I drink[飲む|のむ] coffee[こーひー] every day.', 'I drink coffee every day.', '毎日コーヒーを**飲む**。')
    check_annotate_english('Everyone listens[聞く|きく] to Tanaka because she[彼女|かのじょ] always tells interesting[面白い|おもしろい] stories.', 'Everyone listens to Tanaka because she always tells interesting stories.', '田中さんはいつも面白い話をするから、皆が彼女の話を**聞く**。')
    check_annotate_english('I\'m tired, so I\'ll rest[休む|やすむ] a bit.', 'I\'m tired, so I\'ll rest a bit.', '疲れたから、少し**休む**。')
    check_annotate_english('I don\'t have any money to lend[貸す|かす] him.', 'I don\'t have any money to lend him.', '彼に**貸す**お金はない。')
    check_annotate_english('I read[読む|よむ] a book[本|ほん].', 'I read a book.', '本**を**読む。')
    check_annotate_english('What[何|なに] will you eat[食べる|たべる]?', 'What will you eat?', '何**を**食べますか。')
    check_annotate_english('Won\'t you have some coffee[こーひー]?', 'Won\'t you have some coffee?', 'コーヒー**を**飲みませんか。')
    check_annotate_english('I walk[歩く|あるく] to school[学校|がっこう] every day.', 'I walk to school every day.', '毎日、学校**を**歩きます。')
    check_annotate_english('I like taking walks[散歩|さんぽ] in the park[公園|こうえん].', 'I like taking walks in the park.', '公園**を**散歩するのが好きです。')
    check_annotate_english('I don\'t eat[食べる|たべる] sushi[寿司|すし].', 'I don\'t eat sushi.', '寿司を食べ**ない**。')
    check_annotate_english('I don\'t eat[食べる|たべる] sushi[寿司|すし].', 'I don\'t eat sushi.', '寿司を食べ**ません**。')
    check_annotate_english('I don\'t watch[見る|みる] TV[てれび].', 'I don\'t watch TV.', 'テレビを見**ない**。')
    check_annotate_english('I don\'t watch[見る|みる] TV[てれび].', 'I don\'t watch TV.', 'テレビを見**ません**。')
    check_annotate_english('I will not borrow[借りる|かりる] money.', 'I will not borrow money.', 'お金を借り**ない**。')
    check_annotate_english('I will not borrow[借りる|かりる] money.', 'I will not borrow money.', 'お金を借り**ません**。')
    check_annotate_english('I don\'t eat[食べる|たべる] bread[ぱん].', 'I don\'t eat bread.', 'パンを食べ**ない**。')
    check_annotate_english('I don\'t eat[食べる|たべる] bread[ぱん].', 'I don\'t eat bread.', 'パンを食べ**ません**。')
    check_annotate_english('I don\'t watch[見る|みる] horror[ほらー] movies[映画|えいが].', 'I don\'t watch horror movies.', 'ホラー映画は見**ない**。')
    check_annotate_english('If I don\'t go[行く|いく] to school[学校|がっこう] tomorrow, will you come[来る|くる] to my place?', 'If I don\'t go to school tomorrow, will you come to my place?', '明日、学校へ行か**なかった**ら、うちに来る？')
    check_annotate_english('I didn\'t say[言う|いう] such a thing[こと].', 'I didn\'t say such a thing.', 'そんなこと、言わ**なかった**です。')
    check_annotate_english('Teacher[先生|せんせい], I didn\'t do[する] the homework[宿題|しゅくだい] yesterday[昨日|きのう].', 'Teacher, I didn\'t do the homework yesterday.', '先生、昨日、宿題をし**ませんでした**。')
    check_annotate_english('It\'s not like I liked you at all, you know!', 'It\'s not like I liked you at all, you know!', '君のことなんか、全然好きじゃ**なかった**んだからね！')
    check_annotate_english('If[もし] it doesn\'t clear up tomorrow, we won\'t go[行く|いく] on a picnic[ぴくにっく].', 'If it doesn\'t clear up tomorrow, we won\'t go on a picnic.', 'もし明日、晴れ**なければ**、ピクニックに行きません。')
    check_annotate_english('I don\'t have money.', 'I don\'t have money.', 'お金は**ない**。')
    check_annotate_english('I won\'t have[持つ|もつ] a car[車|くるま].', 'I won\'t have a car.', '車は**持ちません**。')
    check_annotate_english('Trees[木|き] do not walk[歩く|あるく].', 'Trees do not walk.', '木は**歩きません**。')
    check_annotate_english('Tommy does not talk[話す|はなす].', 'Tommy does not talk.', 'トミーは**話さない**。')
    check_annotate_english('I do not hit[打つ|うつ] the ball[ぼーる].', 'I do not hit the ball.', 'ボールを**打ちません**。')
    check_annotate_english('I will not go[行く|いく] to school[学校|がっこう] tomorrow.', 'I will not go to school tomorrow.', '明日、学校へ**行かない**。')
    check_annotate_english('I would never say[言う|いう] something like that.', 'I would never say something like that.', 'そんなこと、絶対に**言わない**。')
    check_annotate_english('"Want to go on a date[でーと] tomorrow?" "Sorry, I\'m busy[忙しい|いそがしい] tomorrow, so I can\'t go."', '"Want to go on a date tomorrow?" "Sorry, I\'m busy tomorrow, so I can\'t go."', '「明日、デートしない？」 「ごめん、明日忙しいから、**行けない**。」')
    check_annotate_english('So you don\'t drink[飲む|のむ] alcohol[酒|さけ]?', 'So you don\'t drink alcohol?', 'お酒は**飲まない**んですか？')
    check_annotate_english('Fish[魚|さかな] and[と] bananas.', 'Fish and bananas.', '魚とバナナ。')
    check_annotate_english('This and[と] that are mine.', 'This and that are mine.', 'これとそれは私のものです。')
    check_annotate_english('Mary, Takeshi, and[と] Robert are college[大学|だいがく] students.', 'Mary, Takeshi, and Robert are college students.', 'メアリーとたけしとロバートは大学生だ。')
    check_annotate_english('This and[と] this too are yours, right?', 'This and this too are yours, right?', 'これとこれもあなたのですよね。')
    check_annotate_english('I teach[教える|おしえる] katakana[かたかな] and[と] hiragana[ひらがな].', 'I teach katakana and hiragana.', '私はカタカナとひらがなを教えます。')
    check_annotate_english('Which would you prefer today[今日|きょう]: a movie[映画|えいが] or dinner?', 'Which would you prefer today: a movie or dinner?', '今日、映画**と**食事、どちらがいい？')
    check_annotate_english('The stars[星|ほし] look[見える|みえる] more beautiful[綺麗|きれい] than[より] usual when[いつ] I\'m watching[見る|みる] them with[と] you.', 'The stars look more beautiful than usual when I\'m watching them with you.', '君**と**見る星は、いつもより綺麗に見えるよ。')

def test(mecab, index):
    test_annotate_english(mecab, index)
    return


def process_grammars(dictionaryYaml: str, grammars: list, output: str):
    mecab = get_mecab_tagger()

    with open(dictionaryYaml, 'r', encoding='utf-8') as f:
        dictionary = yaml.safe_load(f.read())
        index = index_dictionary(dictionary)

    test(mecab, index)

    all_grammars = []
    
    for grammar_file in grammars:
        with open(grammar_file, 'r', encoding='utf-8') as f:
            grammar = yaml.safe_load(f.read())
            #print(f"Processing grammar point: {grammar['grammar_point']}")
            annotate_english(mecab, index, grammar)
            all_grammars.append(grammar)

    # Combine all grammars into a single dictionary
    combined_grammar = {
        'grammar_points': all_grammars
    }

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(combined_grammar, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    _, dictionary, *grammars, output = sys.argv
    process_grammars(dictionary, grammars, output)

    