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
    regex = regex.replace('{i-adjective-past}', """
        ⌈ˢ~かっᵖadj:~ᵇ~いʳ~イ⌉⌈ˢたᵖauxvʳタ⌉|
        ⌈~⌉⌈ˢ~かっᵖsuff:adjectivalᵇ~いʳ~イ⌉⌈ˢたᵖauxvʳタ⌉|
        ⌈~⌉⌈ˢしᵖv:non_self_reliantᵇするʳスル⌉⌈ˢ~かっᵖsuff:adjectivalᵇ~いʳ~イ⌉⌈ˢたᵖauxvʳタ⌉|
        ⌈ˢ~ᵖadj:generalᵇ~いʳ~イ⌉⌈ˢかったᵖadj:generalᵇかったいʳカタイ⌉|
        ⌈ˢ~ᵖadj:generalᵇ~いʳ~イ⌉⌈ˢかっᵖv:generalᵇかうʳカウ⌉⌈ˢたᵖauxvʳタ⌉|
        ⌈ˢ~ᵖn:common_nounʳ~⌉⌈ˢかっᵖv:generalᵇかうʳカウ⌉⌈ˢたᵖauxvʳタ⌉
    """)


    regex = regex.replace('{i-adjective-negative}', """
        ⌈ˢ~ᵖadj:~ᵇ~いʳ~⌉⌈ˢないᵖadj:non_self_reliantʳナイ⌉|
        ⌈ˢ~ᵖv:~⌉⌈ˢ~ᵖsuff:adjectivalᵇ~いʳ~イ⌉⌈ˢないᵖadj:non_self_reliantʳナイ⌉|
        ⌈~⌉⌈~ᵖv:non_self_reliant~⌉⌈ˢ~ᵖsuff:~⌉⌈ˢないᵖadj:non_self_reliantʳナイ⌉
    """)
    regex = regex.replace('{verb-dictionary}', """
        (?<!て)⌈ˢ~るᵖv:~ʳ~ル⌉|
        ⌈ˢ~くᵖv:~ʳ~ク⌉|
        ⌈ˢ~うᵖv:~ʳ~ウ⌉|
        ⌈ˢ~むᵖv:~ʳ~ム⌉|
        ⌈ˢ~すᵖv:~ʳ~ス⌉|
        ⌈ˢ~ぐᵖv:~ʳ~グ⌉|
        ⌈ˢ~ぶᵖv:~ʳ~ブ⌉|
        ⌈ˢ~つᵖv:~ʳ~ツ⌉|
        ⌈~⌉⌈ˢするᵖv:non_self_reliantʳスル⌉
    """)
    regex = regex.replace('{i-adjective-dictionary}', """
        
        (?!⌈ˢないᵖadj:non_self_reliantʳナイ⌉)
        (?!⌈ˢ素晴らしいᵖadj:generalʳスバラシイ⌉)
        (
            ⌈ˢ~いᵖadj:~ʳ~イ⌉|
            ⌈~⌉⌈ˢ~いᵖsuff:adjectivalʳ~イ⌉|
            (
                (
                ⌈~ᵖadj:~ᵇ~いʳ~イ⌉|
                ⌈ˢしᵖv:non_self_reliantᵇするʳスル⌉
                )
                (
                い|
                ⌈ˢいᵖint:fillerʳイー⌉|
                ⌈ˢいᵖv:non_self_reliantᵇいるʳイル⌉
                )
            )
        )
    """)
    regex = regex.replace('{noun}', """
        (
            ⌈ˢ~ᵖpron~⌉|
            ⌈~ᵖn~⌉⌈~ᵖsuff:noun_likeʳ~⌉|
            ⌈~ᵖn~⌉
        )
    """) 
    regex = regex.replace('{ni}', """
        (
            に|
            ⌈ˢにᵖauxvᵇだʳダ⌉
        )
    """)
    regex = regex.replace('{mo}', """
        (
            も
        )
    """)
    regex = regex.replace('{nai}', """
        (
            ⌈ˢないᵖadj:non_self_reliantʳナイ⌉|
            ⌈ˢないᵖauxv~ʳナイ⌉|
            ⌈ˢなかっᵖadj:non_self_reliantᵇないʳナイ⌉|
            ⌈ˢなかっᵖauxvᵇないʳナイ⌉⌈ˢたᵖauxvʳタ⌉|
            ⌈ˢませᵖauxvᵇますʳマス⌉⌈ˢんᵖauxvᵇぬʳズ⌉
        )
    """)
    regex = regex.replace('{suru}', """
        (
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢたᵖauxvʳタ⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢたらᵖauxvᵇたʳタ⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢなさいᵖvᵇなさるʳナサル⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢましᵖauxvᵇますʳマス⌉⌈ˢたᵖauxvʳタ⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢますᵖauxvʳマス⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢようᵖshpʳヨウ⌉⌈ˢじゃᵖauxvᵇだʳダ⌉⌈ˢないᵖadjʳナイ⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉⌈ˢようᵖsuffʳヨウ⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉て⌈ˢしまうᵖvʳシマウ⌉|
            ⌈ˢしᵖv~ᵇするʳスル⌉て|
            ⌈ˢしようᵖv~ᵇするʳスル⌉|
            ⌈ˢしよっᵖv~ᵇするʳスル⌉|
            ⌈ˢしろᵖv~ᵇするʳスル⌉|
            ⌈ˢするᵖv~ʳスル⌉|
            ⌈ˢすれᵖv~ᵇするʳスル⌉ば|
            ⌈ˢなさいᵖv~ᵇなさるʳナサル⌉⌈ˢますᵖauxvʳマス⌉
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
        (?P<verb_te>(
            (?P<godan_kiru>⌈ˢ~きᵖv:generalᵇ~きるʳ~キル⌉て)|
            (?P<ichidan_beru>⌈ˢ~べᵖv:generalᵇ~べるʳ~ベル⌉て)|
            (?P<ichidan_ru_non_reliant>⌈ˢ~ᵖv:non_self_reliantᵇ~るʳ~ル⌉て)|
            (?P<ichidan_ru_general>⌈ˢ~ᵖv:generalᵇ~るʳ~ル⌉て)|
            (?P<godan_u_sokuon>⌈ˢ~っᵖv:generalᵇ~うʳ~ウ⌉て)|
            (?P<godan_ku_ion>⌈ˢ~いᵖv:generalᵇ~くʳ~ク⌉て)|
            (?P<godan_tsu_sokuon>⌈ˢ~っᵖv:generalᵇ~つʳ~ツ⌉て)|
            (?P<godan_nu_hatsuon>⌈ˢ~んᵖv:generalᵇ~ぬʳ~ヌ⌉で)|
            (?P<godan_bu_hatsuon>⌈ˢ~んᵖv:generalᵇ~ぶʳ~ブ⌉で)|
            (?P<godan_mu_hatsuon>⌈ˢ~んᵖv:generalᵇ~むʳ~ム⌉で)|
            (?P<godan_gu_ion>⌈ˢ~いᵖv:generalᵇ~ぐʳ~グ⌉で)|
            (?P<godan_su_shite>⌈ˢ~しᵖv:generalᵇ~すʳ~ス⌉て)|
            (?P<godan_ku_non_reliant_sokuon>⌈ˢ~っᵖv:non_self_reliantᵇ~くʳ~ク⌉て)|
            ⌈ˢ~っᵖsuff:verb_likeᵇ~るʳ~ル⌉て
        ))
    """)
    regex = regex.replace('{verb-volitional}', """
        (?P<verb_volitional>(
            ⌈ˢ~ようᵖv:non_self_reliantᵇ~るʳ~⌉|
            ⌈ˢ~ようᵖv:generalᵇ~るʳ~⌉|
            ⌈ˢ~おうᵖv:generalᵇ~うʳ~⌉|
            ⌈ˢ~こうᵖv:generalᵇ~くʳ~⌉|
            ⌈ˢ~こうᵖv:non_self_reliantᵇ~くʳ~⌉|
            ⌈ˢ~ごうᵖv:generalᵇ~ぐʳ~⌉|
            ⌈ˢ~そうᵖv:generalᵇ~すʳ~⌉|
            ⌈ˢ~そうᵖv:non_self_reliantᵇ~すʳ~⌉|
            ⌈ˢ~とうᵖv:generalᵇ~つʳ~⌉|
            ⌈ˢ~のうᵖv:generalᵇ~ぬʳ~⌉|
            ⌈ˢ~ぼうᵖv:generalᵇ~ぶʳ~⌉|
            ⌈ˢ~もうᵖv:generalᵇ~むʳ~⌉|
            ⌈ˢ~ろうᵖv:generalᵇ~るʳ~⌉|
            ⌈ˢ~ろうᵖv:non_self_reliantᵇ~るʳ~⌉|
            ⌈ˢ~しようᵖsuff:verb_likeᵇ~るʳ~⌉|
            ⌈ˢ~ᵖv:generalᵇ~るʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:non_self_reliantᵇ~るʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~うʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~くʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:non_self_reliantᵇ~くʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~ぐʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~すʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:non_self_reliantᵇ~すʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~つʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~ぬʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~ぶʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:generalᵇ~むʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖsuff:verb_likeᵇ~るʳ~⌉⌈ˢましょうᵖauxvᵇますʳマス⌉|
            ⌈ˢ~ᵖv:non_self_reliantᵇ~るʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~るʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~うʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~くʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:non_self_reliantᵇ~くʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~ぐʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~すʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:non_self_reliantᵇ~すʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~つʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~ぬʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~ぶʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖv:generalᵇ~むʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢ~ᵖsuff:verb_likeᵇ~るʳ~⌉⌈ˢせようᵖauxvᵇせるʳセル⌉|
            ⌈ˢやろうᵖauxvᵇやʳヤ⌉
        ))
    """)
    regex = regex.replace('{verb-eba}', """
        (?P<verb_eba>(
            (?P<kuru_eba>⌈ˢくれᵖv:irregularᵇ~くるʳ~クル⌉ば)|
            (?P<suru_eba>⌈ˢすれᵖv:irregularᵇ~するʳ~スル⌉ば)|
            (?P<ichidan_beru_eba>⌈ˢ~べᵖv:generalᵇ~べるʳ~ベル⌉ば)|
            (?P<ichidan_ru_non_reliant_eba>⌈ˢ~れᵖv:non_self_reliantᵇ~るʳ~ル⌉ば)|
            (?P<ichidan_ru_general_eba>⌈ˢ~れᵖv:generalᵇ~るʳ~ル⌉ば)|
            (?P<godan_u_eba>⌈ˢ~えᵖv:generalᵇ~うʳ~ウ⌉ば)|
            (?P<godan_ku_eba>⌈ˢ~けᵖv:generalᵇ~くʳ~ク⌉ば)|
            (?P<godan_ku_eba_non_reliant_eba>⌈ˢ~けᵖv:non_self_reliantᵇ~くʳ~ク⌉ば)|
            (?P<godan_tsu_eba>⌈ˢ~てᵖv:generalᵇ~つʳ~ツ⌉ば)|
            (?P<godan_ru_eba>⌈ˢ~れᵖv:generalᵇ~るʳ~ル⌉ば)|
            (?P<godan_nu_eba>⌈ˢ~ねᵖv:generalᵇ~ぬʳ~ヌ⌉ば)|
            (?P<godan_bu_eba>⌈ˢ~べᵖv:generalᵇ~ぶʳ~ブ⌉ば)|
            (?P<godan_mu_eba>⌈ˢ~めᵖv:generalᵇ~むʳ~ム⌉ば)|
            (?P<godan_gu_eba>⌈ˢ~げᵖv:general~ʳ~グ⌉ば)|
            (?P<godan_su_eba>⌈ˢ~せᵖv:generalᵇ~すʳ~ス⌉ば)|
            (?P<godan_kiru_eba>⌈ˢ~きれᵖv:generalᵇ~きるʳ~キル⌉ば)|
            (?P<nai_eba>⌈ˢなけれᵖauxvᵇないʳナイ⌉ば)|
            (?P<tai_eba>⌈ˢたけれᵖauxvᵇたいʳタイ⌉ば)
        )) 
    """)
    regex = regex.replace('{verb-imperative}', """
        (?P<verb_imperative>(
            (?P<ichidan_imperative_ro>⌈ˢ~ろᵖv:generalᵇ~るʳ~ル⌉)|
            (?P<ichidan_imperative_ro_non_reliant>⌈ˢ~ろᵖv:non_self_reliantᵇ~るʳ~ル⌉)|
            (?P<ichidan_imperative_ke>⌈ˢ~けᵖv:generalᵇ~けるʳ~ケル⌉)|
            (?P<ichidan_imperative_ke_non_reliant>⌈ˢ~けᵖv:non_self_reliantᵇ~けるʳ~ケル⌉)|
            (?P<ichidan_imperative_se>⌈ˢ~せᵖv:generalᵇ~せるʳ~セル⌉)|
            (?P<ichidan_imperative_se_non_reliant>⌈ˢ~せᵖv:non_self_reliantᵇ~せるʳ~セル⌉)|
            (?P<ichidan_imperative_te>⌈ˢ~てᵖv:generalᵇ~てるʳ~テル⌉)|
            (?P<ichidan_imperative_te_non_reliant>⌈ˢ~てᵖv:non_self_reliantᵇ~てるʳ~テル⌉)|
            (?P<ichidan_imperative_ne>⌈ˢ~ねᵖv:generalᵇ~ねるʳ~ネル⌉)|
            (?P<ichidan_imperative_ne_non_reliant>⌈ˢ~ねᵖv:non_self_reliantᵇ~ねるʳ~ネル⌉)|
            (?P<ichidan_imperative_be>⌈ˢ~べᵖv:generalᵇ~べるʳ~ベル⌉)|
            (?P<ichidan_imperative_be_non_reliant>⌈ˢ~べᵖv:non_self_reliantᵇ~べるʳ~ベル⌉)|
            (?P<ichidan_imperative_me>⌈ˢ~めᵖv:generalᵇ~めるʳ~メル⌉)|
            (?P<ichidan_imperative_me_non_reliant>⌈ˢ~めᵖv:non_self_reliantᵇ~めるʳ~メル⌉)|
            (?P<ichidan_imperative_re>⌈ˢ~れᵖv:generalᵇ~れるʳ~レル⌉)|
            (?P<ichidan_imperative_re_non_reliant>⌈ˢ~れᵖv:non_self_reliantᵇ~れるʳ~レル⌉)|
            (?P<ichidan_imperative_ge>⌈ˢ~げᵖv:generalᵇ~げるʳ~ゲル⌉)|
            (?P<ichidan_imperative_ge_non_reliant>⌈ˢ~げᵖv:non_self_reliantᵇ~げるʳ~ゲル⌉)|
            (?P<godan_u_imperative>⌈ˢ~えᵖv:generalᵇ~うʳ~ウ⌉)|
            (?P<godan_u_non_reliant_imperative>⌈ˢ~えᵖv:non_self_reliantᵇ~うʳ~ウ⌉)|
            (?P<godan_ku_imperative>⌈ˢ~けᵖv:generalᵇ~くʳ~ク⌉)|
            (?P<godan_ku_non_reliant_imperative>⌈ˢ~けᵖv:non_self_reliantᵇ~くʳ~ク⌉)|
            (?P<godan_gu_imperative>⌈ˢ~げᵖv:generalᵇ~ぐʳ~グ⌉)|
            (?P<godan_gu_non_reliant_imperative>⌈ˢ~げᵖv:non_self_reliantᵇ~ぐʳ~グ⌉)|
            (?P<godan_su_imperative>⌈ˢ~せᵖv:generalᵇ~すʳ~ス⌉)|
            (?P<godan_su_non_reliant_imperative>⌈ˢ~せᵖv:non_self_reliantᵇ~すʳ~ス⌉)|
            (?P<godan_tsu_imperative>⌈ˢ~てᵖv:generalᵇ~つʳ~ツ⌉)|
            (?P<godan_tsu_non_reliant_imperative>⌈ˢ~てᵖv:non_self_reliantᵇ~つʳ~ツ⌉)|
            (?P<godan_nu_imperative>⌈ˢ~ねᵖv:generalᵇ~ぬʳ~ヌ⌉)|
            (?P<godan_nu_non_reliant_imperative>⌈ˢ~ねᵖv:non_self_reliantᵇ~ぬʳ~ヌ⌉)|
            (?P<godan_bu_imperative>⌈ˢ~べᵖv:generalᵇ~ぶʳ~ブ⌉)|
            (?P<godan_bu_non_reliant_imperative>⌈ˢ~べᵖv:non_self_reliantᵇ~ぶʳ~ブ⌉)|
            (?P<godan_mu_imperative>⌈ˢ~めᵖv:generalᵇ~むʳ~ム⌉)|
            (?P<godan_mu_non_reliant_imperative>⌈ˢ~めᵖv:non_self_reliantᵇ~むʳ~ム⌉)|
            (?P<godan_ru_imperative>⌈ˢ~れᵖv:generalᵇ~るʳ~ル⌉)|
            (?P<godan_ru_non_reliant_imperative>⌈ˢ~れᵖv:non_self_reliantᵇ~るʳ~ル⌉)|
            (?P<irregular_kuru_imperative>⌈ˢ来いᵖv:non_self_reliantᵇ来るʳクル⌉)|
            (?P<irregular_kuru_imperative_general>⌈ˢ来いᵖv:generalᵇ来るʳクル⌉)|
            (?P<irregular_suru_imperative>⌈ˢしろᵖv:non_self_reliantᵇするʳスル⌉)|
            (?P<irregular_suru_imperative_general>⌈ˢしろᵖv:generalᵇするʳスル⌉)|
            ⌈ˢ~えᵖsuff:verb_likeᵇ~るʳ~ル⌉|
            ⌈ˢ~ろᵖsuff:verb_likeᵇ~るʳ~ル⌉
         
        ))
    """)
   
    regex = regex.replace('\n','').replace(' ', '')
    regex = regex.replace("~", '[^⌉]*?')
    return Matcher(matcher, regex)
