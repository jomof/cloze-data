import sys
import yaml
from dumpyaml import dump_yaml_file
import difflib

missing_meanings = {
    "RelativeClause": "Modifies a noun by providing additional descriptive information about it." ,
    "RhetoricalQuestion": "A question asked for effect, not requiring an answer, often used to express strong emotion or make a point.",
    "VmasuasaNoun": "Treats a verb in the masu-stem form as a noun, often to describe an action or state as a concept.",
    "お": "Honorific prefix for nouns and verbs, adds politeness and respect.",
    "お~だ": "Polite copula, equivalent to 'desu' but often used for adjectives or states related to the listener.", 
    "お〜する": "Humble verb form, used when the speaker performs an action for someone of higher status.",
    "お〜になる": "Honorific verb form, used when referring to actions or states of someone of higher status.",
    "かい": "Informal sentence ending particle, similar to 'ka' but softer and more casual, often used by males.",
    "が (subject marker)": "Particle marking the grammatical subject of the sentence.", 
    "ことがある (there are times)":  "Indicates that an action or event happens occasionally or sometimes.", 
    "しい": "Suffix for i-adjectives, indicates a strong emotion or feeling.",
    "だい": "Informal sentence ending particle, emphasizes a question or request, often used by males.",
    "っけ": "Sentence ending particle, expresses uncertainty or seeks confirmation, 'wasn't it?', 'didn't we?'", 
    "に": "Particle with various functions, including indicating location, time, target of action, and indirect object.",
    "は〜が": "Sentence structure emphasizing a contrast, 'A is (topic), but B (focus)'.",
    "は〜だ": "Basic sentence structure, identifies the topic (A) and provides information (B) about it.", 
    "わ": "Sentence ending particle, mainly used by females, adds a soft and feminine tone, can express emphasis or emotion.",
    "を (object marker)":  "Particle marking the direct object of a transitive verb.",
    "を (object of an emotion)": "Indicates the object or cause of an emotion or feeling.", 
    "を (point of departure)": "Indicates the point from which someone or something departs or separates.",
    "君・くん": "Suffix added to names, primarily for males, expresses familiarity or a slightly informal tone." 
}

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
    "ずして": "dojg",
    "せっかく": "dojg",
    "そうかと言って": "dojg",
    "そのもの": "dojg",
    "そもそも(の)": "dojg",
    "それから": "dojg",
    "それが": "dojg",
    "それだけ": "dojg",
    "それでは": "dojg",
    "それと": "dojg",
    "それどころか": "dojg",
    "それなりに・の": "dojg",
    "それは": "dojg",
    "それも": "dojg",
    "たかが": "dojg",
    "ただ": "dojg",
    "ただの": "dojg",
    "だい": "dojg",
    "だからと言って": "dojg",
    "だが": "dojg",
    "する (cost)": "dojg",
    "する (have)": "dojg",
    "要る・いる (need)": "dojg",
    "見るからに": "dojg",
    "言ってみれば": "dojg",
    "言わば": "dojg",
    "限り (only until)": "dojg",
    "そうになる": "dojg",
    "願う・願います": "dojg",
    "面": "dojg",
    "限り (only until)": "dojg",
    "行く・いく (continue)": "dojg",
    "行く・いく (go)" : "dojg",
    "自分・じぶん①": "dojg",
    "自分・じぶん②": "dojg",
    "自体": "dojg",
    "そこで (then)" : "dojg",
    "そこを": "dojg",
    "たるや": "dojg",
    "そして": "dojg",
    "だって (too)": "dojg",
    "ちなみに": "dojg",
    "って (speaking of)": "dojg",
    "って (that)": "dojg",
    "ついては": "dojg",
    "てばかりはいられない": "dojg",
    "て仕方がない": "dojg",
    "で (because)": "dojg",
    "で (by time)": "dojg",
    "で (for)": "dojg",
    "であろう": "dojg",
    "と (thinking that)" : "dojg",
    "とあっては": "dojg",
    "というのに": "dojg",
    "ほうが~より": "dojg",
    "ましだ": "dojg",
    "まして(や)": "dojg",
    "と (in the manner of)": "dojg",
    "といったところだ": "dojg",
    "とかで": "dojg",
    "ところから": "dojg",
    "を (movement through space)": "dojg",
    "を (point of departure)": "dojg",
    "を (object of an emotion)": "dojg",
    "ところだ (in a place where it takes ~ to get to)": "dojg",
    "ところ": "dojg",
    "とでも言うべき": "dojg",
    "となる": "dojg",
    "となると": "dojg",
    "とは言え": "dojg",
    "とばかりに": "dojg",
    "ともすると": "dojg",
    "ともなく": "dojg",
    "と言うか": "dojg",
    "と言うと": "dojg",
    "ども": "dojg",
    "とする (assume that)": "dojg",
    "とする (feel ~)": "dojg",
    "と言えば": "dojg",
    "と言って": "dojg",
    "どう": "dojg",
    "どうか": "dojg",
    "どうにも〜ない": "dojg",
    "どうも": "dojg",
    "どちらかと言うと": "dojg",
    "ども": "dojg",
    "どんなに~(こと)か": "dojg",
    "なあ": "dojg",
    "なく": "dojg",
    "なくなる": "dojg",
    "なしでは": "dojg",
    "なしに": "dojg",
    "なす": "dojg",
    "なぜか": "dojg",
    "ないし(は)" : "dojg",
    "なおさら": "dojg",
    "などと": "dojg",
    "なまじ(っか)": "dojg",
    "なり~なり": "dojg",
    "なるほど": "dojg",
    "なんて (what)": "dojg",
    "に(も)なく": "dojg",
    "に (at)": "dojg",
    "に (to)": "dojg",
    "に (by)": "dojg",
    "に (on)": "dojg",
    "に (to do something)": "dojg",
    "に (in)": "dojg",
    "に (toward)": "dojg",
    "にとって": "dojg",
    "になると": "dojg",
    "によらず": "dojg",
    "を介して・介した": "dojg",
    "んとする": "dojg",
    "一[Counter]として〜ない": "dojg",
    "一つには": "dojg",
    "一切〜ない": "dojg",
    "にしてからが": "dojg",
    "に従って・従い": "dojg",
    "の (possessive)": "dojg",
    "の (one)": "dojg",
    "の (that ~)": "dojg",
    "の (it is that ~)": "dojg",
    "のこと": "dojg",
    "のは~のことだ": "dojg",
    "のみ": "dojg",
    "分": "dojg",
    "分かる・わかる": "dojg",
    "及び": "dojg",
    "君・くん": "dojg",
    "結構": "dojg",
    "結果": "dojg",
    "の上では": "dojg",
    "の無さ・のなさ": "dojg",
    "の関係で": "dojg",
    "は〜が": "dojg",
    "は〜だ": "dojg",
    "はあれ": "dojg",
    "はいいとしても": "dojg",
    "または": "dojg",
    "まで(のこと)だ": "dojg",
    "まま": "dojg",
    "も~ば": "dojg",
    "も~も": "dojg",
    "もしくは": "dojg",
    "ものか (wish)": "dojg",
    "ものではない": "dojg",
    "より (than)": "dojg",
    "より (in ~ of)": "dojg",
    "より・のほか(に)(は)〜ない": "dojg",
    "ろくに~ない": "dojg",
    "をめぐって・めぐる": "dojg",
    "は (as for ~)": "dojg",
    "もらう (have someone do)": "dojg",
    "やっと": "dojg",
    "やはり": "dojg",
    "やら": "dojg",
    "ようと・が": "dojg",
    "ように (like)": "dojg",
    "ようにも(〜ない)": "dojg",
    "ようものなら": "dojg",
    "んばかり(に)": "dojg",
    "知る・しる": "dojg",
    "やる (send)": "dojg",
    "やる (knowing that it will cause someone trouble)": "dojg",
    "目": "dojg",
    "よう (probably)": "dojg",
    "よう (the way to)": "dojg",
    "一方(で)": "dojg",
    "且つ・かつ": "dojg",
    "並びに": "dojg",
    "今更・いまさら": "dojg",
    "代わりに・かわりに": "dojg",
    "以上(は)": "dojg",
    "以外": "dojg",
    "仮に": "dojg",
    "但し・ただし": "dojg",
    "何[(Number)+Counter]も": "dojg",
    "何〜ない": "dojg",
    "何でも": "dojg",
    "何とか": "dojg",
    "何も〜ない": "dojg",
    "何ら〜ない": "dojg",
    "何らかの": "dojg",
    "例の": "dojg",
    "少ない・すくない": "dojg",
    "屋・や": "dojg",
    "思うに": "dojg",
    "思えば": "dojg",
    "思われる": "dojg",
    "思われる": "dojg",
    "折(に)": "dojg",
    "一番・いちばん": "dojg",
    "様・さま": "dojg",
    "ほしい (want something)" : "dojg",
    "ほしい (want someone to do something)": "dojg",
    "済む": "dojg",
    "滅多に〜ない": "dojg",
    "くる (come about)": "dojg",
    "単に": "dojg",
    "単位で": "dojg",
    "堪らない・たまらない": "dojg",
    "多い・おおい": "dojg",
    "好きだ・すきだ": "dojg",
    "如何(だ)・いかん(だ)": "dojg",
    "如何(だ)・いかん(だ)": "dojg",
    "呉れる・くれる (do something for someone)": "dojg",
    "呉れる・くれる (give)": "dojg",
    "方をする": "dojg",
    "末(に)": "dojg",
    "来": "dojg",
    "毎・まい": "dojg",
    "点(で)": "dojg",
    "由・よし": "dojg",
    "甲斐・かい・がい": "dojg",
    "毎・まい": "dojg",
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
    "〜やら〜やら": "やら〜やら",
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
    "そこで②": "そこで (then)",
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
    "は①": "は (as for ~)",
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
    "より①": "より (than)",
    "より②": "より (in ~ of)",
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
    apply_missing_meanings(merged, missing_meanings)

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
