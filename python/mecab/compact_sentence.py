import re
from python.mecab.tagger import get_mecab_tagger

validate = True

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

pos2_map = {
    "副詞可能": "adverb-possible",
    "一般": "general",
    "サ変可能": "suru-possible",
    "地名": "place-name",
    "状詞可能": "descriptive-possible",
    "形状詞可能": "pos2-unk1",
    "助数詞可能": "counter-possible",
    "サ変形状詞可能": "pos2-unk2",
    "人名": "person-name",
    "助数詞": "counter",
    "": ''
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

conjugated_type_map = {
    "助動詞-タ": "auxv-ta",        # だった (datta - "was")
    "助動詞-ダ": "auxv-da",        # だ (da - "is/am/are")
    "助動詞-マス": "auxv-masu",    # ます (masu - polite ending)
    "助動詞-ヌ": "auxv-nu",        # ぬ (nu - classical negative), classical
    "助動詞-デス": "auxv-desu",    # です (desu - polite copula)
    "助動詞-ナイ": "auxv-nai",     # ない (nai - "not")
    "助動詞-ラシイ": "auxv-rashii",  # らしい (rashii - "seems like/apparently")
    "助動詞-レル": "auxv-reru",    # られる (rareru - passive/potential)
    "助動詞-タイ": "auxv-tai",     # たい (tai - "want to")
    "文語助動詞-リ": "auxv-ri",  # り (ri - classical perfective), classical
    "文語助動詞-ベシ": "auxv-beshi",  # べし (beshi - "should/ought to"), classical
    "文語助動詞-ゴトシ": "auxv-gotoshi",  # ごとし (gotoshi - "like/as if"), classical
    "助動詞-マイ": "auxv-mai",  # まい (mai - "probably won't/shouldn't")
    "助動詞-ジャ": "auxv-ja",  # じゃ (ja - contracted copula "is/am/are")
    "助動詞-ヤ": "auxv-ya",  # や (ya - classical question particle/auxiliary)
    "文語助動詞-タリ-断定": "auxv-tari",  # たり (tari - classical assertive), classical
    "形容詞": "adjective",          # 高い (takai - "tall/expensive")
    "五段-ラ行": "godan-ra",       # 作る (tsukuru - "to make")
    "五段-カ行": "godan-ka",       # 書く (kaku - "to write")
    "五段-ガ行": "godan-ga",       # 泳ぐ (oyogu - "to swim")
    "五段-サ行": "godan-sa",       # 話す (hanasu - "to speak")
    "五段-タ行": "godan-ta",       # 立つ (tatsu - "to stand")
    "五段-ナ行": "godan-na",       # 死ぬ (shinu - "to die"), rare
    "五段-バ行": "godan-ba",       # 遊ぶ (asobu - "to play")
    "五段-マ行": "godan-ma",       # 読む (yomu - "to read")
    "五段-ワ行": "godan-wa",       # 買う (kau - "to buy")
    "五段-ワア行": "godan-waa",    # 言う (iu - "to say")
    "上一段-ア行": "i-ichidan-a",  # いる (iru - "to exist")
    "上一段-カ行": "i-ichidan-ka", # 起きる (okiru - "to wake up")
    "上一段-ガ行": "i-ichidan-ga", # 過ぎる (sugiru - "to pass")
    "上一段-ザ行": "i-ichidan-za", # 信じる (shinjiru - "to believe")
    "上一段-タ行": "i-ichidan-ta", # 落ちる (ochiru - "to fall")
    "上一段-ナ行": "i-ichidan-na", # 死ぬる (shinuru), archaic
    "上一段-バ行": "i-ichidan-ba", # 浴びる (abiru - "to bathe")
    "上一段-マ行": "i-ichidan-ma", # 見る (miru - "to see")
    "上一段-ラ行": "i-ichidan-ra", # 居る (iru - "to be"), archaic
    "下一段-ハ行": "e-ichidan-ha",  # へる (heru - "to decrease"), rare
    "下一段-ア行": "e-ichidan-a",  # える (eru - "to get"), rare
    "下一段-サ行": "e-ichidan-sa", # せる (seru - causative), rare
    "下一段-バ行": "e-ichidan-ba", # 食べる (taberu - "to eat")
    "下一段-カ行": "e-ichidan-ka", # 受ける (ukeru - "to receive")
    "下一段-ガ行": "e-ichidan-ga", # 上げる (ageru - "to raise")
    "下一段-ザ行": "e-ichidan-za", # 教える (oshieru - "to teach")
    "下一段-タ行": "e-ichidan-ta", # 捨てる (suteru - "to throw away")
    "下一段-ダ行": "e-ichidan-da", # 出る (deru - "to exit")
    "下一段-ナ行": "e-ichidan-na", # 寝る (neru - "to sleep")
    "下一段-マ行": "e-ichidan-ma", # 止める (yameru - "to stop")
    "下一段-ラ行": "e-ichidan-ra", # 入れる (ireru - "to put in")
    "文語下二段-ア行": "nidan-a",   # 得 (u - "to get"), classical
    "文語下二段-カ行": "nidan-ka",  # 受く (uku - "to receive"), classical
    "文語下二段-ガ行": "nidan-ga",  # 上ぐ (agu - "to raise"), classical
    "文語下二段-ザ行": "nidan-za",  # 教ふ (oshefu - "to teach"), classical
    "文語下二段-タ行": "nidan-ta",  # 捨つ (sutsu - "to throw away"), classical
    "文語下二段-ダ行": "nidan-da",  # 出づ (idezu - "to exit"), classical
    "文語下二段-ナ行": "nidan-na",  # 寝ぬ (nenu - "to sleep"), classical
    "文語下二段-バ行": "nidan-ba",  # 食ぶ (tabu - "to eat"), classical
    "文語下二段-マ行": "nidan-ma",  # 止む (yamu - "to stop"), classical
    "文語下二段-ヤ行": "nidan-ya",  # 焼ゆ (yaku - "to burn"), classical
    "文語下二段-ラ行": "nidan-ra",  # 入る (iru - "to enter"), classical
    "文語下二段-ワ行": "nidan-wa",  # 植う (uu - "to plant"), classical
    "文語上二段-カ行": "upper-nidan-ka", # 起く (oku - "to wake up"), classical
    "文語上二段-ガ行": "upper-nidan-ga", # 過ぐ (sugu - "to pass"), classical
    "カ行変格": "ka-irregular",    # 来る (kuru - "to come")
    "サ行変格": "sa-irregular",    # する (suru - "to do")
    "文語サ行変格": "classical-sa-irregular",  # す (su - classical "to do"), classical
    "文語四段-カ行": "yodan-ka",  # 書く (kaku - "to write"), classical
    "文語四段-ガ行": "yodan-ga",  # 泳ぐ (oyogu - "to swim"), classical
    "文語四段-サ行": "yodan-sa",  # 話す (hanasu - "to speak"), classical
    "文語四段-タ行": "yodan-ta",  # 立つ (tatsu - "to stand"), classical
    "文語四段-ナ行": "yodan-na",  # 死ぬ (shinu - "to die"), classical
    "文語四段-バ行": "yodan-ba",  # 遊ぶ (asobu - "to play"), classical
    "文語四段-マ行": "yodan-ma",  # 読む (yomu - "to read"), classical
    "文語四段-ラ行": "yodan-ra",  # 作る (tsukuru - "to make"), classical
    "文語四段-ワ行": "yodan-wa",  # 買ふ (kafu - "to buy"), classical
    "文語四段-ハ行": "yodan-ha",  # 笑ふ (warafu - "to laugh"), classical
    "文語形容詞-ク": "classical-adjective-ku",  # 高く (takaku), classical
   "": ""
}

conjugated_form_map = {
  "仮定形-一般": "conditional", 
  "仮定形-融合": "conditional-fused",
  "命令形": "imperative",
  "意志推量形": "volitional-presumptive",
  "未然形-サ": "imperfective-sa",
  "未然形-一般": "imperfective",
  "終止形-一般": "terminal",
  "終止形-撥音便": "terminal-nasal",
  "終止形-融合": "terminal-fused",
  "語幹-一般": "stem",
  "連体形-一般": "attributive",
  "連用形-イ音便": "conjunctive-i-sound",
  "連用形-ニ": "conjunctive-ni",
  "連用形-一般": "conjunctive",
  "連用形-促音便": "conjunctive-geminate", 
  "連用形-撥音便": "conjunctive-nasal",
  "連用形-融合": "conjunctive-fused",
  "未然形-セ": "imperfective-se",
  "連用形-ウ音便": "conjunctive-u-sound",
  "連体形-撥音便": "attributive-nasal",
  "已然形-一般": "realis",
  "連体形-補助": "attributive-auxiliary",
  "未然形-補助": "imperfective-auxiliary",
  "": ""
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

def compact_sentence_to_japanese(compact_sentence, spaces=False, collapse_punctuation=True):
    pattern = r'ˢ(.*?)ᵖ'
    matches = re.findall(pattern, compact_sentence, re.DOTALL)
    if spaces:
        result = ' '.join(matches).replace('{ ', '{').replace(' }', '}')
        if collapse_punctuation:
            for punc in pos_to_chars['auxs']:
                if punc == '{' or punc == '}': continue
                result = result.replace(f' {punc}', punc)
                result = result.replace(f'{punc} ', punc)
        return result
    else:
        return ''.join(matches)

_validate_compact_token_to_raw_mecab = {}

def _parse_raw_mecab_output(raw_output : str) -> list[dict]:
    tokens = []
    for line in raw_output.split("\n"):
        if line == "EOS":
            continue
        line = line.strip()
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
        try:

            # --- Safe Parsing Helper Function ---
            def get_feature(features_list, index, default_value=""):
                """Safely gets a feature from the list by index, returning a default value if it's out of bounds."""
                if index < len(features_list):
                    return features_list[index]
                return default_value

            # --- Your Main Parsing Logic ---
            # Assuming 'features' is the list of fields from the UniDic output (e.g., ['名詞', '数詞'])
            # and 'add(key, value)' is your function to build the result.

            # We now use the get_feature() helper for every access to make the code robust.

            # --- Part of Speech (POS) ---
            # Using .get() for the maps is also a good defensive practice.
            add("pos", pos_map.get(get_feature(features, 0)))
            add("pos_detail_1", pos1_map.get(get_feature(features, 1)))
            add("pos_detail_2", pos2_map[get_feature(features, 2)])
            add("pos_detail_3", get_feature(features, 3))

            # --- Conjugation ---
            add("conjugated_type", conjugated_type_map.get(get_feature(features, 4)))
            add("conjugated_form", conjugated_form_map.get(get_feature(features, 5)))

            # --- Lexical Information & Pronunciation ---
            add("lemma_pronunciation", get_feature(features, 6))
            add("lemma", get_feature(features, 7))

            # --- Orthography (Spelling) ---
            add("surface_orthography", get_feature(features, 8))
            add("base_orthography", get_feature(features, 10))

            # --- Pronunciation ---
            add("surface_pronunciation", get_feature(features, 9))
            add("base_pronunciation", get_feature(features, 11))
            add("surface_kana", get_feature(features, 20))
            add("base_kana", get_feature(features, 21))

            # --- Semantic and Grammatical Info ---
            add("word_origin", get_feature(features, 12))
            add("initial_inflection_type", get_feature(features, 13))
            add("initial_inflection_form", get_feature(features, 14))
            add("final_inflection_type", get_feature(features, 15))
            add("final_inflection_form", get_feature(features, 16))
            add("initial_connection_type", get_feature(features, 17))
            add("final_connection_type", get_feature(features, 18))
            add("entry_type", get_feature(features, 19))

            # --- Word Form (Pronunciation-based) ---
            add("surface_form_pronunciation", get_feature(features, 22))
            add("base_form_pronunciation", get_feature(features, 23))

            # --- Accent Information ---
            add("accent_type", get_feature(features, 24))
            add("accent_connection_type", get_feature(features, 25))
            add("accent_modification_type", get_feature(features, 26))

            # --- Unique Identifiers ---
            add("internal_id", get_feature(features, 27))
            add("lemma_id", get_feature(features, 28))

        except Exception as e:
            print(f"LINE: {line}")
            raise

        if validate:
            compact_token = _raw_token_to_compact_token(token)
            japanese = ""
            for x in raw_output.split("\n"):
                if x == "EOS":
                    continue
                x = x.strip()
                parts = x.split("\t")
                japanese += parts[0] + " "

            if compact_token not in _validate_compact_token_to_raw_mecab:
                _validate_compact_token_to_raw_mecab[compact_token] =[line, japanese]
            else:
                [prior_line, prior_japanese] = _validate_compact_token_to_raw_mecab[compact_token]
                if line != prior_line:
                    with open("/workspaces/cloze-data/conflicts.txt", "w") as file:
                        file.write(f"COMPACT:     {compact_token}\n")
                        file.write(f"  TOKEN1:    {line}\n")
                        file.write(f"  SENTENCE1: {japanese}\n")
                        file.write(f"  TOKEN2:    {prior_line}\n")
                        file.write(f"  SENTENCE2: {prior_japanese}\n")
                    raise Exception("Two Mecab lines map to the same compact representation.")

        tokens.append(token)
    return tokens

def _raw_token_to_compact_token(token: dict) -> str:
    recombined = ""
    surface = token["surface"]
    pos = token["pos"]
    pos_detail_1 = token.get("pos_detail_1")
    pos_detail_2 = token.get("pos_detail_2")
    
    conjugated_type = token.get("conjugated_type")
    conjugated_form = token.get("conjugated_form")
    lemma = token.get("lemma")
    base = token.get("base_orthography", None)
    pronunciation = token.get("surface_pronunciation", None)

    pos_code = pos_map.get(pos, pos)

    recombined += f"⌈ˢ{surface}ᵖ{pos_code}"
    if pos_detail_1:
        recombined += f":{pos_detail_1}"
    if pos_detail_2 and pos_detail_2 != "general":
        recombined += f":{pos_detail_2}"
    if conjugated_type:
        recombined += f":{conjugated_type}"
    if conjugated_form:
        recombined += f":{conjugated_form}"
    if base:
        recombined += f"ᵇ{base}"
    if lemma and lemma != surface:
        recombined += f"ᵈ{lemma}"
    if pronunciation and pronunciation != surface:
        recombined += f"ʳ{pronunciation}"
    recombined += "⌉"
    return recombined

def _raw_tokens_to_compact_sentence(tokens: list[dict]) -> str:
    recombined = ""
    for token in tokens:
        recombined += _raw_token_to_compact_token(token)
    return recombined

def _mecab_raw_to_compact_sentence(raw: str) -> str:
    tokens = _parse_raw_mecab_output(raw)
    return _raw_tokens_to_compact_sentence(tokens)

def japanese_to_compact_sentence(japanese: str) -> str:
    wakati = get_mecab_tagger()

    # Fix for special case seen
    japanese = japanese.replace(' っ', 'っ').replace('っ ', 'っ')
    raw = wakati.parse(japanese)
    return _mecab_raw_to_compact_sentence(raw)

    
def japanese_to_japanese_with_spaces(japanese: str, collapse_punctuation: bool = True) -> str:
    wakati = get_mecab_tagger()
    try:
        # Fix for special case seen
        japanese = japanese.replace(' っ', 'っ').replace('っ ', 'っ')
        raw = wakati.parse(japanese)
        compact_sentence = _mecab_raw_to_compact_sentence(raw)
        result = compact_sentence_to_japanese(compact_sentence, spaces=True, collapse_punctuation=collapse_punctuation)

        if validate:
            # Round trip check
            reconstructed = wakati.parse(result)
            reconstructed_compact_sentence = _mecab_raw_to_compact_sentence(reconstructed)
            if compact_sentence != reconstructed_compact_sentence:
                raise ValueError(f"Reconstructed compact sentence does not match original\n{japanese}=>{compact_sentence}\n{result}=>{reconstructed_compact_sentence}")

        return result
    except Exception as e:
        raise Exception(f"Failed to convert Japanese '{japanese}' to spaced Japanese: {e}")

def split_compact_sentence(compact_sentence: str) -> list[str]:
    return re.findall(r'⌈[^⌉]*⌉', compact_sentence)
