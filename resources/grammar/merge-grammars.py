import sys
import yaml
from dumpyaml import dump_yaml_file
import difflib

missing_meanings = {
    "Relative clause": "Modifies a noun by providing additional descriptive information about it." ,
    "Rhetorical question": "A question asked for effect, not requiring an answer, often used to express strong emotion or make a point.",
    "Verb[masu-stem] noun": "Treats a verb in the masu-stem form as a noun, often to describe an action or state as a concept.",
    "お": "Honorific prefix for nouns and verbs, adds politeness and respect.",
    "お~だ": "Polite copula, equivalent to 'desu' but often used for adjectives or states related to the listener.", 
    "お〜する": "Humble verb form, used when the speaker performs an action for someone of higher status.",
    "お〜になる": "Honorific verb form, used when referring to actions or states of someone of higher status.",
    "かい": "Informal sentence ending particle, similar to 'ka' but softer and more casual, often used by males.",
    "が (subject marker)": "Particle marking the grammatical subject of the sentence.", 
    "ことがある (there are times when)":  "Indicates that there are times an action or event happens.", 
    "ことがある (occassionally)": "Indicates an action or event happens occasionally.",
    "しい": "Suffix for i-adjectives, indicates a strong emotion or feeling.",
    "だい": "Informal sentence ending particle, emphasizes a question or request, often used by males.",
    "っけ": "Sentence ending particle, expresses uncertainty or seeks confirmation, 'wasn't it?', 'didn't we?'", 
    "に (in/with - hypothetical)": "Marks a hypothetical situation or condition.",
    "は〜が": "Sentence structure emphasizing a contrast, 'A is (topic), but B (focus)'.",
    "は〜だ": "Basic sentence structure, identifies the topic (A) and provides information (B) about it.", 
    "わ": "Sentence ending particle, mainly used by females, adds a soft and feminine tone, can express emphasis or emotion.",
    "を (object marker)":  "Particle marking the direct object of a transitive verb.",
    "を (object of an emotion)": "Indicates the object or cause of an emotion or feeling.", 
    "を (point of departure)": "Indicates the point from which someone or something departs or separates.",
    "君・くん": "Suffix added to names, primarily for males, expresses familiarity or a slightly informal tone." 
}

# Rules
# - Instead of using numbers like やる①, use descriptive like やる (send)
# - English should be lower-case unless it's the first word in English
grammar_point_name_translations = {
    "れる・られる+ままに": "れる・られる~ままに",
    "何[(Number)+Counter]も": "何 counter も",
    "なん+counter+か": "なん counter か",
    "な-Adjective+Noun": "な-adjective noun",
    "だに+しない": "だに~しないい",
    "がある+Noun": "[がある]noun",
    "Verb[て]+みせる": "Verb[て]みせる",
    "い-Adj[く]+もなんともない": "い-adjective[く]もなんともない",
    "い-Adjective+Noun": "い-adjective noun",
    "Verb[volitional]+としたが": "Verb[volitional]としたが",
    "Question-phrase+か": "Question[か]",
    "Particle+の": "Particle[の]",
    "Number+しか〜ない|bunpro": "Number[しか]〜ない",
    "Noun+まで": "Noun[まで]",
    "Noun＋型": "Noun[型]",
    "Verb+だに": "Verb[だに]",
    "Number/Amount+は": "Number[は]",
    "Verb[た・ている]+Noun": "Verb[た・ている] noun",
    "Verb[て]・Noun[で]+B": "Verb[て]・noun[で]",
    "Verb+て|bunpro": "Verb[て] (and then)",
    "Verb+て+B": "Verb[て] (and then another event)",
    "Verb+てもいい": "Verb[てもいい]",
    "Verb+まで": "Verb[まで]",
    "Verb+にいく": "Verb[にいく]",
    "RelativeClause": "Relative clause",
    "RhetoricalQuestion": "Rhetorical question",
    "VmasuasaNoun": "Verb[masu-stem] noun",
    "Vmasu": "Verb[masu-steam] conjunction",
    "限り|bunpro": "限り (as long as)",
    "限り|dojg": "限り (as long as)",
    "限り②|dojg": "限り (limited to)",
    "より|bunpro": "より (than/comparison)",
    "より①|dojg": "より (than/comparison)",
    "より|dojg": "より (degree)",
    "より②": "より (from - extent/range)",
    "も": "も (also/too)",
    "も②": "Number[も] (as many as)",
    "Number+も": "Number[も] (as many as)",
    "は|bunpro": "は (topic marker, as for ~)",
    "は①|dojg": "は (topic marker, as for ~)",
    "は|dojg": "は (emphatic)",
    "に|bunpro": "に (location/direction)",
    "に|dojg": "に (in/with - hypothetical)",
    "そこで": "そこで (therefore)",
    "そこで②|dojg": "そこで (then)",
    "さ|bunpro": "さ (-ness/-ity)",
    "さ|dojg": "さ (casual emphasis)",
    "さ - Casual よ|bunpro": "さ (casual よ)",
    "ことがある|bunpro": "ことがある (there are times when)",
    "ことがある①|dojg": "ことがある (there are times when)",
    "ことがある②|dojg": "ことがある (occassionally)",
    "こと|bunpro": "こと (making a verb a noun)",
    "こと|dojg": "こと (imperative)",
    "こと①|dojg": "こと (abstract thing)",
    "こと②|dojg": "こと (making a verb a noun)",
    "後(の) Noun": "後(の) noun",
    "ん (Slang)": "ん (slang)",
    "れる・られる (Potential)": "られる (potential)",
    "る-Verb (Dictionary)": "る-verb (dictionary)",
    "る-Verb (Negative)": "る-verb (negative)",
    "る-Verb (Negative-Past)": "る-verb (negative-past)",
    "る-Verb (Past)": "る-verb (past)",
    "に (Frequency)": "に (frequency)",
    "つ (Slang)": "つ slang)",
    "さ - Filler": "さ (filler)",
    "さ - Interjection": "さ (interjection)",
    "う-Verb (Dictionary)": "う-verb (dictionary)",
    "う-Verb (Negative)": "う-verb (negative)",
    "う-Verb (Negative-Past)": "う-verb (negative-past)",
    "う-Verb (Past)": "う-verb (past)",
    "い-Adjective (Past)": "い-adjective (past)",
    "い-Adjective (Predicate)": "い-adjective (predicate)",
    "Verbs (Non-past)": "Verbs (non-past)",
    "Adj限りだ": "Adjective[限りだ] (extremely)",
    "限りだ": "Adjective[限りだ] (extremely)",
    "Adjective+の(は)": "Adjective[の] (the one that is)",
    "Adjective+て・Noun+で": "Adjective[て]・noun[で] (and/because)",
    "Adjective+て+B": "Adjective[て] (and/because)",
    "にして①": "にして (at the point of)",
    "にして②": "にして (and also)",
    "〜かというと ①": "〜かというと (because)",
    "〜かというと ②": "〜かというと (if I were to say)",
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
    "〜わ〜わ": "わ〜わ",
    "〜やら〜やら": "やら〜やら",
    "風に": "風",
    "際(に)": "際に",
    "間・あいだ(に)": "の間に",
    "過ぎる・すぎる": "すぎる",
    "通り(に)": "とおり",
    "途端(に)": "たとたんに",
    "言うまでもない ②": "言うまでもない",
    "見える・みえる": "見える",
    "だに": "Verb[だに]",
    "みせる": "Verb[て]みせる",
    "のだ": "〜んです・のです",
    "もの(だ)": "ものだ",
    "~ば~ほど": "ば〜ほど",
    "〜であれ〜であれ": "であれ〜であれ",
    "〜でも[Wh.word]でも": "〜でも 〜でも",
    "〜も[V]ば〜も[V]": "も〜ば〜も",
    "と言っても": "〜と言っても",
    "ばこそ": "〜ばこそ",
    "ようでは": "ようでは・ようじゃ",
    "ようと思う": "〜ようと思う・〜おうと思う",
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
    "ずつ": "〜ずつ",
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
    "はいけない": "てはいけない",
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
        content = file.read().replace("’", "''") .replace("  ", " ").replace("&emsp;", " ").replace("　", " ").replace(" ​"," ").replace("～", "〜").replace("+ ", "+").replace(" +", "+").replace("［","[").replace("］","]").replace("？", "?").replace("（", "(").replace("）",")")
        point = yaml.safe_load(content)
        
        point[f"{type}_grammar_point"] = point["grammar_point"]
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

def trim_elements(merged_list):
    trimmed_list = []
    for item in merged_list:
        trimmed_item = {'grammar_point': item['grammar_point']}
        
        if 'meaning' in item:
            trimmed_item['meaning'] = item['meaning']
        
        if 'bunpro' in item and item['bunpro'] is not None:
            bunpro_trimmed = {
                'grammar_point': item['bunpro']['bunpro_grammar_point'], 
                # 'url': item['bunpro']['url']
                }
            if 'meaning' in item['bunpro']:
                bunpro_trimmed['meaning'] = item['bunpro']['meaning']
            if 'examples' in item['bunpro']:
                bunpro_trimmed['examples'] = item['bunpro']['examples'][:10]
            trimmed_item['bunpro'] = bunpro_trimmed
        
        if 'dojg' in item and item['dojg'] is not None:
            dojg_trimmed = {'grammar_point': item['dojg']['dojg_grammar_point']}
            if 'meaning' in item['dojg']:
                dojg_trimmed['meaning'] = item['dojg']['meaning']
            if 'examples' in item['dojg']:
                dojg_trimmed['examples'] = item['dojg']['examples'][:10]
            trimmed_item['dojg'] = dojg_trimmed
        
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
    
def find_inconsistent_parentheticals(grammar_points):
    """
    Find pairs of grammar points where one has a parenthetical description and the other doesn't,
    but they share the same Japanese text.
    """
    # Group by the part before any parentheses
    point_groups = {}
    for point in grammar_points:
        # Split on first '(' if it exists
        base_point = point.split(' (')[0]
        if base_point not in point_groups:
            point_groups[base_point] = []
        point_groups[base_point].append(point)
    
    # Find groups with inconsistent parenthetical usage
    inconsistent_pairs = []
    for base_point, variants in point_groups.items():
        if len(variants) > 1:
            has_parenthetical = any('(' in v for v in variants)
            missing_parenthetical = any('(' not in v for v in variants)
            if has_parenthetical and missing_parenthetical:
                inconsistent_pairs.append(sorted(variants))
    
    return inconsistent_pairs
    
def validate_grammar_points(merged_data):
    """
    Validates grammar points for formatting issues.
    """
    numbered_points = []
    capitalization_points = []
    adj_points = []
    plus_points = []
    uncapitalized_english = []
    
    for item in merged_data:
        grammar_point = item['grammar_point']

        # Check for numbered variants
        if any(char in grammar_point for char in "①②③④⑤⑥⑦"):
            numbered_points.append(grammar_point)
            
        # Check for any plus signs
        if '+' in grammar_point:
            plus_points.append(grammar_point)

        # Check capitalization in subsequent words
        words = grammar_point.split()
        for word in words[1:]:  # Skip first word
            if word[0].isupper() and word != word[0] + word[1:].lower():
                capitalization_points.append(grammar_point)
                break

        # Check for 'Adj' not at start
        if "Adj" in words[1:]:
            adj_points.append(grammar_point)
            
        # If first word starts with English letter, it must be capitalized
        if words[0][0].isascii() and words[0][0].isalpha() and not words[0][0].isupper():
            uncapitalized_english.append(grammar_point)

    # Check for inconsistent parentheticals
    inconsistent_pairs = find_inconsistent_parentheticals(
        [item['grammar_point'] for item in merged_data]
    )
    
    errors = []
    if numbered_points:
        errors.append(f"Found numbered grammar points: {numbered_points}")
    if plus_points:
        errors.append(f"Found grammar points containing '+': {plus_points}")
    if capitalization_points:
        errors.append(f"Found grammar points with incorrect capitalization after first word: {capitalization_points}")
    if adj_points:
        errors.append(f"Found grammar points using 'Adj' not at start: {adj_points}")
    if uncapitalized_english:
        errors.append(f"Found grammar points with uncapitalized English first word: {uncapitalized_english}")
    if inconsistent_pairs:
        errors.append(f"Found grammar points with inconsistent parenthetical descriptions: {inconsistent_pairs}")
        
    if errors:
        raise ValueError("\n".join(errors))
    
def get_all_grammar_points(merged_data):
    """Get all grammar points with their meanings."""
    all_points = []
    
    for item in merged_data:
        point = item['grammar_point']
        
        # Get meaning from either source, prioritizing bunpro if both exist
        meaning = ""
        if 'bunpro' in item and item['bunpro'] and 'meaning' in item['bunpro']:
            meaning += " --" + item['bunpro']['meaning']
        if 'dojg' in item and item['dojg'] and 'meaning' in item['dojg']:
            meaning += " --" + item['dojg']['meaning']
            
        if meaning:
            point = f"{point}: {meaning}"
            
        all_points.append(point)
    
    return sorted(all_points)

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
