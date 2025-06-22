import re
from python.mecab.compact_sentence import japanese_to_compact_sentence, compact_sentence_to_japanese


class Matcher:
    def __init__(
        self,
        matcher: str,
        regex_string: str,
    ):
        self.matcher = matcher
        self.regex_string = regex_string
        self.regex = re.compile(regex_string)

    def match_japanese(self, japanese: str):
        if '⌈' not in japanese:
            japanese = japanese.replace('{','').replace('}', '')
            japanese = japanese_to_compact_sentence(japanese)
            # print(f"COMPACT: {japanese}")
        return _flatten_search_results(self.regex.search(japanese))
    
def _flatten_search_results(search):
    if not search: return None
    return compact_sentence_to_japanese(search.group(0), spaces=True)

def compile_matcher(matcher: str) -> Matcher:
    # Do replacements".
    regex = matcher

    regex = regex.replace('{to}', """
        (
            ⌈ˢとᵖprt:case_particleᵇとʳト⌉
        )
    """)

    regex = regex.replace('{i-adjective-past}', """
        ⌈~⌉⌈ˢかったᵖadj:general:adjective:stemᵇかったいᵈ固いʳカッタ⌉|
        ⌈~⌉⌈ˢかっᵖv~ᵇ~うᵈ~うʳ~⌉⌈ˢたᵖauxv:auxv-ta~⌉|
        ⌈~かっᵖadj~ᵇ~いᵈ~いʳ~ッ⌉⌈ˢたᵖauxv~⌉|
        ⌈~⌉⌈ˢ~かっᵖsuff~ᵇ~いᵈ~いʳ~カッ⌉⌈ˢたᵖauxv~⌉|
        ⌈~⌉⌈ˢしᵖv:non_self_reliant~⌉⌈ˢ~かっᵖsuff~ᵇ~いᵈ~いʳ~カッ⌉⌈ˢたᵖauxv:auxv-ta~⌉
    """)


    regex = regex.replace('{i-adjective-negative}', """
        ⌈ˢ~くᵖadj:~ᵇ~いᵈ~いʳ~⌉⌈ˢないᵖadj~⌉|
        ⌈~⌉⌈ˢ~くᵖsuff~ᵇ~いᵈ~いʳ~⌉⌈ˢないᵖadj~⌉|
        ⌈~⌉⌈ˢしᵖv~⌉⌈ˢ~くᵖsuff~ᵇ~いᵈ~いʳ~⌉⌈ˢないᵖ~⌉
    """)
    # ⌈ˢてᵖprt:conjunctive_particleᵇてʳテ⌉
    regex = regex.replace('{verb-dictionary}', """
        (?<!⌈ˢてᵖprt:conjunctive_particleᵇてʳテ⌉)
        (
            ⌈ˢ~むᵖv:~ᵇ~むʳ~ム⌉|
            ⌈ˢ~くᵖv:~ᵇ~くʳ~ク⌉|
            ⌈ˢ~うᵖv:~ᵇ~うʳ~ウ⌉|
            ⌈ˢ~るᵖv:~ᵇ~るʳ~ル⌉|
            ⌈ˢ~すᵖv:~ᵇ~すʳ~ス⌉|
            ⌈ˢ~ぐᵖv:~ᵇ~ぐʳ~グ⌉|
            ⌈ˢ~ぶᵖv:~ᵇ~ぶʳ~ブ⌉|
            ⌈ˢ~つᵖv:~ᵇ~つʳ~ツ⌉|
            ⌈~ᵖn~⌉⌈ˢするᵖv:non_self_reliant:~ᵇするᵈ為るʳスル⌉
        )
    """)
   
    regex = regex.replace('{i-adjective-dictionary}', """
        (?!
            ⌈ˢないᵖadj:non_self_reliant:adjective:terminalᵇないᵈ無いʳナイ⌉|
            ⌈ˢやすいᵖsuff:adjectival:adjective:terminalᵇやすいᵈ易いʳヤスイ⌉|
            ⌈ˢ~らしいᵖadj:general:adjective:attributiveᵇ~らしいʳスバ~⌉
        )
        (
            ⌈ˢ~いᵖadj:~ᵇ~いʳ~⌉|
            ⌈ˢ~ᵖv:general:~:conjunctiveᵇ~⌉⌈ˢやすいᵖsuff:adjectival:~ᵇやすいᵈ易いʳヤスイ⌉|
            ⌈ˢ~ᵖv:general:~:conjunctiveᵇ~⌉⌈ˢにくいᵖsuff:adjectival:~ᵇにくいᵈ難いʳニクイ⌉
        )
    """)
    regex = regex.replace('{noun}', """
        (
            ⌈ˢ~ᵖpron~⌉|
            ⌈~ᵖn~⌉⌈~ᵖsuff:~ʳ~⌉|
            ⌈~ᵖn~⌉
        )
    """) 
    regex = regex.replace('{ni}', """
        (
            ⌈ˢにᵖprt:case_particleᵇにʳニ⌉|
            ⌈ˢにᵖauxv:auxv-da:conjunctive-niᵇだᵈだʳニ⌉
        )
    """)
    regex = regex.replace('{mo}', """
        (
            も
        )
    """)
    regex = regex.replace('{nai}', """
        (
            ⌈ˢないᵖadj:non_self_reliant:adjective:terminalᵇないᵈ無いʳナイ⌉|
            ⌈ˢなかっᵖauxv:auxv-nai:conjunctive-geminateᵇないᵈないʳナカッ⌉⌈ˢたᵖauxv:auxv-ta:terminalᵇたʳタ⌉|
            ⌈ˢませᵖauxv:auxv-masu:imperfectiveᵇますᵈますʳマセ⌉⌈ˢんᵖauxv:auxv-nu:terminal-nasalᵇぬᵈずʳン⌉|
            ⌈ˢないᵖauxv:auxv-nai:terminalᵇないʳナイ⌉|
            ⌈ˢなかっᵖadj:non_self_reliant:adjective:conjunctive-geminateᵇないᵈ無いʳナカッ⌉⌈ˢたᵖauxv:auxv-ta:terminalᵇたʳタ⌉
        )
    """)
    regex = regex.replace('{suru}', """
        (
            ⌈ˢしᵖv:non_self_reliant:sa-irregular:conjunctiveᵇするᵈ為るʳシ⌉⌈~⌉|
            ⌈ˢしようᵖv:non_self_reliant:sa-irregular:volitional-presumptiveᵇするᵈ為るʳシヨー⌉|
            ⌈ˢするᵖv:non_self_reliant:sa-irregular:terminalᵇするᵈ為るʳスル⌉|
            ⌈ˢすれᵖv:non_self_reliant:sa-irregular:conditionalᵇするᵈ為るʳスレ⌉⌈~⌉
        )
    """)
    regex = regex.replace('{desu}', """
        (
            ⌈ˢですᵖauxvʳデス⌉|
            ⌈ˢだᵖauxvʳダ⌉
        )
    """)
    
    regex = regex.replace('{shinai}', """
        (
            ⌈ˢしᵖvᵇするʳスル⌉{nain}
        )
    """)
    regex = regex.replace('{verb-dictionary}', """
        (
            ⌈ˢ.*るᵖv~ʳ.*ル⌉|
            ⌈ˢたᵖauxv~ʳタ⌉
        )
    """)
    regex = regex.replace('{verb-te}', """
        ⌈ˢ~ᵖadj:general:adjective:stemᵇ~⌉⌈ˢがっᵖsuff:~⌉⌈ˢてᵖprt:conjunctive_particleᵇてʳテ⌉|
        ⌈ˢ~ᵖv:~⌉⌈ˢてᵖprt:conjunctive_particleᵇてʳテ⌉|
        ⌈ˢ~ᵖv:~⌉⌈ˢでᵖprt:conjunctive_particleᵇでᵈてʳデ⌉
    """)
    regex = regex.replace('{verb-volitional}', """
        (?!
            ⌈ˢでしょうᵖauxv:auxv-desu:volitional-presumptiveᵇですᵈですʳデショー⌉
        )
        (
            ⌈ˢ~うᵖ~:volitional-presumptiveᵇ~ᵈ~ʳ~ー⌉|
            ⌈ˢ~ᵖv:~⌉⌈ˢましょうᵖ~:volitional-presumptiveᵇますᵈますʳマショー⌉|
            ⌈ˢ~ᵖv:~⌉⌈ˢせようᵖ~:volitional-presumptiveᵇせるᵈせるʳセヨー⌉
        )
    """)
    regex = regex.replace('{verb-eba}', """
        ⌈ˢ~ᵖv:~:conditionalᵇ~⌉⌈ˢばᵖprt:conjunctive_particleᵇばʳバ⌉|
        ⌈ˢ~ᵖv:~:conjunctiveᵇ~⌉⌈ˢばᵖprt:conjunctive_particleᵇばʳバ⌉|
        ⌈ˢ~ᵖ~:auxv-nai:conditionalᵇ~⌉⌈ˢばᵖprt:conjunctive_particleᵇばʳバ⌉|
        ⌈~⌉⌈ˢ~ᵖauxv:auxv-tai:conditionalᵇ~⌉⌈ˢばᵖprt:conjunctive_particleᵇばʳバ⌉
    """)
    regex = regex.replace('{verb-imperative}', """
        (?!
            ⌈ˢなさいᵖv:non_self_reliant:godan-ra:imperativeᵇなさるᵈ為さるʳナサイ⌉|
            ⌈ˢくださいᵖv:non_self_reliant:godan-ra:imperativeᵇくださるᵈ下さるʳクダサイ⌉|
            ⌈ˢくれᵖv:non_self_reliant:e-ichidan-ra:imperativeᵇくれるᵈ呉れるʳクレ⌉
        )
        ⌈ˢ~ᵖv:~:imperativeᵇ~⌉
    """)
   
    regex = regex.replace('\n','').replace(' ', '')
    regex = regex.replace("~", '[^⌉]*?')
    return Matcher(matcher, regex)
