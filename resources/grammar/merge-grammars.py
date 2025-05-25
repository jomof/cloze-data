import sys
import yaml
from dumpyaml import dump_yaml_file
import difflib
import re
import os
import json

missing_meanings = {
    "Number+も": "Indicates a surprising or emphatic quantity, e.g. “as many as” or “not even.",
    "何しろ": "Emphasizes “in any case,” “anyway,” or “after all,” stressing inevitability or importance.",
    "い-adjective (predicate)": "An い-adjective used as the sentence-ending descriptor for a state or property.",
    "Relative Clause": "Modifies a noun by providing additional descriptive information about it." ,
    "Rhetorical Question": "A question asked for effect, not requiring an answer, often used to express strong emotion or make a point.",
    "Verb[masu-stem]+Noun": "Treats a verb in the masu-stem form as a noun, often to describe an action or state as a concept.",
    "Verb[masu-stem] (conjunction)": "Treats the verb’s ます-stem as a conjunction, linking consecutive or simultaneous actions (like “and” or “then”).",
    "お": "Honorific prefix for nouns and verbs, adds politeness and respect.",
    "お~だ": "Polite copula, equivalent to 'desu' but often used for adjectives or states related to the listener.", 
    "お〜する": "Humble verb form, used when the speaker performs an action for someone of higher status.",
    "お〜になる": "Honorific verb form indicating respect for the actions of someone of higher status.",
    "かい": "Informal sentence ending particle, similar to 'ka' but softer and more casual, often used by males.",
    "が (subject marker)": "Particle marking the grammatical subject of the sentence.", 
    "ことがある (there are times when)":  "Indicates that there are times an action or event happens.", 
    "ことがある (occassionally)": "Indicates an action or event happens occasionally.",
    "しい": "Suffix for i-adjectives, indicates a strong emotion or feeling.",
    "だい": "Informal sentence ending particle, emphasizes a question or request, often used by males.",
    "っけ": "Sentence ending particle, expresses uncertainty or seeks confirmation, 'wasn't it?', 'didn't we?'", 
    "に (in, with - hypothetical)": "Marks a hypothetical situation or condition.",
    "は〜が": "Sentence structure emphasizing a contrast, 'A is (topic), but B (focus)'.",
    "は〜だ": "Basic sentence structure, identifies the topic (A) and provides information (B) about it.", 
    "わ": "Sentence ending particle, mainly used by females, adds a soft and feminine tone, can express emphasis or emotion.",
    "を (object marker)":  "Particle marking the direct object of a transitive verb.",
    "を (object of an emotion)": "Indicates the object or cause of an emotion or feeling.", 
    "を (point of departure)": "Indicates the point from which someone or something departs or separates.",
    "君・くん": "Suffix added to names, primarily for males, expresses familiarity or a slightly informal tone.",
    "１〜たりとも〜ない": "Emphasizes 'not even one' or 'not a single.'",
    "Verb[て]+はいけない": "Must not, may not, cannot. Expresses strong prohibition or a rule that forbids the action.",
    "Verb[ない]+ものかな・ものだろうか": "Is there no way to make this happen? I wish it could be so..."
}

grammar_point_name_rules = """
# Rules for Grammar Point Names:
# - The Grammar Point Name must accurately represent real, fluent, natural Japanese.
# - Instead of using numbers like やる①, use descriptive like やる (send)
# - Japanese text in parenthesis is optional in the grammar point.
# - English inside parenthesis at the end is flavor text and must be all lower case
# - Use + to combine two things when they're directly adjacent.
# - 〜 and ~ are used to combine two things when they're not directly adjacent. 
# - Alternatives between multiple grammar options are separated by '・' and not a slash.
# - Rules for [brackets]:
#   - Verb[conjugation] means a verb conjugated in that way (volitional, etc)
#   - Adjective[conjugation] means an adjective conjugated in that way (past, etc)
"""
grammar_point_name_translations = {
    "〜わ〜わ": "わ〜わ",
    "〜やら〜やら": "やら〜やら",
    "〜も[V]ば〜も[V]": "Noun+も+Verb[ば-conditional]+Noun+も+Verb",
    "〜であれ〜であれ": "Noun+であれ+Noun+であれ",
    "のなかで〜がいちばん〜": "Group+のなかで+Subject+がいちばん+Verb・Adjective",
    "〜得ない": "Noun・Verb[dictionary]・Adjective+得ない",
    "〜代": "Number+代",
    "〜んです・のです": "Noun+な・Verb[dictionary]・Adjective+んです・のです",
    "のだ": "Noun+な・Verb[dictionary]・Adjective+んです・のです",
    "〜を〜に任せる": "Noun+を〜に任せる",
    "〜るまでだ": "Verb[dictionary]+までだ",
    "〜ら": "Pronoun+ら",
    "〜ようと思う・〜おうと思う": "Verb[volitional-よう]+と思う",
    "ようと思う": "Verb[volitional-よう]+ようと思う",
    "Verb[よう]": "Verb[volitional-よう]",
    "〜ようとしない": "Verb[volitional-よう]+としない",
    "〜ようではないか": "Verb[volitional-よう]+ではないか",
    "〜やがる": "Verb[masu-stem]+やがる",
    "〜ましょうか": "Verb[ましょう]+か",
    "〜ばこそ": "Noun・Verb[dictionary]・Adjective+ばこそ",
    "〜は〜の一つだ": "Noun・Adjective+は〜の一つだ",
    "〜は〜となっている": "Noun・Adjective+は〜となっている",
    "〜は〜で有名": "Noun・Adjective+は〜で有名",
    "〜のだろうか": "Noun・Verb[dictionary]・Adjective+のだろうか",
    "〜の〜のと": "Verb[dictionary]・Adjective・Noun+の〜のと",
    "〜になる・〜くなる": "Noun・Adjective+になる・くなる",
    "〜にする・〜くする": "Verb[volitional-よう]+にする・くする",
    "〜に〜ない": "Verb[volitional-よう]+に〜ない",
    "〜なり〜なり": "Noun・Verb[dictionary]+なり〜なり",
    "〜ない〜はない": "Noun[negative-modifier]・Verb[ない]・Adjective[negative]+はない",
    "〜と言っても": "Noun・Verb[dictionary]・Adjective+と言っても",
    "〜ところに・〜ところへ": "Verb[ていた・ている]・Noun+ところに・ところへ",
    "〜というのは事実だ": "Noun・Verb[dictionary]・Adjective+というのは事実だ",
    "〜といい〜といい": "Noun+といい〜といい",
    "〜でも[Wh.word]でも": "Noun+でも〜でも",
    "〜でも 〜でも": "Noun+でも〜でも",
    "〜ても〜なくても": "Noun[で]・Verb[て]・Adjective[て]+も〜なくても",
    "〜ても〜ても": "Verb[て]・Adjective[て]+も〜ても",
    "〜てこそ": "Verb[て]+こそ",
    "〜たまでだ": "Verb[た]+までだ",
    "〜ずつ": "Noun+ずつ",
    "ずつ": "Noun+ずつ",
    "〜ざる": "Verb[imperfective]+ざる",
    "〜が〜なら": "Noun+が~なら",
    "〜かは〜によって違う": "Noun・Verb[dictionary]・Adjective+かは~によって違う",
    "〜(の)姿":"Noun+の・Verb[dictionary]・Adjective+姿",
    "〜のうち(で)": "のうち(で) (within, among)",
    "~言わず~と言わず": "Verb[imperfective]+言わず~と言わず",
    "~ばかりか~(さえ)": "Noun・Verb・Adjective+ばかりか~(さえ) (not only ~ but also)",
    "Verb[volitional]とする": "Verb[volitional-よう]+とする",
    "Verb[ない]もの(だろう)か": "Verb[ない]+ものかな・ものだろうか",
    "てもいい": "Verb[て]+もいい (even if ~ is the case, it’s fine)",
    "てはいけない|bunpro": "Verb[て]+はいけない",
    "はいけない|dojg": "Verb[て]+はいけない",
    "れる・られる+ままに": "Verb[れる・られる]~ままに",
    "何[(Number)+Counter]も": "何+Counter+も",
    "だに+しない": "だに~しないい",
    "い-Adj[く]+もなんともない": "い-aAdjective[く]もなんともない",
    "Verb[volitional]+としたが": "Verb[volitional-よう]+としたが",
    "Number/Amount+は": "Number+は",
    "Verb[て]・Noun[で]+B": "Verb[て]・Noun[で]",
    "Verb+て|bunpro": "Verb[て] (and then)",
    "Verb+て+B": "Verb[て] (and then another event)",
    "Verb+てもいい": "Verb[て]+もいい (permission)",
    "RelativeClause": "Relative Clause",
    "RhetoricalQuestion": "Rhetorical Question",
    "VmasuasaNoun": "Verb[masu-stem]+Noun",
    "Vmasu": "Verb[masu-stem] (conjunction)",
    "限り|bunpro": "限り (as long as)",
    "限り|dojg": "限り (as long as)",
    "限り②|dojg": "限り (limited to)",
    "より|bunpro": "より (than, comparison)",
    "より①|dojg": "より (than, comparison)",
    "より|dojg": "より (degree)",
    "より②": "より (from - extent, range)",
    "も": "も (also, too)",
    "も②": "Number+も",
    "は|bunpro": "は (topic marker, as for ~)",
    "は①|dojg": "は (topic marker, as for ~)",
    "は|dojg": "は (emphatic)",
    "に|bunpro": "に (location, direction)",
    "に|dojg": "に (in, with - hypothetical)",
    "そこで": "そこで (therefore)",
    "そこで②|dojg": "そこで (then)",
    "さ|bunpro": "さ (-ness, -ity)",
    "さ|dojg": "さ (casual emphasis)",
    "さ - Casual よ|bunpro": "さ (casual よ)",
    "ことがある|bunpro": "ことがある (there are times when)",
    "ことがある①|dojg": "ことがある (there are times when)",
    "ことがある②|dojg": "ことがある (occassionally)",
    "こと|bunpro": "こと (making a verb a noun)",
    "こと|dojg": "こと (imperative)",
    "こと①|dojg": "こと (abstract thing)",
    "こと②|dojg": "こと (making a verb a noun)",
    "後(の) Noun": "後(の)+Noun",
    "ん (Slang)": "ん (slang)",
    "れる・られる (Potential)": "られる (potential)",
    "る-Verb (Dictionary)": "る-verb (dictionary)",
    "る-Verb (Negative)": "る-verb (negative)",
    "る-Verb (Negative-Past)": "る-verb (negative-past)",
    "る-Verb (Past)": "る-verb (past)",
    "に (Frequency)": "に (frequency)",
    "つ (Slang)": "つ (slang)",
    "さ - Filler": "さ (filler)",
    "さ - Interjection": "さ (interjection)",
    "う-Verb (Dictionary)": "う-verb (dictionary)",
    "う-Verb (Negative)": "う-verb (negative)",
    "う-Verb (Negative-Past)": "う-verb (negative-past)",
    "う-Verb (Past)": "う-verb (past)",
    "い-Adjective (Past)": "い-adjective (past)",
    "い-Adjective (Predicate)": "い-adjective (predicate)",
    "Verbs (Non-past)": "Verbs (non-past)",
    "Adj限りだ": "Adjective+限りだ (extremely)",
    "限りだ": "Adjective+限りだ (extremely)",
    "Adjective+の(は)": "Adjective+の(は) (the one that is)",
    "Adjective+て・Noun+で": "Adjective[て]・Noun[で] (and, because)",
    "Adjective+て+B": "Adjective[て] (and, because)",
    "にして①": "にして (at the point of)",
    "にして②": "にして (and also)",
    "〜かというと ①": "かというと (because)",
    "〜かというと ②": "かというと (if I were to say)",
    "Verb[て]+B①": "Verb[て] (and, non-sequential)",
    "Verb[て]+B②": "Verb[て] (because of)",
    "込む ①": "込む (into)",
    "込む ②": "込む (thoroughly)",
    "べからず・べからざる": "べからず",
    "Causative-Passive": "られる (passive)",
    "られる①": "られる (passive)",
    "られる②": "られる (potential)",
    "(と言)ったらない": "ったらない・といったらない",
    "させる": "Verb[せる・させる]",
    "(っ)きり": "きり",
    "て|dojg": "Verb[て] (and then)",
    "Verb[て]|bunpro": "Verb[て] (casual request)", 
    "なくて": "なくて (not)",
    "始める・はじめる": "はじめる",
    "終わる・おわる": "おわる",
    "難い・にくい": "にくい",
    "易い・やすい": "やすい",
    "に違いない・にちがいない": "に違いない",
    "ものか": "ものか (definitely not)",
    "ものか①": "ものか (definitely not)",
    "ものか②": "ものか (wish)",
    "に関して・関する": "に関する・に関して",
    "下さい・ください": "てください",
    "なんて②": "なんか・なんて",
    "なんて①": "なんて (what)",
    "しか": "しか〜ない",
    "しまう": "てしまう・ちゃう",
    "(の)上で": "上で",
    "(の)代わりに": "代わりに",
    "あげく(に)": "あげく",
    "ある①": "ある (to be)",
    "ある②": "てある",
    "で": "で (for)",
    "で①": "で (at)",
    "で②": "で (by)",
    "で③": "で (because)",
    "で④": "で (by time)",
    "たって": "たって (even if)",
    "(っ)たって①": "(っ)たって (hypothetical, certain outcome)",
    "(っ)たって②": "(っ)たって (hypothetical, futile)",
    "ところだった ①": "ところだった (on the verge of)",
    "ところだった ②": "ところだった (in the middle of)",
    "は言うまでもない ①": "は言うまでもない",
    "は言うまでもなく": "は言うまでもない",
    "くらい ①": "くらい (about)",
    "くらい ②": "くらい (to the extent)",
    "くらい": "くらい (to the extent)",
    "ずっと ①": "ずっと (continuously)",
    "ずっと ②": "ずっと (by far)",
    "あげる①": "あげる (give away)",
    "あげる②": "てあげる",
    "わ②": "わ",
    "風に": "風",
    "際(に)": "際に",
    "間・あいだ(に)": "の間に",
    "過ぎる・すぎる": "すぎる",
    "通り(に)": "とおり",
    "途端(に)": "たとたんに",
    "言うまでもない ②": "言うまでもない",
    "見える・みえる": "見える",
    "みせる": "Verb[て]+みせる",
    "もの(だ)": "ものだ",
    "~ば~ほど": "ば〜ほど",
    "ようでは": "ようでは・ようじゃ",
    "あげる": "あげる (give away)",
    "いる①": "いる (be)",
    "いる②": "ている (~ing)",
    "ている①": "ている (~ing)",
    "ている②": "ている (resultant state)",
    "ている③": "ている (habitual action)",
    "お~下さい": "お〜ください",
    "おおよそ": "およそ・おおよそ",
    "およそ": "およそ・おおよそ",
    "おく": "ておく",
    "か(どうか)": "かどうか",
    "か①": "か (or)",
    "か②": "か (question)",
    "方・かた": "かた",
    "かと思うと": "かと思ったら・かと思うと",
    "かのようだ": "かのようだ・かのように",
    "かのように": "かのようだ・かのように",
    "から①": "から (from)",
    "から③": "から (because)",
    "から②": "てから",
    "から~にかけて": "にかけて",
    "から~に至るまで": "に至るまで",
    "からと言って": "からといって",
    "が②": "が (but)",
    "が①": "が (subject marker)",
    "自分・じぶん①": "自分・じぶん (one's own)",
    "自分・じぶん②": "自分・じぶん (self - independent action)",
    "以上 ①": "以上 (at least)",
    "以上 ②": "以上 (given that)",
    "には及ばない①": "には及ばない (not necessary)",
    "には及ばない②": "には及ばない (inferior in comparison)",
    "ことが出来る・できる": "ことができる",
    "ことは": "ことは〜が",
    "さぞ(かし)": "さぞ",
    "し": "し〜し",
    "する": "する (do)",
    "する①": "する (do)",
    "する③": "がする",
    "する②": "する (have)",
    "する④": "する (cost)",
    "せいで": "せい",
    "そうだ": "そうだ (hear that)",
    "そうだ①": "そうだ (hear that)",
    "そうだ②": "そう",
    "たなり(で)": "たなり・なり",
    "だけで(は)なく〜(も)": "だけでなく(て)〜も",
    "だって": "だって (because)",
    "だって①": "だって (because)",
    "だって②": "だって (too)",
    "要る・いる③": "要る・いる (need)",
    "行く・いく②": "行く・いく (continue)",
    "行く・いく①": "行く・いく (go)",
    "聞こえる・きこえる": "聞こえる",
    "たらどうですか": "たらどう",
    "って①": "って (speaking of)",
    "って②": "って (that)",
    "つもり": "つもりだ",
    "でも・じゃあるまいし": "じゃあるまいし",
    "と": "と (thinking that)",
    "と①": "と (and)",
    "と②": "と (with)",
    "と③": "と (in the manner of)",
    "と④": "と (conditional)",
    "という": "という (called)",
    "というのは~ことだ": "ということだ",
    "というより(は)": "というより",
    "ほうがいい": "たほうがいい",
    "ところだ②": "るところだ",
    "を": "を (object marker)",
    "を①": "を (object marker)",
    "を②": "を (movement through space)",
    "を③": "を (point of departure)",
    "を④": "を (object of an emotion)",
    "ところだ①": "ところだ (in a place where it takes ~ to get to)",
    "とする①": "とする (assume that)",
    "とする②": "とする (feel ~)",
    "と言うのは": "というのは",
    "ないことには": "ないことには〜ない",
    "ないことも・はない": "ないことはない",
    "なぜなら(ば)〜からだ": "なぜなら〜から",
    "なお": "なお (still)",
    "なお①": "なお (still)",
    "なお②": "なお (additionally)",
    "ながら(も)": "ながらも",
    "ならでは(の)": "ならでは",
    "ならない": "てならない",
    "に①": "に (at)",
    "に②": "に (to)",
    "に③": "に (by)",
    "に④": "に (on)",
    "に⑤": "に (to do something)",
    "に⑥": "に (in)",
    "に⑦": "に (toward)",
    "にかたくない・に難くない": "に難くない",
    "にしろ・せよ": "にせよ・にしろ",
    "によって・より": "によって・による",
    "を通して": "を通じて・を通して",
    "にいたっては": "に至っては",
    "において・おける": "において・における",
    "にかかわらず・に関・拘・係わらず": "にかかわらず",
    "につれて・つれ": "につれて",
    "によると": "によると・によれば",
    "にわたって・わたる": "にわたって",
    "に・ともなると": "ともなると・にもなると",
    "に反して・反する": "に反して",
    "に向けて・に向けた": "に向かって・に向けて",
    "に基づいて・基づく": "にもとづいて",
    "に当たって・当たり": "当たり",
    "得る (うる・える)": "得る・得る",
    "に対して・対する": "に対して",
    "に比べると・比べて": "に比べて",
    "に過ぎない": "にすぎない",
    "に応じて・応じた": "に応じて",
    "の①": "の (possessive)",
    "の②": "の (one)",
    "の③": "の (that ~)",
    "の④": "の (it is that ~)",
    "のことだから": "ことだから",
    "のに②": "のに (in order to)",
    "のに①": "のに (despite)",
    "のは〜だ": "のは",
    "出す・だす": "だす",
    "前に・まえに": "まえに",
    "割に(は)": "割に",
    "はず": "はずだ",
    "べきだ": "べき",
    "みる": "てみる",
    "ものなら": "ものなら (if ~ at all)",
    "ものなら①": "ものなら (if ~ at all)",
    "ものなら②": "ものなら (if you were to do)",
    "もらう①": "もらう (receive)",
    "もらう": "もらう (receive)",
    "もらう②": "もらう (have someone do)",
    "らしい": "らしい (seems)",
    "らしい ①": "らしい (seems)",
    "らしい ②": "らしい (typical of)",
    "をおいてほかに(は)〜ない": "をおいてほかに〜ない",
    "をはじめ(として)": "をはじめ",
    "よう①": "よう (the way to)",
    "よう②": "よう (probably)",
    "ように①": "ように (so that)",
    "ように": "ように (so that)",
    "ように②": "ように (like)",
    "ように言う": "ようにいう",
    "一応 ②": "一応 (for the time being)",
    "一応": "一応 (for the time being)",
    "一応 ①": "一応 (just in case)",
    "一方(だ)": "一方だ",
    "一方で(は)~他方で(は)": "一方で",
    "確かに~が": "確かに",
    "〜てやる": "やる (send)",
    "やる①": "やる (send)",
    "やる②": "やる (knowing that it will cause someone trouble)",
    "や否や・やいなや": "や否や",
    "一旦・いったん": "一旦",
    "故に・ゆえに": "ゆえに",
    "くる": "くる (come)",
    "来る・くる①": "くる (come)",
    "来る・くる②": "くる (come about)",
    "上(に)": "上に",
    "欲しい・ほしい①": "ほしい (want something)",
    "欲しい・ほしい②": "ほしい (want someone to do something)",
    "に加えて": "加えて",
    "呉れる・くれる①": "呉れる・くれる (give)",
    "呉れる・くれる②": "呉れる・くれる (do something for someone)",
    "嫌いだ・きらいだ": "きらい",
    "時・とき": "とき",
    "為(に)・ため(に)": "ため(に)",
}

def read_file_list(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

def read_yaml(input_file: str, type) -> dict:
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read().replace("  ", " ").replace("&emsp;", " ").replace("　", " ").replace(" ​"," ").replace("～", "〜").replace("+ ", "+").replace(" +", "+").replace("［","[").replace("］","]").replace("？", "?").replace("（", "(").replace("）",")")
        point = yaml.safe_load(content)
        
        point[f"{type}_grammar_point"] = point["grammar_point"]
        point[f"source"] = input_file
        return point

def parse_translation_key(key):
    """Parse a translation key into the grammar point and optional source type."""
    if '|' in key:
        grammar_point, source = key.split('|', 1)
        return grammar_point, source
    return key, None

def validate_translations(bunpro_list, dojg_list, translations):
    """Validate that all translation keys match an existing grammar point."""
    # Collect all grammar points from both sources
    all_grammar_points = {item['grammar_point'] for item in bunpro_list}
    all_grammar_points.update(item['grammar_point'] for item in dojg_list)

    # Validate each translation key
    for trans_key in translations:
        grammar_point, specified_source = parse_translation_key(trans_key)
        if specified_source and specified_source not in ('bunpro', 'dojg'):
            raise ValueError(f"Invalid source type in translation key {trans_key}")
        
        if grammar_point not in all_grammar_points:
            raise ValueError(f"No matching grammar point found for translation key: {grammar_point}")

def apply_translations(yaml_list, translations, used_translations, source_type=None):
    """
    Apply translations to grammar points, respecting source-specific translations.
    """
    for item in yaml_list:
        current_point = item['grammar_point']
        
        # Check direct match first
        direct_key = f"{current_point}|{source_type}" if source_type else current_point
        if direct_key in translations:
            item['grammar_point'] = translations[direct_key]
            used_translations.add(direct_key)
        # If no source-specific match, try general match
        elif current_point in translations and '|' not in current_point:
            item['grammar_point'] = translations[current_point]
            used_translations.add(current_point)

    return yaml_list

def clean_sentence(sentence):
    result = sentence.strip()
    if result.startswith("'") and result.endswith("'"):
        result = result[1:-1]
    if result.startswith("'") and result.endswith("'"):
        result = result[1:-1]
    return result

def clean_sentences(sentences):
    result = []
    for sentence in sentences:
        result.append({
            "japanese": clean_sentence(sentence['japanese']),
            "english": clean_sentence(sentence['english'])
        })
    return result

def trim_elements(merged_list):
    trimmed_list = []
    for item in merged_list:
        trimmed_item = {'grammar_point': item['grammar_point'], 'rank': 0}
        
        if 'meaning' in item:
            trimmed_item['meaning'] = clean_sentence(item['meaning'])
        
        if 'bunpro' in item and item['bunpro'] is not None:
            bunpro_trimmed = { }
            for key in item['bunpro']:
                bunpro_trimmed[key] = item['bunpro'][key]
            bunpro_trimmed['grammar_point'] = item['bunpro']['bunpro_grammar_point']
            del bunpro_trimmed['bunpro_grammar_point']
            trimmed_item['bunpro'] = bunpro_trimmed
        
        if 'dojg' in item and item['dojg'] is not None:
            dojg_trimmed = { }
            for key in item['dojg']:
                 dojg_trimmed[key] = item['dojg'][key]
            dojg_trimmed['grammar_point'] = item['dojg']['dojg_grammar_point']
            del dojg_trimmed['dojg_grammar_point']
            trimmed_item['dojg'] = dojg_trimmed

        
        bunpro_rank = -1
        if 'bunpro' in trimmed_item:
            bunpro = trimmed_item['bunpro']
            level = bunpro['jlpt']
            if level == 'N0':
                bunpro_rank = 5
            elif level == 'N1':
                bunpro_rank = 4
            elif level == 'N2':
                bunpro_rank = 3
            elif level == 'N3':
                bunpro_rank = 2
            elif level == 'N4':
                bunpro_rank = 1
            elif level == 'N5':
                bunpro_rank = 0
            else:
                raise ValueError(f"Unexpected bunpro jlpt level: {level}")
            
        dojg_rank = -1
        if 'dojg' in trimmed_item:
            dojg = trimmed_item['dojg']
            level = dojg['level']
            if level == 'Advanced':
                dojg_rank = 5
            elif level == 'Intermediate':
                dojg_rank = 3
            elif level == 'Basic':
                dojg_rank = 0
            else:
                raise ValueError(f"Unexpected DOJG level: {level}")
        
        if dojg_rank == -1:
            dojg_rank = bunpro_rank
            
        if bunpro_rank == -1:
            bunpro_rank = dojg_rank

        rank = bunpro_rank + dojg_rank
        trimmed_item['rank'] = rank

        trimmed_list.append(trimmed_item)
    
    return trimmed_list


def merge_lists(list_one, list_two, list_name_one='one', list_name_two='two'):
    merged_dict = {}

    # Add items from the first list
    for item in list_one:
        grammar_point = item['grammar_point']
        if grammar_point not in merged_dict:
            merged_dict[grammar_point] = {'grammar_point': grammar_point, list_name_one: item, list_name_two: None}
        else:
            merged_dict[grammar_point][list_name_one] = item

    # Add items from the second list
    for item in list_two:
        grammar_point = item['grammar_point']
        if grammar_point not in merged_dict:
             merged_dict[grammar_point] = {'grammar_point': grammar_point, list_name_one: None, list_name_two: item}
        else:
            merged_dict[grammar_point][list_name_two] = item

    # Convert the dictionary back to a list
    merged_list = list(merged_dict.values())

    # Sort the merged list by 'grammar_point'
    sorted_merged = sorted(merged_list, key=lambda x: x['grammar_point'])

    return sorted_merged


def is_merged(item):
    has_bunpro = 'bunpro' in item and item['bunpro'] is not None
    has_dojg = 'dojg' in item and item['dojg'] is not None

    return has_bunpro and has_dojg

def generate_statistics(merged_list):
    merged_count = 0
    dojg_only_count = 0
    bunpro_only_count = 0

    for item in merged_list:
        has_bunpro = 'bunpro' in item and item['bunpro'] is not None
        has_dojg = 'dojg' in item and item['dojg'] is not None
        if has_bunpro and has_dojg:
            merged_count += 1
        elif has_bunpro:
            bunpro_only_count += 1
        elif has_dojg:
            dojg_only_count += 1

    return {
        'merged_count': merged_count,
        'dojg_only_count': dojg_only_count,
        'bunpro_only_count': bunpro_only_count,
        'total_count': len(merged_list)
    }

def remove_merged_grammar_points(merged_list):
    """
    Removes the grammar points that have both bunpro and dojg points. 
    """
    filtered_list = []

    for item in merged_list:
        if not is_merged(item):
            filtered_list.append(item)

    return filtered_list

def find_closest_match(dojg_point, bunpro_points):
    matches = difflib.get_close_matches(dojg_point, bunpro_points, n=1, cutoff=0.0)
    return matches[0] if matches else "No match found"

def label_closest_matches(data):
    bunpro_points = {item['grammar_point']: item['bunpro']['grammar_point'] for item in data if 'bunpro' in item}
    bunpro_list = list(bunpro_points.keys())
    
    for entry in data:
        if 'dojg' in entry:
            dojg_point = entry['dojg']['grammar_point']
            closest_bunpro = find_closest_match(dojg_point, bunpro_list)
            entry['dojg']['closest_bunpro'] = bunpro_points.get(closest_bunpro, "No match found")

def apply_missing_meanings(merged_data, missing_meanings):
    used_meanings = set()  # Track which meanings were used

    for entry in merged_data:
        grammar_point = entry['grammar_point']
        if grammar_point in missing_meanings:
            used_meanings.add(grammar_point)  # Mark the meaning as used
            if 'dojg' in entry and entry['dojg'] is not None:
                entry['dojg']['meaning'] = missing_meanings[grammar_point]
            if 'bunpro' in entry and entry['bunpro'] is not None:
                entry['bunpro']['meaning'] = missing_meanings[grammar_point]

    # Check for blank meanings after applying missing meanings
    for entry in merged_data:
        if 'dojg' in entry and entry['dojg'] is not None and entry['dojg']['meaning'] == '':
            raise ValueError(f"Missing meaning for grammar point: {entry['grammar_point']} (DOJG)")
        if 'bunpro' in entry and entry['bunpro'] is not None and entry['bunpro']['meaning'] == '':
            raise ValueError(f"Missing meaning for grammar point: {entry['grammar_point']} (Bunpro)")

    # Check for unused meanings
    unused_meanings = set(missing_meanings.keys()) - used_meanings
    if unused_meanings:
        raise ValueError(f"Unused missing meanings: {unused_meanings}")
    
VALID_VERB_CONJUGATIONS = {
    'masu-stem', 'て', 'た', 'ている', 
    'volitional-よう', 
    'ない', 
    'せる・させる',
    'れる・られる', 'dictionary', 'negative', 'negative-past', 'past', 'た・ている', 
    'ていた・ている',
    'ば-conditional',
    'ましょう', # polite volitional
    'imperfective', # mizenkei
    'ないで' # negative-te
}

VALID_ADJECTIVE_CONJUGATIONS = {
    'く', 'て', 'い', 'past', 'predicate', 'negative'
}

VALID_NOUN_MODIFIERS = {
    'で', 'に', 'へ', 'と', 'から', 'まで', 'より', 'negative-modifier'
}

def verify_grammar_point_name(grammar_point: str) -> tuple[bool, str]:
    # Early returns
    if not grammar_point:
        return False, "Grammar point cannot be empty"
    
    # Combine all character checks into one regex
    if re.search(r'[①②③④⑤⑥⑦⑧⑨⑩/]', grammar_point):
        return False, "Grammar point cannot contain numbered circles (①, ②, etc.) or forward slashes (/)"
    
    # Check brackets and parentheses balance in one pass
    stack = []
    for char in grammar_point:
        if char in '([':
            stack.append(char)
        elif char in ')]':
            if not stack:
                return False, "Unbalanced brackets/parentheses"
            if (char == ')' and stack[-1] != '(') or (char == ']' and stack[-1] != '['):
                return False, "Mismatched brackets/parentheses"
            stack.pop()
    if stack:
        return False, "Unbalanced brackets/parentheses"

    # Combine all bracket pattern checks into one regex
    pattern = r'(Verb|Adjective|Noun)\[(.*?)\]'
    for match in re.finditer(pattern, grammar_point):
        type_, conjugation = match.groups()
        if not conjugation:
            return False, "Empty brackets are not allowed"
        
        valid_set = {
            'Verb': VALID_VERB_CONJUGATIONS,
            'Adjective': VALID_ADJECTIVE_CONJUGATIONS,
            'Noun': VALID_NOUN_MODIFIERS
        }[type_]
        
        if conjugation not in valid_set:
            return False, f"Invalid {type_.lower()} conjugation: {conjugation}"

    # Check final parentheses contents
    if grammar_point.endswith(')'):
        last_paren_match = re.search(r'\(([^)]+)\)$', grammar_point)
        if last_paren_match:
            english_text = last_paren_match.group(1)
            # Split the text into words and check each one
            words = english_text.split()
            for word in words:
                # Skip the word "I"
                if word != "I" and any(c.isupper() for c in word):
                    return False, "English in final parentheses must be lowercase (except for 'I')"
            if any(char.isdigit() for char in english_text):
                return False, "English description cannot contain numbers"

    # Check separators in one pass
    for sep in ('+', '~', '〜'):
        if sep in grammar_point:
            if any(not part.strip() for part in grammar_point.split(sep)):
                return False, f"'{sep}' must have content on both sides"

    return True, ""
    
def validate_grammar_points(merged_data):
    """
    Validates grammar points for formatting issues.
    """
    
    for item in merged_data:
        valid,error = verify_grammar_point_name(item['grammar_point'])
        if not valid:
            raise ValueError(f"Invalid grammar point name: {item['grammar_point']} ({error})")

    
def get_all_grammar_points(merged_data):
    """Get all grammar points with their meanings."""
    all_points = []
    
    for item in merged_data:
        point = item['grammar_point']
        
        # Get meaning from either source, prioritizing bunpro if both exist
        meaning = {}
        bunpro = None
        dojg = None
        if 'bunpro' in item and item['bunpro'] and 'meaning' in item['bunpro']:
            bunpro = item['bunpro']['meaning']
        if 'dojg' in item and item['dojg'] and 'meaning' in item['dojg']:
            dojg = item['dojg']['meaning']
        if bunpro is not None and dojg is not None and bunpro == dojg:
            meaning['meaning'] = bunpro
        elif bunpro is not None and dojg is not None:
            meaning['bunpro'] = bunpro
            meaning['dojg'] = dojg
        elif bunpro is not None:
            meaning['meaning'] = bunpro
        elif dojg is not None:
            meaning['meaning'] = dojg

        point = { point: meaning }
        all_points.append(point)
    
    return { 
        "grammar_point_naming_rules": grammar_point_name_rules,
        "grammar_points": sorted(all_points, key=lambda x: list(x.keys())[0])
    }

def main():
    if len(sys.argv) != 5:
        print("Usage: merge_grammars.py <bunpro_file_list> <dojg_file_list> <output_file> <output_dir>")
        print("   bunpro_file_list and dojg_file_list contain lists of YAML files to merge")
        print("ARGS", sys.argv)
        sys.exit(1)

    bunpro_file = sys.argv[1]
    dojg_file = sys.argv[2]
    output_file = sys.argv[3]
    output_dir = sys.argv[4]

    bunpro_files = read_file_list(bunpro_file)
    dojg_files = read_file_list(dojg_file)

    bunpro_yamls = [read_yaml(f, 'bunpro') for f in bunpro_files]
    dojg_yamls = [read_yaml(f, 'dojg') for f in dojg_files]

    # First validate all translations
    validate_translations(bunpro_yamls, dojg_yamls, grammar_point_name_translations)

    # Apply translations to the grammar points before merging
    used_translations = set()
    bunpro_yamls = apply_translations(bunpro_yamls, grammar_point_name_translations, used_translations, 'bunpro')
    dojg_yamls = apply_translations(dojg_yamls, grammar_point_name_translations, used_translations, 'dojg')
    unused_translations = set(grammar_point_name_translations.keys()) - used_translations
    if unused_translations:
        raise ValueError(f"Unused translation keys: {unused_translations}")

    merged = merge_lists(bunpro_yamls, dojg_yamls, list_name_one='bunpro', list_name_two='dojg')

    statistics = generate_statistics(merged)
    apply_missing_meanings(merged, missing_meanings)

    removed = trim_elements(merged)  
    #removed = remove_merged_grammar_points(removed)
    #label_closest_matches(removed)
    all_grammar_points = get_all_grammar_points(removed)

    # Write the individual YAML files
    for grammar_point in removed:
        filename = f"{grammar_point['grammar_point']}.yaml"
        grammar_point_file = os.path.join(output_dir, filename)
        with open(grammar_point_file, 'w') as f:
            dump_yaml_file(grammar_point, f)

    # Combine statistics and merged data
    output_data = {
        'statistics': statistics,
        'merged_data': removed,
        'all_grammar_points': all_grammar_points
    }

    with open(output_file, 'w') as f:
        dump_yaml_file(output_data, f)

    validate_grammar_points(merged)

if __name__ == "__main__":
    main()
