import sys
import yaml
from dumpyaml import dump_yaml_file
import difflib

#   merged_count: 258
#   dojg_only_count: 368
#   bunpro_only_count: 670

# Add a dictionary to specify forced resolutions
forced_resolutions = {
    "(っ)たって①": "dojg", 
    "(っ)たって②": "dojg", 
    "Adjective+て+B": "bunpro",
    "Adjective+て・Noun+で": "bunpro",
    "Adjective+の(は)": "bunpro",
    "Noun+まで": "bunpro",
    "Noun＋型": "bunpro",
    "Number/Amount+は": "bunpro",
    "Particle+の": "bunpro",
    "Question-phrase+か": "bunpro",
    "Verb+て+B": "bunpro",
    "Verb+てもいい": "bunpro",
    "Verb[volitional]とする": "bunpro",
    "Imperative": "dojg",
    "RelativeClause": "dojg",
    "RhetoricalQuestion": "dojg",
    "Imperative": "dojg",
    "Verb+て": "bunpro",
    "Verb+にいく": "bunpro",
    "Verb+まで": "bunpro",
    "Verb[volitional]+としたが": "bunpro",
    "Verb[て]+B①": "bunpro",
    "Verb[て]+B②": "bunpro",
    "Verb[て]・Noun[で]+B": "bunpro",
    "Verb[ない]もの(だろう)か": "bunpro",
    "Verb[ないで]": "bunpro",
    "Verb[よう]": "bunpro",
    "Verbs (Non-past)": "bunpro",
    "Verb[た・ている]+Noun": "bunpro",
    "Verb[れる・られる]": "bunpro",
    "Vmasu": "dojg",
    "VmasuasaNoun": "dojg",
    "~ばかりか~(さえ)": "dojg",
    "~言わず~と言わず": "dojg",
    "〜(の)姿": "bunpro",
    "〜かというと ①": "bunpro",
    "〜かというと ②": "bunpro",
    "〜かは〜によって違う": "bunpro",
    "〜が〜なら": "dojg",
    "〜ざる": "bunpro",
    "〜ずつ": "bunpro",
    "〜たまでだ": "bunpro",
    "〜てこそ": "bunpro",
    "〜ても〜ても": "dojg",
    "〜ても〜なくても": "bunpro",
    "〜てやる": "bunpro",
    "〜といい〜といい": "dojg",
    "〜というのは事実だ": "bunpro",
    "〜ところに・〜ところへ": "bunpro",
    "〜ない〜はない": "bunpro",
    "〜なり〜なり": "bunpro",
    "〜にする・〜くする": "bunpro",
    "〜になる・〜くなる": "bunpro",
    "〜の〜のと": "dojg",
    "〜のうち(で)": "bunpro",
    "〜のだろうか": "bunpro",
    "〜は〜で有名": "bunpro",
    "〜は〜となっている": "bunpro",
    "〜は〜の一つだ": "bunpro",
    "ひいては": "dojg",
    "ひつようがある": "bunpro",
    "ひとつ": "dojg",
    "びる": "bunpro",
    "〜ましょうか": "bunpro",
    "〜やがる": "bunpro",
    "〜ようではないか": "bunpro",
    "〜ようとしない": "bunpro",
    "〜ら": "bunpro",
    "〜るまでだ": "bunpro",
    "〜を〜に任せる": "bunpro",
    "〜代": "bunpro",
    "〜得ない": "bunpro",
    "あえて": "dojg",
    "あそこ": "bunpro",
    "あたかも": "dojg",
    "あっての": "bunpro",
    "あながち〜ない": "dojg",
    "あの": "bunpro",
    "あまり〜ない": "bunpro",
    "あまりに": "bunpro",
    "あり": "bunpro",
    "あれ": "bunpro",
    "ある (to be)": "dojg",
    "あわよくば": "bunpro",
    "い": "bunpro",
    "い-Adj[く]+もなんともない": "bunpro",
    "い-Adjective (Past)": "bunpro",
    "い-Adjective (Predicate)": "bunpro",
    "い-Adjective くなかった": "bunpro",
    "い-Adjective+Noun": "bunpro",
    "い-Adjectives": "bunpro",
    "い-Adjectives くない": "bunpro",
    "いい": "bunpro",
    "いか": "bunpro",
    "いかに": "dojg",
    "いかにも": "dojg",
    "いかん〜ず": "bunpro",
    "いがい": "bunpro",
    "いきなり": "bunpro",
    "いくら": "dojg",
    "いくら〜でも": "bunpro",
    "いずれも": "bunpro",
    "いたす": "bunpro",
    "いつの間にか": "bunpro",
    "いよいよ": "bunpro",
    "いらっしゃる": "bunpro",
    "がいる": "bunpro",
    "いる (be)": "dojg",
    "う-Verb (Dictionary)": "bunpro",
    "う-Verb (Negative)": "bunpro",
    "う-Verb (Negative-Past)": "bunpro",
    "う-Verb (Past)": "bunpro",
    "お": "dojg",
    "お~だ": "dojg",
    "お〜願う": "bunpro",
    "おかげで": "bunpro",
    "おきに": "bunpro",
    "おそらく": "bunpro",
    "おまけに": "bunpro",
    "および": "bunpro",
    "おり": "dojg",
    "か~か": "dojg",
    "か〜ないかのうちに": "bunpro",
    "かえって": "dojg",
    "かけ": "bunpro",
    "かたがた": "bunpro",
    "かたわら": "bunpro",
    "かと言うと": "dojg",
    "かなり": "bunpro",
    "かねない": "bunpro",
    "からある": "bunpro",
    "からこそ": "bunpro",
    "からする": "bunpro",
    "からすると・からすれば": "bunpro",
    "から見ると": "bunpro",
    "からなる": "dojg",
    "から言うと": "bunpro",
    "から言って": "dojg",
    "かれ〜かれ": "bunpro",
    "か何か": "bunpro",
    "がある": "bunpro",
    "がある+Noun": "bunpro",
    "がいい": "bunpro",
    "がけに": "bunpro",
    "く": "dojg",
    "こうした": "dojg",
    "こと (thing)": "dojg",
    "こと (to~)": "dojg",
    "ことがある (there are times)": "dojg",
    "ことで": "dojg",
    "ことによる": "dojg",
    "この上ない": "dojg",
    "ごとし": "dojg",
    "さも": "dojg",
    "すぐ": "dojg",
    "しい": "dojg",



}

grammar_point_name_translations = {
    "べからず・べからざる": "べからず",
    "られる②": "れる・られる (Potential)",
    "(と言)ったらない": "ったらない・といったらない",
    "させる": "Verb[せる・させる]",
    "(っ)きり": "きり",
    "て": "Verb[て]",
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
    "Number+しか〜ない": "しか〜ない",
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
    "〜やら〜やら": "やら～やら",
    "風に": "風",
    "際(に)": "際に",
    "限りだ": "Adj限りだ",
    "限り②": "限り (only until)",
    "間・あいだ(に)": "の間に",
    "過ぎる・すぎる": "すぎる",
    "通り(に)": "とおり",
    "途端(に)": "たとたんに",
    "言うまでもない ②": "言うまでもない",
    "見える・みえる": "見える",
    "だに": "Verb+だに",
    "られる①": "Causative-Passive",
    "も②": "も (as many as)",
    "Number+も": "も (as many as)",
    "みせる": "Verb[て]+みせる",
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
    "いる②": "ている (~ing)",
    "ている①": "ている (~ing)",
    "いる①": "いる (be)",
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
    "こと①": "こと (thing)",
    "こと②": "こと (to~)",
    "ことがある①": "ことがある",
    "ことがある②": "ことがある (there are times)",
    "ことが出来る・できる": "ことができる",
    "ことは": "ことは〜が",
    "さぞ(かし)": "さぞ",
    "し": "し〜し",
    "する": "する (do)",
    "する①": "する (do)",
    "する③": "がする",
}

def read_file_list(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

def read_yaml(input_file: str, type) -> dict:
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read().replace("～", "〜")
        point = yaml.safe_load(content)
        point["grammar_point"] = point["grammar_point"].replace("+ ", "+").replace(" +", "+").replace("［","[").replace("］","]")
        point[f"{type}_grammar_point"] = point["grammar_point"]
        return point

def apply_translations(yaml_list, translations, used_translations):
    translation_keys = set(translations.keys()) 
    for item in yaml_list:
        translation_key = item['grammar_point']
        if  translation_key in translation_keys:
            item['grammar_point'] = translations[translation_key]
            used_translations.add(translation_key) 

    return yaml_list

def trim_elements(merged_list):
    trimmed_list = []
    for item in merged_list:
        trimmed_item = {'grammar_point': item['grammar_point']}
        
        if 'meaning' in item:
            trimmed_item['meaning'] = item['meaning']
        
        if 'bunpro' in item and item['bunpro'] is not None:
            bunpro_trimmed = {'grammar_point': item['bunpro']['bunpro_grammar_point'], 'url': item['bunpro']['url']}
            if 'meaning' in item['bunpro']:
                bunpro_trimmed['meaning'] = item['bunpro']['meaning']
            if 'examples' in item['bunpro']:
                bunpro_trimmed['examples'] = item['bunpro']['examples'][:2]
            trimmed_item['bunpro'] = bunpro_trimmed
        
        if 'dojg' in item and item['dojg'] is not None:
            dojg_trimmed = {'grammar_point': item['dojg']['dojg_grammar_point']}
            if 'meaning' in item['dojg']:
                dojg_trimmed['meaning'] = item['dojg']['meaning']
            if 'examples' in item['dojg']:
                dojg_trimmed['examples'] = item['dojg']['examples'][:2]
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


def is_merged(item, used_resolutions = None):
    grammar_point = item['grammar_point']
    has_bunpro = 'bunpro' in item and item['bunpro'] is not None
    has_dojg = 'dojg' in item and item['dojg'] is not None

    # Check for forced resolutions
    if grammar_point in forced_resolutions:
        forced_source = forced_resolutions[grammar_point]
        if forced_source == 'bunpro' and has_bunpro:
            if used_resolutions is not None:
                used_resolutions.add(grammar_point)
            return True
        elif forced_source == 'dojg' and has_dojg:
            if used_resolutions is not None:
                used_resolutions.add(grammar_point)
            return True
        else:
            return False
    # Regular filtering if no forced resolution
    else: 
        return has_bunpro and has_dojg

def generate_statistics(merged_list):
    merged_count = 0
    dojg_only_count = 0
    bunpro_only_count = 0

    for item in merged_list:
        if is_merged(item):
            merged_count += 1
        elif item['bunpro']:
            bunpro_only_count += 1
        elif item['dojg']:
            dojg_only_count += 1

    return {
        'merged_count': merged_count,
        'dojg_only_count': dojg_only_count,
        'bunpro_only_count': bunpro_only_count
    }

def remove_merged_grammar_points(merged_list):
    """
    Removes the grammar points that have both bunpro and dojg points,
    while considering forced resolutions. Raises an error if a forced resolution
    is not used.
    """
    filtered_list = []
    used_resolutions = set()  # Keep track of used forced resolutions

    for item in merged_list:
        if not is_merged(item, used_resolutions):
            filtered_list.append(item)

    # Check if all forced resolutions were used
    unused_resolutions = set(forced_resolutions.keys()) - used_resolutions
    if unused_resolutions:
        print("USED_RESOLUTIONS", used_resolutions)
        raise ValueError(f"Unused forced resolutions: {unused_resolutions}")

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

    # Apply translations to the grammar points before merging
    used_translations = set()
    bunpro_yamls = apply_translations(bunpro_yamls, grammar_point_name_translations, used_translations)
    dojg_yamls = apply_translations(dojg_yamls, grammar_point_name_translations, used_translations)
    unused_translations = set(grammar_point_name_translations.keys()) - used_translations
    if unused_translations:
        raise ValueError(f"Unused translation keys: {unused_translations}")

    merged = merge_lists(bunpro_yamls, dojg_yamls, list_name_one='bunpro', list_name_two='dojg')

    statistics = generate_statistics(merged)

    removed = remove_merged_grammar_points(trim_elements(merged))
    #removed = trim_elements(merged)
    label_closest_matches(removed)

    # Combine statistics and merged data
    output_data = {
        'statistics': statistics,
        'merged_data': removed
    }

    with open(output_file, 'w') as f:
        dump_yaml_file(output_data, f)

if __name__ == "__main__":
    main()
