import unittest
from python.grammar.matcher import compile_matcher
from python.mecab.compact_sentence import japanese_to_compact_sentence

class TestMatcher(unittest.TestCase):

    def test_noun(self):
        matcher = compile_matcher("{noun}")
        self.check(matcher, " 隣人 {と} 仲 が いい。", "隣人")

    def test_i_adjective_past(self):
        matcher = compile_matcher("{i-adjective-past}")

        self.check(matcher, "昨日、忙し {かっ た} よう でし た ね。", "忙しかった")
        self.check(matcher, "寒 {かっ た} から、家 に い まし た。", "寒かった")
        self.check(matcher, "その 夜 は 長く、そして 暗 {かっ た}。", "暗かった")
        
        # Basic i-adjectives in past tense form (かった)
        self.check(matcher, "この本は{面白かった}です。", "面白かった")
        self.check(matcher, "昨日は{暑かった}ですね。", "暑かった")
        self.check(matcher, "彼女は{美しかった}人です。", "美しかった")
        self.check(matcher, "その問題は{難しかった}です。", "難しかった")
        self.check(matcher, "映画は{つまらなかった}でした。", None) # Verb

        # Common i-adjectives in past tense form
        self.check(matcher, "部屋が{広かった}ですね。", "広かった")
        self.check(matcher, "水が{冷たかった}です。", "冷たかった")
        self.check(matcher, "昨日は{寒かった}です。", "寒かった")
        self.check(matcher, "その料理は{美味しかった}です。", "美味しかった")
        self.check(matcher, "宿題が{多かった}です。", "多かった")
        self.check(matcher, "時間が{少なかった}です。", "少なかった")
        self.check(matcher, "彼は{若かった}です。", "若かった")
        self.check(matcher, "その道は{長かった}です。", "長かった")
        self.check(matcher, "話が{短かった}です。", "短かった")
        self.check(matcher, "値段が{高かった}です。", "高かった")
        self.check(matcher, "その商品は{安かった}です。", "安かった")

        # Size and physical properties in past tense form
        self.check(matcher, "象は{大きかった}動物です。", "大きかった")
        self.check(matcher, "アリは{小さかった}です。", "小さかった")
        self.check(matcher, "その箱は{重かった}です。", "重かった")
        self.check(matcher, "羽は{軽かった}です。", "軽かった")
        self.check(matcher, "道が{狭かった}です。", "狭かった")
        self.check(matcher, "海は{深かった}です。", "深かった")
        self.check(matcher, "プールは{浅かった}です。", "浅かった")

        # Colors (i-adjectives) in past tense form
        self.check(matcher, "血は{赤かった}です。", "赤かった")
        self.check(matcher, "空は{青かった}です。", "青かった")
        self.check(matcher, "雪は{白かった}です。", "白かった")
        self.check(matcher, "髪は{黒かった}です。", "黒かった")
        self.check(matcher, "葉っぱは{黄色かった}です。", "黄色かった")

        # Emotions and feelings in past tense form
        self.check(matcher, "彼は{嬉しかった}そうです。", "嬉しかった")
        self.check(matcher, "とても{悲しかった}気持ちです。", "悲しかった")
        self.check(matcher, "試験が{怖かった}です。", "怖かった")
        self.check(matcher, "昨日は{楽しかった}日でした。", "楽しかった")
        self.check(matcher, "とても{恥ずかしかった}です。", "恥ずかしかった")

        # Special i-adjectives in past tense form
        self.check(matcher, "彼は{よかった}人です。", "よかった")  # よい → よかった
        self.check(matcher, "天気が{よかった}です。", "よかった")
        # Note: いい → よかった (not いかった)

        # Compound i-adjectives in past tense form
        self.check(matcher, "その靴は{履きやすかった}です。", "履きやすかった")
        self.check(matcher, "漢字は{覚えにくかった}です。", "覚えにくかった")
        self.check(matcher, "その本は{読みやすかった}です。", "読みやすかった")
        self.check(matcher, "数学は{分かりにくかった}です。", "分かりにくかった")

        # Adjectives already ending in ない in past form
        self.check(matcher, "お金が{なかった}です。", "なかった")  # ない → なかった
        self.check(matcher, "時間が{足りなかった}です。", None) # Not an adjective
        self.check(matcher, "昨日は{忙しなかった}です。", "忙しなかった")  # 忙しない → 忙しなかった

        # Longer compound i-adjectives in past tense form
        self.check(matcher, "その機械は{使いやすかった}です。", "使いやすかった")
        self.check(matcher, "彼の説明は{分かりやすかった}です。", "分かりやすかった")
        self.check(matcher, "その道は{歩きにくかった}です。", "歩きにくかった")
        self.check(matcher, "昨日は{過ごしやすかった}天気でした。", "過ごしやすかった")

        # Regional/dialectal i-adjectives in past tense form
        self.check(matcher, "その料理は{うまかった}ですね。", "うまかった")  # うまい → うまかった
        self.check(matcher, "昨日は{えらかった}暑いです。", "えらかった")  # えらい → えらかった

        # Various sentence contexts
        self.check(matcher, "この本は{面白かった}ですか？", "面白かった")  # Question
        self.check(matcher, "昨日は{暑かった}でしょう。", "暑かった")  # Probability
        self.check(matcher, "彼は{優しかった}人だと思います。", "優しかった")  # Opinion
        self.check(matcher, "その映画は{つまらなかった}かもしれません。", None)  # Not an adjective

        # With intensifiers
        self.check(matcher, "とても{暑かった}日でした。", "暑かった")
        self.check(matcher, "すごく{面白かった}映画でした。", "面白かった")
        self.check(matcher, "かなり{難しかった}問題でした。", "難しかった")
        self.check(matcher, "本当に{美味しかった}料理でした。", "美味しかった")

        # Casual vs polite contexts
        self.check(matcher, "映画が{面白かった}。", "面白かった")  # Casual
        self.check(matcher, "映画が{面白かった}です。", "面白かった")  # Polite
        self.check(matcher, "映画が{面白かった}でした。", "面白かった")  # Past polite

        # --- False Positives (should NOT match) ---

        # Dictionary form i-adjectives (present tense)
        self.check(matcher, "この本は{面白い}です。", None)
        self.check(matcher, "今日は{暑い}ですね。", None)
        self.check(matcher, "彼女は{美しい}人です。", None)
        self.check(matcher, "この問題は{難しい}です。", None)

        # Negative forms (くない)
        self.check(matcher, "この本は{面白くない}です。", None)
        self.check(matcher, "今日は{暑くない}ですね。", None)
        self.check(matcher, "彼女は{美しくない}人です。", None)

        # Na-adjectives (not i-adjectives)
        self.check(matcher, "彼は{親切}でした。", None)  # na-adjective past
        self.check(matcher, "部屋が{静か}でした。", None)  # na-adjective past
        self.check(matcher, "とても{綺麗}でしたね。", None)  # na-adjective past

        # Na-adjectives with past copula
        self.check(matcher, "彼は{親切だった}です。", None)  # na-adjective + だった
        self.check(matcher, "部屋が{静かだった}です。", None)  # na-adjective + だった

        # Adverbial forms (く form)
        self.check(matcher, "天気が{よく}なりました。", None)  # Adverbial form
        self.check(matcher, "もっと{大きく}してください。", None)  # Adverbial form
        self.check(matcher, "部屋が{広く}て良いですね。", None)  # Te-form

        # Polite past negative forms
        self.check(matcher, "この本は{面白くありませんでした}。", None)  # Polite past negative
        self.check(matcher, "今日は{暑くございませんでした}。", None)  # Honorific past negative

        # Verbs in past tense
        self.check(matcher, "友達に{会った}。", None)  # Past tense verb
        self.check(matcher, "本を{読んだ}。", None)  # Past tense verb
        self.check(matcher, "学校に{行った}。", None)  # Past tense verb
        self.check(matcher, "映画を{見た}。", None)  # Past tense verb

        # Nouns that might end in かった pattern
        self.check(matcher, "{昔}の話です。", None)  # Noun
        self.check(matcher, "{方}が良いです。", None)  # Noun

        # Adverbs
        self.check(matcher, "{もっと}食べてください。", None)  # Adverb
        self.check(matcher, "{ずっと}待っていました。", None)  # Adverb
        self.check(matcher, "{ちょっと}休みましょう。", None)  # Adverb

        # Grammar patterns that might contain かった
        self.check(matcher, "雨が{降った}らしいです。", None)  # Past verb + らしい
        self.check(matcher, "彼は{来た}はずです。", None)  # Past verb + はず

        # Potential confusion with other forms
        self.check(matcher, "彼は{来なかった}です。", None)  # Past negative verb
        self.check(matcher, "何も{分からなかった}。", None)  # Past negative verb

        # --- Edge Cases ---

        # I-adjectives in different sentence positions
        self.check(matcher, "{新しかった}車を売りました。", "新しかった")  # Modifying noun
        self.check(matcher, "車が{新しかった}です。", "新しかった")  # Predicate

        # Multiple past adjectives
        self.check(matcher, "{古かった}本と{新しかった}本がありました。", "古かった")  # Should match first

        # Embedded in longer expressions
        self.check(matcher, "それは{正しかった}考えだと思います。", "正しかった")
        self.check(matcher, "{安かった}ものを買いました。", "安かった")

        # Complex compound adjectives in past
        self.check(matcher, "その説明は{理解しやすかった}です。", "理解しやすかった")
        self.check(matcher, "その方法は{実行しにくかった}です。", "実行しにくかった")

        # With various time expressions
        self.check(matcher, "昨日は{暑かった}です。", "暑かった")
        self.check(matcher, "去年は{忙しかった}でした。", "忙しかった")
        self.check(matcher, "子供の時は{楽しかった}です。", "楽しかった")

        # In relative clauses
        self.check(matcher, "{面白かった}本を友達に貸しました。", "面白かった")
        self.check(matcher, "{美味しかった}料理のレシピを教えてください。", "美味しかった")

        # With various sentence endings
        self.check(matcher, "とても{寒かった}ね。", "寒かった")  # Casual
        self.check(matcher, "本当に{面白かった}よ。", "面白かった")  # Casual with よ
        self.check(matcher, "すごく{難しかった}なあ。", "難しかった")  # Casual with なあ
        
    def test_i_adjective_negative(self):
        matcher = compile_matcher("{i-adjective-negative}")

        # Should not match - not a negative i-adjective
        # self.check(matcher, "本当に素晴らしい眺めです", None)

        # Basic i-adjectives in negative form (くない)
        self.check(matcher, "この本は{面白くない}です。", "面白く ない")
        self.check(matcher, "今日は{暑く ない}ですね。", "暑く ない")
        self.check(matcher, "彼女は{美しく ない}人です。", "美しく ない")
        self.check(matcher, "この問題は{難しく ない}です。", "難しく ない")
        self.check(matcher, "その映画は{つまらなく ない}でした。", None)

        # Common i-adjectives in negative form
        self.check(matcher, "部屋が{広く ない}ですね。", "広く ない")
        self.check(matcher, "水が{冷たく ない}です。", "冷たく ない")
        self.check(matcher, "今日は{寒く ない}です。", "寒く ない")
        self.check(matcher, "この料理は{美味しく ない}です。", "美味しく ない")
        self.check(matcher, "宿題が{多く ない}です。", "多く ない")
        self.check(matcher, "時間が{少なく ない}です。", "少なく ない")
        self.check(matcher, "彼は{若く ない}です。", "若く ない")
        self.check(matcher, "この道は{長く ない}です。", "長く ない")
        self.check(matcher, "その話は{短く ない}です。", "短く ない")
        self.check(matcher, "値段が{高く ない}です。", "高く ない")
        self.check(matcher, "この商品は{安く ない}です。", "安く ない")

        # Size and physical properties in negative form
        self.check(matcher, "象は{大きく ない}動物です。", "大きく ない")
        self.check(matcher, "アリは{小さく ない}です。", "小さく ない")
        self.check(matcher, "この箱は{重く ない}です。", "重く ない")
        self.check(matcher, "羽は{軽く ない}です。", "軽く ない")
        self.check(matcher, "道が{狭く ない}です。", "狭く ない")
        self.check(matcher, "海は{深く ない}です。", "深く ない")
        self.check(matcher, "プールは{浅く ない}です。", "浅く ない")

        # Colors (i-adjectives) in negative form
        self.check(matcher, "血は{赤く ない}です。", "赤く ない")
        self.check(matcher, "空は{青く ない}です。", "青く ない")
        self.check(matcher, "雪は{白く ない}です。", "白く ない")
        self.check(matcher, "髪は{黒く ない}です。", "黒く ない")
        self.check(matcher, "葉っぱは{黄色く ない}です。", "黄色く ない")

        # Emotions and feelings in negative form
        self.check(matcher, "彼は{嬉しく ない}そうです。", "嬉しく ない")
        self.check(matcher, "とても{悲しく ない}気持ちです。", "悲しく ない")
        self.check(matcher, "試験が{怖く ない}です。", "怖く ない")
        self.check(matcher, "今日は{楽しく ない}日でした。", "楽しく ない")
        self.check(matcher, "とても{恥ずかしく ない}です。", "恥ずかしく ない")

        # Special i-adjectives in negative form
        self.check(matcher, "彼は{よく ない}人です。", "よく ない")  # よい → よく ない
        self.check(matcher, "天気が{よく ない}です。", "よく ない")
        # Note: いい usually becomes よく ない, not いく ない

        # Compound i-adjectives in negative form
        self.check(matcher, "この靴は{履きやすく ない}です。", "履き やすく ない")
        self.check(matcher, "漢字は{覚えにくく ない}です。", "覚え にくく ない")
        self.check(matcher, "この本は{読みやすく ない}です。", "読み やすく ない")
        self.check(matcher, "数学は{分かりにくく ない}です。", "分かり にくく ない")

        # Double negatives (adjectives already ending in ない)
        self.check(matcher, "お金が{なく ない}です。", "なく ない")  # ない → なく ない
        self.check(matcher, "時間が{足りなく ない}です。", None)
        self.check(matcher, "今日は{忙しなく ない}です。", "忙しなく ない")  # 忙しない → 忙しなく ない

        # Longer compound i-adjectives in negative form
        self.check(matcher, "この機械は{使いやすく ない}です。", "使い やすく ない")
        self.check(matcher, "彼の説明は{分かりやすく ない}です。", "分かり やすく ない")
        self.check(matcher, "この道は{歩きにくく ない}です。", "歩き にくく ない")
        self.check(matcher, "今日は{過ごしやすく ない}天気です。", "過ごし やすく ない")

        # Regional/dialectal i-adjectives in negative form
        self.check(matcher, "この料理は{うまく ない}ですね。", "うまく ない")  # うまい → うまく ない
        self.check(matcher, "今日は{えらく ない}暑いです。", "えらく ない")  # えらい → えらく ない

        # Various sentence contexts
        self.check(matcher, "この本は{面白く ない}ですか？", "面白く ない")  # Question
        self.check(matcher, "今日は{暑く ない}でしょう。", "暑く ない")  # Probability
        self.check(matcher, "彼は{優しく ない}人だと思います。", "優しく ない")  # Opinion
        self.check(matcher, "この映画は{つまらなく ない}かもしれません。", None)  # Maybe

        # With intensifiers
        self.check(matcher, "とても{暑く ない}日です。", "暑く ない")
        self.check(matcher, "すごく{面白く ない}映画でした。", "面白く ない")
        self.check(matcher, "かなり{難しく ない}問題です。", "難しく ない")
        self.check(matcher, "本当に{美味しく ない}料理です。", "美味しく ない")

        # --- False Positives (should NOT match) ---

        # Dictionary form i-adjectives (positive)
        self.check(matcher, "この本は{面白い}です。", None)
        self.check(matcher, "今日は{暑い}ですね。", None)
        self.check(matcher, "彼女は{美しい}人です。", None)
        self.check(matcher, "この問題は{難しい}です。", None)

        # Na-adjectives (not i-adjectives)
        self.check(matcher, "彼は{親切}です。", None)  # na-adjective
        self.check(matcher, "部屋が{静か}です。", None)  # na-adjective
        self.check(matcher, "とても{綺麗}ですね。", None)  # na-adjective
        self.check(matcher, "この問題は{簡単}です。", None)  # na-adjective

        # Na-adjectives with negative copula
        self.check(matcher, "彼は{親切ではない}です。", None)  # na-adjective negative
        self.check(matcher, "部屋が{静かではない}です。", None)  # na-adjective negative
        self.check(matcher, "とても{綺麗じゃない}ですね。", None)  # na-adjective negative

        # Adverbial forms (く form)
        self.check(matcher, "天気が{よく}なりました。", None)  # Adverbial form
        self.check(matcher, "とても{美しく}ありません。", None)  # Negative with ありません
        self.check(matcher, "もっと{大きく}してください。", None)  # Adverbial form
        self.check(matcher, "部屋が{広く}て良いですね。", None)  # Te-form

        # Past negative forms
        self.check(matcher, "昨日は{暑くなかった}。", None)  # Past negative
        self.check(matcher, "その映画は{面白くありませんでした}。", None)  # Polite past negative
        self.check(matcher, "天気が{よくなかった}です。", None)  # Past negative

        # Polite negative forms
        self.check(matcher, "この本は{面白くありません}。", None)  # Polite negative
        self.check(matcher, "今日は{暑くございません}。", None)  # Honorific negative
        self.check(matcher, "問題が{難しくありません}。", None)  # Polite negative

        # Nouns ending in く ない pattern
        self.check(matcher, "{悪く ない}という考えです。", "悪く ない")  # This should match - 悪い → 悪く ない
        self.check(matcher, "{良く ない}結果です。", "良く ない")  # This should match - 良い → 良く ない

        # Verbs that might have similar patterns
        self.check(matcher, "友達に{会う}。", None)  # Verb
        self.check(matcher, "本を{読む}。", None)  # Verb
        self.check(matcher, "学校に{行かない}。", None)  # Negative verb

        # Adverbs
        self.check(matcher, "{もっと}食べてください。", None)  # Adverb
        self.check(matcher, "{ずっと}待っています。", None)  # Adverb
        self.check(matcher, "{ちょっと}休みましょう。", None)  # Adverb

        # Grammar patterns that might contain く ない
        self.check(matcher, "雨が{降らない}らしいです。", None)  # Negative verb + らしい
        self.check(matcher, "彼は{来ない}はずです。", None)  # Negative verb + はず

        # Words that might look like negative i-adjectives but aren't
        self.check(matcher, "{忙しない}人です。", None)  # This is dictionary form of 忙しない
        self.check(matcher, "とても{せわしない}です。", None)  # Dictionary form

        # --- Edge Cases ---

        # I-adjectives in different sentence positions
        self.check(matcher, "{新しく ない}車を買いました。", "新しく ない")  # Modifying noun
        self.check(matcher, "車が{新しく ない}です。", "新しく ない")  # Predicate

        # Multiple negative adjectives
        self.check(matcher, "{古く ない}本と{新しく ない}本があります。", "古く ない")  # Should match first

        # Embedded in longer expressions
        self.check(matcher, "それは{正しく ない}考えだと思います。", "正しく ない")
        self.check(matcher, "{安く ない}ものを買いました。", "安く ない")

        # Potential confusion with similar endings
        self.check(matcher, "彼は{来ない}です。", None)  # Negative verb, not adjective
        self.check(matcher, "雨が{降らない}。", None)  # Negative verb
        self.check(matcher, "何も{分からない}。", None)  # Negative verb

        # Complex compound adjectives
        self.check(matcher, "この説明は{理解しやすく ない}です。", "理解 し やすく ない")
        self.check(matcher, "その方法は{実行しにくく ない}です。", "実行 し にくく ない")

        # With various particles and contexts
        self.check(matcher, "それほど{難しく ない}問題です。", "難しく ない")
        self.check(matcher, "あまり{高く ない}値段です。", "高く ない")
        self.check(matcher, "全然{面白く ない}映画でした。", "面白く ない")

    def test_verb_dictionary(self):
        matcher = compile_matcher("{verb-dictionary}")

        # Should not match - not a verb
        self.check(matcher, "本当に素晴らしい眺めです", None)

        # Basic u-verbs (godan verbs) in dictionary form
        self.check(matcher, "毎日学校に{行く}。", "行く")
        self.check(matcher, "本を{読む}のが好きです。", "読む")
        self.check(matcher, "友達に{会う}予定です。", "会う")
        self.check(matcher, "新しい車を{買う}つもりです。", "買う")
        self.check(matcher, "手紙を{書く}。", "書く")
        self.check(matcher, "音楽を{聞く}。", "聞く")
        self.check(matcher, "コーヒーを{飲む}。", "飲む")
        self.check(matcher, "ご飯を{食べる}。", "食べる")
        self.check(matcher, "家に{帰る}。", "帰る")
        self.check(matcher, "電話で{話す}。", "話す")
        self.check(matcher, "宿題を{する}。", "する")
        self.check(matcher, "日本に{来る}。", "来る")

        # Ru-verbs (ichidan verbs) in dictionary form
        self.check(matcher, "テレビを{見る}。", "見る")
        self.check(matcher, "朝早く{起きる}。", "起きる")
        self.check(matcher, "家を{出る}。", "出る")
        self.check(matcher, "友達に{教える}。", "教える")
        self.check(matcher, "質問に{答える}。", "答える")
        self.check(matcher, "新しい言葉を{覚える}。", "覚える")
        self.check(matcher, "窓を{開ける}。", "開ける")
        self.check(matcher, "ドアを{閉める}。", "閉める")
        self.check(matcher, "電気を{つける}。", "つける")
        self.check(matcher, "会議を{始める}。", "始める")
        self.check(matcher, "仕事を{辞める}。", "辞める")

        # Irregular verbs
        self.check(matcher, "宿題を{する}。", "する")
        self.check(matcher, "勉強を{する}。", "する")
        self.check(matcher, "日本に{来る}。", "来る")
        self.check(matcher, "ここに{来る}。", "来る")

        # Movement verbs
        self.check(matcher, "公園を{歩く}。", "歩く")
        self.check(matcher, "階段を{上る}。", "上る")
        self.check(matcher, "山を{下る}。", "下る")
        self.check(matcher, "プールで{泳ぐ}。", "泳ぐ")
        self.check(matcher, "空を{飛ぶ}。", "飛ぶ")
        self.check(matcher, "道路を{走る}。", "走る")

        # Daily activity verbs
        self.check(matcher, "朝ご飯を{作る}。", "作る")
        self.check(matcher, "皿を{洗う}。", "洗う")
        self.check(matcher, "部屋を{掃除する}。", "掃除 する")
        self.check(matcher, "服を{着る}。", "着る")
        self.check(matcher, "靴を{履く}。", "履く")
        self.check(matcher, "お風呂に{入る}。", "入る")
        self.check(matcher, "夜{寝る}。", "寝る")

        # Communication verbs
        self.check(matcher, "日本語を{話す}。", "話す")
        self.check(matcher, "歌を{歌う}。", "歌う")
        self.check(matcher, "冗談を{言う}。", "言う")
        self.check(matcher, "声で{呼ぶ}。", "呼ぶ")
        self.check(matcher, "手紙を{送る}。", "送る")

        # Mental/emotional verbs
        self.check(matcher, "映画を{見る}。", "見る")
        self.check(matcher, "音楽を{聞く}。", "聞く")
        self.check(matcher, "問題を{考える}。", "考える")
        self.check(matcher, "答えを{知る}。", "知る")
        self.check(matcher, "友達を{信じる}。", "信じる")
        self.check(matcher, "夢を{見る}。", "見る")

        # Work/study verbs
        self.check(matcher, "仕事を{する}。", "する")
        self.check(matcher, "会社で{働く}。", "働く")
        self.check(matcher, "大学で{学ぶ}。", "学ぶ")
        self.check(matcher, "本を{読む}。", "読む")
        self.check(matcher, "レポートを{書く}。", "書く")
        self.check(matcher, "試験を{受ける}。", "受ける")

        # --- False Positives (should NOT match) ---

        # Conjugated verbs (not dictionary form)
        self.check(matcher, "学校に{行きます}。", None)  # Polite form
        self.check(matcher, "本を{読んでいます}。", None)  # Progressive form
        self.check(matcher, "映画を{見ました}。", None)  # Past tense
        self.check(matcher, "友達に{会った}。", None)  # Past tense casual
        self.check(matcher, "宿題を{していません}。", None)  # Negative polite
        self.check(matcher, "来年{行かない}。", None)  # Negative casual
        self.check(matcher, "本を{読んだ}。", None)  # Past tense casual
        self.check(matcher, "友達と{話している}。", None)  # Progressive casual

        # Verb stems
        self.check(matcher, "友達に{会い}たいです。", None)  # i-stem
        self.check(matcher, "本を{読み}ながら食べる。", "食べる")  # i-stem
        self.check(matcher, "学校に{行き}ました。", None)  # i-stem
        self.check(matcher, "音楽を{聞き}ます。", None)  # i-stem

        # Te-form and other conjugations
        self.check(matcher, "本を{読んで}ください。", None)  # Te-form
        self.check(matcher, "学校に{行って}きます。", None)  # Te-form
        self.check(matcher, "友達に{会って}話しました。", None)  # Te-form
        self.check(matcher, "宿題を{して}から寝る。", "寝る")  # Te-form of する

        # Conditional and other forms
        self.check(matcher, "雨が{降れば}行きません。", None)  # Conditional
        self.check(matcher, "時間が{あれば}来ます。", None)  # Conditional
        self.check(matcher, "本を{読める}。", None)  # Potential form
        self.check(matcher, "漢字が{書ける}。", None)  # Potential form
        self.check(matcher, "日本語を{話せる}。", None)  # Potential form

        # Passive and causative forms
        self.check(matcher, "先生に{怒られる}。", None)  # Passive
        self.check(matcher, "友達に{笑われる}。", None)  # Passive
        self.check(matcher, "子供に{食べさせる}。", None)  # Causative
        self.check(matcher, "学生に{勉強させる}。", None)  # Causative

        # Nouns that might look like verbs
        self.check(matcher, "{愛}が大切です。", None)  # Noun
        self.check(matcher, "{夢}を見ました。", None)  # 夢 is noun, 見る is verb
        self.check(matcher, "{声}が大きいです。", None)  # Noun
        self.check(matcher, "{心}が痛いです。", None)  # Noun

        # Adjectives that might end in ru
        self.check(matcher, "この問題は{軽い}です。", None)  # i-adjective
        self.check(matcher, "彼は{優しい}人です。", None)  # i-adjective

        # Adverbs
        self.check(matcher, "{もっと}食べてください。", None)  # Adverb
        self.check(matcher, "{ずっと}待っています。", None)  # Adverb
        self.check(matcher, "{ちょっと}休みましょう。", None)  # Adverb

        # Grammar patterns that might look like verbs
        self.check(matcher, "雨が{降るらしい}です。", "降る")  # らしい pattern
        self.check(matcher, "彼は医者{らしい}です。", None)  # らしい pattern
        self.check(matcher, "明日{来るはず}です。", "来る")  # はず pattern

        # --- Edge Cases ---

        # Verbs in different sentence positions
        self.check(matcher, "{行く}人はいますか？", "行く")  # Modifying noun
        self.check(matcher, "明日{来る}予定です。", "来る")  # Modifying noun
        self.check(matcher, "{食べる}ものがありません。", "食べる")  # Modifying noun

        # Verbs with particles
        self.check(matcher, "学校に{行く}。", "行く")
        self.check(matcher, "友達と{話す}。", "話す")
        self.check(matcher, "本を{読む}。", "読む")

        # Multiple verbs in one sentence
        self.check(matcher, "本を{読む}前に{勉強する}。", "読む")  # Should match first occurrence
        self.check(matcher, "朝{起きて}{学校に行く}。", "行く")  # First is te-form, shouldn't match

        # Compound verbs
        self.check(matcher, "友達に{出会う}。", "出会う")
        self.check(matcher, "電話を{かける}。", "かける")
        self.check(matcher, "手を{上げる}。", "上げる")
        self.check(matcher, "荷物を{持つ}。", "持つ")

        # Verbs in questions
        self.check(matcher, "何を{食べる}のですか？", "食べる")
        self.check(matcher, "どこに{行く}つもりですか？", "行く")
        self.check(matcher, "いつ{来る}予定ですか？", "来る")

        # Verbs with various sentence endings
        self.check(matcher, "明日{行く}と思います。", "行く")
        self.check(matcher, "雨が{降る}かもしれません。", "降る")
        self.check(matcher, "彼は{来る}でしょう。", "来る")

        # Honorific verbs (in dictionary form)
        self.check(matcher, "先生が{いらっしゃる}。", "いらっしゃる")  # Honorific "to be"
        self.check(matcher, "お客様が{おっしゃる}。", "おっしゃる")  # Honorific "to say"

        # Humble verbs (in dictionary form)
        self.check(matcher, "私が{参る}。", "参る")  # Humble "to go/come"
        self.check(matcher, "私が{申す}。", "申す")  # Humble "to say"

        # Verbs that end in -eru but are u-verbs
        self.check(matcher, "荷物を{持つ}。", "持つ")
        self.check(matcher, "友達に{会う}。", "会う")
        self.check(matcher, "窓を{開ける}。", "開ける")  # This is actually ru-verb
        self.check(matcher, "家に{帰る}。", "帰る")  # This is u-verb despite ending in ru

        # Verbs that might be confused with other word types
        self.check(matcher, "彼は{走る}のが速い。", "走る")  # Verb
        self.check(matcher, "{走る}人を見ました。", "走る")  # Verb modifying noun
        self.check(matcher, "今{走っている}。", None)  # Progressive, not dictionary

    def test_i_adjective_dictionary(self):
        matcher = compile_matcher("{i-adjective-dictionary}")

        
        self.check(matcher, "本当に素晴らしい眺めです", None)

        # Basic i-adjectives in dictionary form (ending inい)
        self.check(matcher, "この本は{面白い}です。", "面白い")
        self.check(matcher, "今日は{暑い}ですね。", "暑い")
        self.check(matcher, "彼女は{美しい}人です。", "美しい")
        self.check(matcher, "この問題は{難しい}です。", "難しい")
        self.check(matcher, "その映画は{つまらない}でした。", None)

        # Common i-adjectives
        self.check(matcher, "部屋が{広い}ですね。", "広い")
        self.check(matcher, "水が{冷たい}です。", "冷たい")
        self.check(matcher, "今日は{寒い}です。", "寒い")
        self.check(matcher, "この料理は{美味しい}です。", "美味しい")
        self.check(matcher, "宿題が{多い}です。", "多い")
        self.check(matcher, "時間が{少ない}です。", "少ない")
        self.check(matcher, "彼は{若い}です。", "若い")
        self.check(matcher, "この道は{長い}です。", "長い")
        self.check(matcher, "その話は{短い}です。", "短い")
        self.check(matcher, "値段が{高い}です。", "高い")
        self.check(matcher, "この商品は{安い}です。", "安い")

        # Size and physical properties
        self.check(matcher, "象は{大きい}動物です。", "大きい")
        self.check(matcher, "アリは{小さい}です。", "小さい")
        self.check(matcher, "この箱は{重い}です。", "重い")
        self.check(matcher, "羽は{軽い}です。", "軽い")
        self.check(matcher, "道が{狭い}です。", "狭い")
        self.check(matcher, "海は{深い}です。", "深い")
        self.check(matcher, "プールは{浅い}です。", "浅い")

        # Colors (i-adjectives)
        self.check(matcher, "血は{赤い}です。", "赤い")
        self.check(matcher, "空は{青い}です。", "青い")
        self.check(matcher, "雪は{白い}です。", "白い")
        self.check(matcher, "髪は{黒い}です。", "黒い")
        self.check(matcher, "葉っぱは{黄色い}です。", "黄色い")

        # Emotions and feelings
        self.check(matcher, "彼は{嬉しい}そうです。", "嬉しい")
        self.check(matcher, "とても{悲しい}気持ちです。", "悲しい")
        self.check(matcher, "試験が{怖い}です。", "怖い")
        self.check(matcher, "今日は{楽しい}日でした。", "楽しい")
        self.check(matcher, "とても{恥ずかしい}です。", "恥ずかしい")

        # Negative i-adjectives (ending in ない)
        self.check(matcher, "お金が{ない}です。", None) # Standalone i-adjective
        self.check(matcher, "時間が{足りない}です。", None)
        self.check(matcher, "今日は{忙しく ない}です。", None)  # This is conjugated form, not dictionary
        self.check(matcher, "問題が{ない}と思います。", None)

        # Special i-adjectives
        self.check(matcher, "彼は{いい}人です。", "いい")  #いい (colloquial form of よい)
        self.check(matcher, "天気が{よい}です。", "よい")  # よい (formal form ofいい)

        # Compound i-adjectives
        self.check(matcher, "この靴は{履きやすい}です。", "履き やすい")
        self.check(matcher, "漢字は{覚えにくい}です。", "覚え にくい")
        self.check(matcher, "この本は{読みやすい}です。", "読み やすい")
        self.check(matcher, "数学は{分かりにくい}です。", "分かり にくい")

        # --- False Positives (should NOT match) ---

        # Na-adjectives (not i-adjectives)
        self.check(matcher, "彼は{親切}です。", None)  # na-adjective
        self.check(matcher, "部屋が{静か}です。", None)  # na-adjective
        self.check(matcher, "とても{綺麗}ですね。", None)  # na-adjective
        self.check(matcher, "この問題は{簡単}です。", None)  # na-adjective
        self.check(matcher, "彼女は{元気}です。", None)  # na-adjective

        # Nouns ending inい
        self.check(matcher, "{愛}が大切です。", None)  # 愛 (ai) - noun
        self.check(matcher, "{背}が高いです。", "高い")  # 背 (se) - noun
        self.check(matcher, "{声}が大きいです。", "大きい")  # 声 (koe) - noun
        self.check(matcher, "{恋}をしています。", None)  # 恋 (koi) - noun

        # Verbs ending inい sound
        self.check(matcher, "友達に{会い}ます。", None)  # 会う verb stem
        self.check(matcher, "本を{買い}ました。", None)  # 買う verb stem
        self.check(matcher, "歌を{歌い}ます。", None)  # 歌う verb stem

        # Conjugated i-adjectives (not dictionary form)
        self.check(matcher, "天気が{よく}なりました。", None)  # Adverbial form
        self.check(matcher, "とても{美しく}ありません。", None)  # Adverbial form
        self.check(matcher, "昨日は{暑く}なかった。", None)  # Past negative stem
        self.check(matcher, "今日は{寒く}ないです。", None)  # Negative stem
        self.check(matcher, "もっと{大きく}してください。", None)  # Adverbial form
        self.check(matcher, "部屋が{広く}て良いですね。", "良い")  # Te-form

        # Adverbs that might look like i-adjectives
        self.check(matcher, "{もっと}食べてください。", None)  # Adverb
        self.check(matcher, "{ずっと}待っています。", None)  # Adverb
        self.check(matcher, "{とても}美味しいです。", "美味しい")  # Adverb
        self.check(matcher, "{ちょっと}休みましょう。", None)  # Adverb

        # Particles and grammar ending inい
        self.check(matcher, "本{という}ものです。", None)  # Grammar pattern
        self.check(matcher, "学校{に}行きます。", None)  # Particle
        self.check(matcher, "友達{と}会います。", None)  # Particle

        # --- Edge Cases ---

        # I-adjectives in different sentence positions
        self.check(matcher, "{新しい}車を買いました。", "新しい")  # Modifying noun
        self.check(matcher, "車が{新しい}です。", "新しい")  # Predicate
        self.check(matcher, "{古い}本と{新しい}本があります。", "古い")  # Multiple adjectives

        # I-adjectives with intensifiers
        self.check(matcher, "とても{暑い}日です。", "暑い")
        self.check(matcher, "すごく{面白い}映画でした。", "面白い")
        self.check(matcher, "かなり{難しい}問題です。", "難しい")
        self.check(matcher, "本当に{美味しい}料理です。", "美味しい")

        # Longer compound i-adjectives
        self.check(matcher, "この機械は{使いやすい}です。", "使い やすい")
        self.check(matcher, "彼の説明は{分かりやすい}です。", "分かり やすい")
        self.check(matcher, "この道は{歩きにくい}です。", "歩き にくい")
        self.check(matcher, "今日は{過ごしやすい}天気です。", "過ごし やすい")

        # I-adjectives in questions
        self.check(matcher, "この本は{面白い}ですか？", "面白い")
        self.check(matcher, "今日は{暑い}ですか？", "暑い")
        self.check(matcher, "日本語は{難しい}ですか？", "難しい")

        # I-adjectives with various sentence endings
        self.check(matcher, "彼は{優しい}人だと思います。", "優しい")
        self.check(matcher, "この映画は{つまらない}かもしれません。", None)
        self.check(matcher, "今日は{忙しい}でしょう。", "忙しい")

        # Regional/dialectal i-adjectives
        self.check(matcher, "この料理は{うまい}ですね。", "うまい")  # うまい (delicious, casual)
        self.check(matcher, "今日は{えらい}暑いです。", "えらい")  # えらい (very, dialectal)

        # Archaic or formal i-adjectives
        self.check(matcher, "とても{美しい}景色です。", "美しい")
        self.check(matcher, "{正しい}答えを選んでください。", "正しい")
        self.check(matcher, "彼の考えは{新しい}です。", "新しい")

        # Potential confusion with similar patterns
        self.check(matcher, "彼は医者{らしい}です。", None)  # らしい is not pure i-adjective
        self.check(matcher, "雨が{降るらしい}です。", None)  # Grammar pattern, not adjective
        self.check(matcher, "今日は{暖かそう}です。", None)  # そう form, not dictionary
        self.check(matcher, "この問題は{易しそう}に見えます。", None)  # そう form, not dictionary

        # Numbers that might end inい sound
        self.check(matcher, "{四}時に会いましょう。", None)  # Number
        self.check(matcher, "{九}時です。", None)  # Number

        # Katakana words ending inい sound
        self.check(matcher, "{コーヒー}を飲みます。", None)  # Katakana noun
        self.check(matcher, "{パーティー}に行きます。", None)  # Katakana noun



    def test_verb_volitional(self):
        matcher = compile_matcher("{verb-volitional}")

        self.check(matcher, "やろう！", "やろう")
        self.check(matcher, "今日 中 に この 仕事 を {終わら せよう}！", "終わら せよう")

        # Basic volitional usage
        self.check(matcher, "映画を見よう。", "見よう")
        self.check(matcher, "一緒に食べましょう。", "食べ ましょう")

        # Ichidan verbs (easy: drop る, addよう)
        self.check(matcher, "映画を見ようか。", "見よう")
        self.check(matcher, "ご飯を食べよう。", "食べよう")
        self.check(matcher, "早く起きよう。", "起きよう")
        self.check(matcher, "もう寝よう。", "寝よう")
        self.check(matcher, "新しい服を着よう。", "着よう")
        self.check(matcher, "手紙を出そう。", "出そう")

        # Godan verbs - o-stem +う
        # 1.う verbs -> おう
        self.check(matcher, "友達に会おう。", "会おう")
        self.check(matcher, "歌を歌おう。", "歌おう")
        self.check(matcher, "家を買おう。", "買おう")
        self.check(matcher, "今日は休もう。", "休もう")  # む verb

        # 2. く verbs -> こう
        self.check(matcher, "手紙を書こう。", "書こう")
        self.check(matcher, "駅まで歩こう。", "歩こう")
        self.check(matcher, "音楽を聞こう。", "聞こう")

        # 3. ぐ verbs -> ごう
        self.check(matcher, "海で泳ごう。", "泳ごう")
        self.check(matcher, "急ごう。", "急ごう")
        self.check(matcher, "服を脱ごう。", "脱ごう")

        # 4. す verbs -> そう
        self.check(matcher, "友達と話そう。", "話そう")
        self.check(matcher, "新しいことを試そう。", "試そう")
        self.check(matcher, "本を貸そう。", "貸そう")

        # 5. つ verbs -> とう
        self.check(matcher, "手紙を待とう。", "待とう")
        self.check(matcher, "強く打とう。", "打とう")

        # 6. ぬ verbs -> のう
        self.check(matcher, "若くして死のう。", "死のう")

        # 7. ぶ verbs -> ぼう
        self.check(matcher, "みんなで遊ぼう。", "遊ぼう")
        self.check(matcher, "新しい技を学ぼう。", "学ぼう")
        self.check(matcher, "本を読もう。", "読もう")  # む verb

        # 8. む verbs -> もう
        self.check(matcher, "本を読もう。", "読もう")
        self.check(matcher, "今日は飲もう。", "飲もう")

        # 9. る godan verbs -> ろう
        self.check(matcher, "家に帰ろう。", "帰ろう")
        self.check(matcher, "部屋に入ろう。", "入ろう")
        self.check(matcher, "紙を切ろう。", "切ろう")
        self.check(matcher, "その本を取ろう。", "取ろう")

        # Irregular verbs
        self.check(matcher, "日本に行こう。", "行こう")  # 行く (iku) -> 行こう (ikou)
        self.check(matcher, "友達が来よう。", "来よう")  # 来る (kuru) -> 来よう (koyou)
        self.check(matcher, "宿題をしよう。", "しよう")  # する (suru) -> しよう (shiyou)

        # Compound verbs (volitional of the last verb)
        self.check(matcher, "立ち上がろう。", "立ち上がろう")  # 立ち上がる (tachiagaru - godan)
        self.check(matcher, "走り続けよう。", "続けよう")  # 走り続ける (hashiritsuzukeru - ichidan)
        self.check(matcher, "話し合おう。", "話し合おう")  # 話し合う (hanashiau - godan)
        self.check(matcher, "書き直そう。", "書き直そう")  # 書き直す (kakinaosu - godan)

        # Volitional in different contexts
        self.check(matcher, "一緒に食べようか。", "食べよう")  # ~ou ka (suggestion)
        self.check(matcher, "映画を見ようと思う。", "見よう")  # ~ou to omou (intend to)
        self.check(matcher, "行こうとした。", "行こう")  # ~ou to suru (try to)
        self.check(matcher, "帰ろうとしている。", "帰ろう")  # ~ou to shite iru (be about to)

        # Polite volitional (ましょう)
        self.check(matcher, "一緒に食べましょう。", "食べ ましょう")  # Should this match? Depends on your grammar
        self.check(matcher, "始めましょう。", "始め ましょう")
        
        # Loanwords with する
        self.check(matcher, "ジョギングしよう。", "しよう")  # ジョギングする
        self.check(matcher, "コピーしよう。", "しよう")  # コピーする

        # --- Negative tests (should NOT match) ---
        
        # Particles and other grammar
        self.check(matcher, "これはペンでしょう。", None)  # でしょう (probably/conjecture)
        self.check(matcher, "そうでしょう。", None)  # でしょう
        self.check(matcher, "来るでしょう。", None)  # でしょう
        
        # Adjectives
        self.check(matcher, "美しい花ですね。", None)  # 美しい (beautiful) - i-adjective
        self.check(matcher, "新しい本を買った。", None)  # 新しい (new) - i-adjective
        
        # Nouns ending in similar sounds
        self.check(matcher, "病院で診察を受けよう。", "受けよう")  # 受ける is ichidan
        self.check(matcher, "図書館で本を借りよう。", "借りよう")  # 借りる is ichidan
        
        # Words that end in ou but are not volitional
        self.check(matcher, "どうしよう。", "しよう")  # どうする -> どうしよう (this IS volitional)
        self.check(matcher, "ありがとう。", None)  # ありがとう (thank you) - not a verb
        self.check(matcher, "おはよう。", None)  # おはよう (good morning) - not a verb
        self.check(matcher, "こんにちは。そうですか。", None)  # そう (so/like that) - not a verb
        
        # Adverbs and other parts of speech
        self.check(matcher, "どう思いますか。", None)  # どう (how) - adverb
        self.check(matcher, "そう思います。", None)  # そう (so/like that) - adverb
        
        # Potential form confusion
        self.check(matcher, "泳げるようになった。", None)  #ように (in order to/so that) - not volitional
        self.check(matcher, "見えるようだ。", None)  #ようだ (seems like) - not volitional
        
        # Onomatopoeia and other expressions
        self.check(matcher, "わんわん鳴こう。", "鳴こう")  # わんわん (bow-wow) + 鳴く (bark)
        
        # Complex sentences with multiple potential matches
        self.check(matcher, "明日は早く起きて、運動しよう。", "しよう")  # Should only match the volitional
        self.check(matcher, "本を読んでから、映画を見よう。", "見よう")  # Should only match the volitional
        
        # Edge cases with compound expressions
        self.check(matcher, "頑張ろうと思っている。", "頑張ろう")  # 頑張る (ganbaru) -> 頑張ろう
        self.check(matcher, "やってみよう。", "みよう")  # みる (miru) -> みよう (try doing)
        
        # Verbs that could be confused with other forms
        self.check(matcher, "食べようとした。", "食べよう")  # volitional + to suru
        self.check(matcher, "行こうと決めた。", "行こう")  # volitional + to kimeru
        
        # Exploitation tests for tricky segmentation
        self.check(matcher, "今度会おうね。", "会おう")  # 会う (au) -> 会おう (aou)
        self.check(matcher, "もっと頑張ろう。", "頑張ろう")  # 頑張る (ganbaru) -> 頑張ろう (ganbarou)
        self.check(matcher, "一緒に帰ろうか。", "帰ろう")  # 帰る (kaeru) -> 帰ろう (kaerou)

    def test_verb_te(self):
        matcher = compile_matcher("{verb-te}")

        
        self.check(matcher, "いつ まで も {寂し がっ て ばかり はい られ ない}。何 か する こと を 見つけ ない と。", "寂しがって")

        # Ichidan verbs (easy: drop る, add て)
        self.check(matcher, "映画を見て、それから晩ご飯を食べました。", "見 て")
        self.check(matcher, "ご飯を食べて、すぐに出かけました。", "食べ て")
        self.check(matcher, "起きて、顔を洗いました。", "起き て")
        self.check(matcher, "寝て、夢を見ました。", "寝 て")

        # Godan verbs
        # 1.う, つ, る ->っ て (促音便 - sokuonbin)
        self.check(matcher, "友達に会って、楽しかった。", "会っ て")
        self.check(matcher, "電車に乗って、旅行に行きました。", "乗っ て")
        self.check(matcher, "手紙を書いて、送りました。", "書い て") # This is a 'ku' verb, not 'u', 'tsu', 'ru'
        self.check(matcher, "本を売って、新しいのを買いました。", "売っ て") # 'ru' ending
        self.check(matcher, "傘を持って、家を出ました。", "持っ て") # 'tsu' ending

        # 2. ぬ, ぶ, む ->ん で (撥音便 - hatsuonbin)
        self.check(matcher, "死んで、生まれ変わる。", "死ん で")
        self.check(matcher, "遊んで、疲れた。", "遊ん で")
        self.check(matcher, "本を読んで、寝ました。", "読ん で")

        # 3. く ->い て (イ音便 - ionbin)
        self.check(matcher, "漢字を書いて、練習しました。", "書い て")
        self.check(matcher, "歩いて、駅まで行った。", "歩い て")

        # 4. ぐ ->いで (イ音便 - ionbin, voiced)
        self.check(matcher, "泳いで、疲れた。", "泳い で")
        self.check(matcher, "急いで、出発した。", "急い で")

        # 5. す -> して
        self.check(matcher, "友達と話して、元気になった。", "話し て")
        self.check(matcher, "音楽を聴いて、リラックスした。", "聴い て") # This is a 'ku' verb. 'kiku' -> kiite.
        self.check(matcher, "服を脱いで、シャワーを浴びた。", "脱い で") # 'gu' verb. 'nugu' -> nuide.

        # Irregular verbs
        self.check(matcher, "日本に行って、寿司を食べたい。", "行っ て") # 行く (iku) is a special case of く ending
        self.check(matcher, "友達が来て、賑やかになった。", "来 て") # 来る (kuru)
        self.check(matcher, "宿題をして、遊びに行った。", "し て") # する (suru)

        # Compound verbs (te-form of the last verb)
        self.check(matcher, "立ち上がって、挨拶した。", "立ち上がっ て") # 立ち上がる (tachiagaru - godan)
        self.check(matcher, "走り続けて、ゴールした。", "続け て") # 走り続ける (hashiritsuzukeru - ichidan)

        # Verbs followed by other grammar patterns using te-form
        self.check(matcher, "本を読んでいます。", "読ん で") # ~te iru (progressive/state)
        self.check(matcher, "座ってください。", "座っ て") # ~te kudasai (request)
        self.check(matcher, "食べてもいいですか。", "食べ て") # ~te mo ii (permission)
        self.check(matcher, "書いてみる。", "書い て") # ~te miru (try doing)

        # Edge cases/Ambiguity (depending on your matcher's sophistication)
        # Some words that end in 'te' but are not te-form verbs (e.g., adverbs)
        # Your matcher should ideally not pick these up.
        # self.check(matcher, "とても美味しい。", None) # 'totte mo' is not a te-verb
        # self.check(matcher, "やっと着いた。", None) # 'yatto' is not a te-verb

        # Verbs that are one syllable + ru (often ichidan, but some godan)
        self.check(matcher, "切って、パンを食べた。", "切っ て") # 切る (kiru - godan)
        self.check(matcher, "帰って、休んだ。", "帰っ て") # 帰る (kaeru - godan)
        self.check(matcher, "入って、座った。", "入っ て") # 入る (hairu - godan)

        # Loanwords/Gairaigo that are verbed with する
        self.check(matcher, "ジョギングして、汗をかいた。", "し て") # ジョギングする

        # --- 1. Particles ending in て/で ---
        # The particle 'te' for listing actions (not a verb te-form)
        self.check(matcher, "雨が降って、傘を持って出かけた。", "降っ て") # '降って' is a verb, '持って' is a verb
        self.check(matcher, "私とあなたとで、これを完成させよう。", None) # とで (to-de) is a particle
        self.check(matcher, "誰にでもできる簡単な仕事です。", None) # にでも (ni-demo) is a particle
        self.check(matcher, "それはさておき、本題に入りましょう。", None) # さて (sate) is an adverbial particle/conjunction
        self.check(matcher, "どこまで行っても、同じ景色だった。", "行っ て") # まで (made) is a particle

        # --- 2. Adverbs/Other words ending in て/で ---
        self.check(matcher, "とても美味しいケーキですね。", None) # とても (totemo) - adverb
        self.check(matcher, "やっと宿題が終わった。", None) # やっと (yatto) - adverb
        self.check(matcher, "まるで夢のようだ。", None) # まるで (marude) - adverb
        self.check(matcher, "たいてい毎日運動します。", None) # たいてい (taitei) - adverb
        self.check(matcher, "ぐっすり寝て、疲れが取れた。", "寝 て") # ぐっすり (gussuri) - adverb (here '寝て' is the verb)
        self.check(matcher, "きっぱり断った。", None) # きっぱり (kippari) - adverb
        self.check(matcher, "はっきり言った方がいい。", None) # はっきり (hakkiri) - adverb

        # --- 3. Nouns ending in て/で ---
        self.check(matcher, "これは手で持ってください。", "持っ て") # 手 (te) - noun, "hand"
        self.check(matcher, "今日は雨で、外出できません。", None) # 雨で (ame de) - noun + particle 'de' (reason/state)
        self.check(matcher, "お茶碗の底を見てください。", "見 て") # 底 (soko) - noun, "bottom" (here '見て' is the verb)

        # --- 4. Conjugated nouns/adjectives that look like verbs ---
        self.check(matcher, "彼が苦手で、話しかけにくい。", None) # 苦手で (nigate de) - な-adjective + particle 'de'
        self.check(matcher, "静かで、勉強しやすい場所だ。", None) # 静かで (shizuka de) - な-adjective + particle 'de'
        self.check(matcher, "寒くて、震えていた。", "震え て") # 寒くて (samukute) -い-adjective te-form (should NOT be matched if you only want VERBS)
                                                            # If your matcher specifically targets {verb-te}, this should be None.
                                                            # If it targets {adjective-te} too, then it would be '寒くて'.
                                                            # It's critical to define if {verb-te} includes i-adjectives. Assuming no.

        # --- 5. Potential partial matches or tricky segmentations ---
        self.check(matcher, "この曲を聞いてから寝よう。", "聞い て") # 聞いて (kiite) is the verb
        self.check(matcher, "これはちょっと待ってくれ。", "待っ て") # 待って (matte) is the verb
        self.check(matcher, "立て札がある。", None) # 立て札 (tatefuda) - noun (signboard). '立て' is part of the noun.
        self.check(matcher, "手洗いをする。", None) # 手洗い (tearai) - noun (handwashing). '手洗い' is a single noun.
        self.check(matcher, "来て見てください。", "来 て") # The first '来て' is the verb, '見て' is the second verb
        self.check(matcher, "これはお酒です。飲んでください。", "飲ん で") # 飲んで (nonde) is the verb
        self.check(matcher, "彼の予定だ。", None) # 予定 (yotei) - noun. '予定だ' is noun + copula.

        # --- Exploit Tests ---

        # I. Godan Verbs with `る` ending (Most Critical Gap Identified):
        self.check(matcher, "家に帰って、すぐ寝た。", "帰っ て")
        self.check(matcher, "部屋に入って、電気をつけた。", "入っ て")
        self.check(matcher, "紙を切って、遊んだ。", "切っ て")
        self.check(matcher, "そこに本が沢山あって、驚いた。", "あっ て")
        self.check(matcher, "この本を取ってくれる？", "取っ て")

        # II. Irregular Verb `行く` (iku - to go, Irregular):
        # This is also a positive test but crucial to ensure it overrides general rules.
        self.check(matcher, "日本に行って、寿司を食べたい。", "行っ て")

        # III. Ambiguity with Other Parts of Speech (False Positives):
        self.check(matcher, "私は学生で、彼は先生です。", None) # Copula/Particle
        self.check(matcher, "この部屋は広くて、明るい。", None) # i-adjective te-form
        self.check(matcher, "静かで、落ち着く場所だ。", None) # na-adjective te-form
        self.check(matcher, "鉛筆で書いた。", None) # Noun + particle 'de' (means)
        self.check(matcher, "駅で会った。", None) # Noun + particle 'de' (location)
        self.check(matcher, "病気で休んだ。", None) # Noun + particle 'de' (reason)
        self.check(matcher, "とても美味しいケーキですね。", None) # Adverb
        self.check(matcher, "やっと宿題が終わった。", None) # Adverb
        self.check(matcher, "どうしても行きたい。", 'し て') # Adverb
        self.check(matcher, "だんだん暖かくなってきた。", 'なっ て') # Adverb
        self.check(matcher, "きらきら光る星。", None) # Onomatopoeia (adverbial)
        self.check(matcher, "ぞろぞろ出てきた。", "出 て") # Onomatopoeia + verb (only verb should match)
        self.check(matcher, "お茶碗の底を見てください。", "見 て") # Noun "底" (bottom)

        # IV. Compound Verbs / Phrasal Verbs:
        self.check(matcher, "話し合って、決めた。", "話し合っ て") # 話し合う (Godan compound)
        self.check(matcher, "書き直して、提出した。", "書き直し て") # 書き直す (Godan compound)

        # V. Verbs with Katakana readings (Loanwords conjugated with する):
        self.check(matcher, "書類をコピーして、提出した。", "し て") # コピーする
        self.check(matcher, "会議をキャンセルして、別の日にした。", "し て") # キャンセルする

    def test_verb_imperative(self):
        matcher = compile_matcher("{verb-imperative}")

        
        self.check(matcher, "{くれ}！", None)

        # Basic imperative usage
        self.check(matcher, "早く{寝ろ}！", "寝ろ")

        # Ichidan verbs (drop る, add ろ)
        self.check(matcher, "映画を見ろ。", "見ろ")
        self.check(matcher, "ご飯を食べろ。", "食べろ")
        self.check(matcher, "早く起きろ！", "起きろ")
        self.check(matcher, "もう寝ろ。", "寝ろ")
        self.check(matcher, "ここで降りろ。", "降りろ")

        # Godan verbs - various endings
        # 1.う ending -> え
        self.check(matcher, "彼に会え。", "会え")
        self.check(matcher, "もっと笑え！", "笑え")
        self.check(matcher, "新しい本を買え。", "買え")
        self.check(matcher, "歌え！", "歌え")

        # 2. つ ending -> て
        self.check(matcher, "少し待て。", "待て")
        self.check(matcher, "ボールを持て。", "持て")
        self.check(matcher, "もう打て。", "打て")

        # 3. る ending (godan) -> れ
        self.check(matcher, "本を売れ。", None)
        self.check(matcher, "早く帰れ！", "帰れ")
        self.check(matcher, "部屋に入れ。", None)
        self.check(matcher, "紙を切れ。", "切れ")
        self.check(matcher, "それを取れ。", "取れ")

        # 4. く ending -> け
        self.check(matcher, "漢字を書け。", "書け")
        self.check(matcher, "歩け！", "歩け")
        self.check(matcher, "よく聞け。", "聞け")
        self.check(matcher, "窓を開け。", None)

        # 5. ぐ ending -> げ
        self.check(matcher, "防げ！", "防げ")
        self.check(matcher, "急げ！", "急げ")
        self.check(matcher, "服を脱げ。", "脱げ")

        # 6. す ending -> せ
        self.check(matcher, "友達と話せ。", "話せ")
        self.check(matcher, "もっと出せ！", "出せ")
        self.check(matcher, "宿題を見せ。", None)

        # 7. ぬ ending -> ね
        self.check(matcher, "死ね！", "死ね")  # Strong imperative

        # 8. ぶ ending -> べ
        self.check(matcher, "友達を呼べ。", "呼べ")
        self.check(matcher, "もっと学べ。", "学べ")

        # 9. む ending -> め
        self.check(matcher, "本を読め。", "読め")
        self.check(matcher, "痛みを止め。", None)
        self.check(matcher, "住め。", "住め")

        # Irregular verbs
        self.check(matcher, "こっちに来い！", "来い")  # 来る (kuru) -> 来い (koi)
        self.check(matcher, "宿題をしろ。", "しろ")   # する (suru) -> しろ (shiro)
        self.check(matcher, "日本に行け。", "行け")   # 行く (iku) -> 行け (ike) - special godan

        # Compound verbs (imperative of the last verb)
        self.check(matcher, "立ち上がれ！", "立ち上がれ")  # 立ち上がる (tachiagaru - godan)
        self.check(matcher, "走り続けろ。", "続けろ")    # 走り続ける (hashiritsuzukeru - ichidan)
        self.check(matcher, "話し合え。", "話し合え")    # 話し合う (hanashiau - godan)
        self.check(matcher, "書き直せ。", "書き直せ")    # 書き直す (kakinaosu - godan)

        # Honorific/Polite commands (using なさい - should NOT match if targeting bare imperatives)
        self.check(matcher, "座りなさい。", None)  # Polite imperative
        self.check(matcher, "食べなさい。", None)  # Polite imperative
        self.check(matcher, "勉強しなさい。", None)  # Polite imperative

        # Negative imperatives (should NOT match as they're different grammar)
        self.check(matcher, "行くな！", None)  # Negative imperative
        self.check(matcher, "するな。", None)  # Negative imperative
        self.check(matcher, "食べるな。", None)  # Negative imperative

        # Request forms (should NOT match)
        self.check(matcher, "座ってください。", None)  # Polite request
        self.check(matcher, "食べてくれ。", None)   # Casual request
        self.check(matcher, "来てくれる？", None)   # Question request

        # --- False Positives (words ending in imperative-like sounds) ---

        # Nouns that end in imperative-like syllables
        self.check(matcher, "時計を見せてくれる？", None) 
        self.check(matcher, "この瀬戸際で何をする？", None)  # 瀬戸際 (setogai) - noun
        self.check(matcher, "彼の姿勢がいい。", None)  # 姿勢 (shisei) - noun
        self.check(matcher, "会議の議題は何？", None)  # 議題 (gidai) - noun
        self.check(matcher, "新しい時代が来た。", None)  # 時代 (jidai) - noun

        # Adjectives ending in similar sounds
        self.check(matcher, "この部屋は広い。", None)  #い-adjective
        self.check(matcher, "彼は元気だ。", None)  # な-adjective
        self.check(matcher, "静かな場所だ。", None)  # な-adjective

        # Particles and other grammar
        self.check(matcher, "誰にでもできる。", None)  # Particle combination
        self.check(matcher, "どこまでも行く。", None)  # Particle combination
        self.check(matcher, "それはさておき。", None)  # Set phrase

        # Adverbs ending in similar sounds
        self.check(matcher, "きっぱり断った。", None)  # Adverb
        self.check(matcher, "はっきり言え。", "言え")  # Here '言え' should match
        self.check(matcher, "ゆっくり歩け。", "歩け")  # Here '歩け' should match

        # Verbs in other forms that might look like imperatives
        self.check(matcher, "彼が来れば良い。", None)  # Conditional form
        self.check(matcher, "食べれる？", None)  # Potential form (colloquial)
        self.check(matcher, "見れない。", None)  # Potential negative (colloquial)

        # --- Exploitation Tests (Critical edge cases) ---

        # I. Godan verbs with る ending (most commonly confused with ichidan)
        self.check(matcher, "家に帰れ！", "帰れ")
        self.check(matcher, "部屋に入れ。", None)
        self.check(matcher, "紙を切れ。", "切れ")
        self.check(matcher, "それを取れ。", "取れ")
        self.check(matcher, "もっと知れ。", "知れ")  # 知る (shiru)

        # II. One-mora verbs and their imperatives
        self.check(matcher, "見ろ！", "見ろ")   # 見る (miru)
        self.check(matcher, "出ろ！", "出ろ")   # 出る (deru)  
        self.check(matcher, "来い！", "来い")   # 来る (kuru) - irregular

        # III. Verbs that could be confused with other word types
        self.check(matcher, "手で持て。", "持て")  # 手 (te) is noun, 持て (mote) is imperative
        self.check(matcher, "底を見ろ。", "見ろ")  # 底 (soko) is noun, 見ろ (miro) is imperative

        # IV. Compound/complex verbs
        self.check(matcher, "振り返れ！", "振り返れ")  # 振り返る (furikaeru)
        self.check(matcher, "飛び跳ねろ。", "飛び跳ねろ")  # 飛び跳ねる (tobihaneru)
        self.check(matcher, "立ち止まれ。", "立ち止まれ")  # 立ち止まる (tachidomaru)

        # V. Loanwords with する (should produce しろ)
        self.check(matcher, "書類をコピーしろ。", "しろ")  # コピーする
        self.check(matcher, "会議をキャンセルしろ。", "しろ")  # キャンセルする
        self.check(matcher, "データをダウンロードしろ。", "しろ")  # ダウンロードする

        # VI. Context where imperatives appear with other grammar
        self.check(matcher, "今すぐ来い！", "来い")
        self.check(matcher, "絶対に負けるな！", None)  # Negative imperative - should not match
        self.check(matcher, "頑張れ、君なら出来る！", "頑張れ")
        self.check(matcher, "信じろ、自分を。", "信じろ")

        # VII. Potential ambiguity with shortened forms
        self.check(matcher, "食べれない。", None)  # Colloquial potential (not imperative)
        self.check(matcher, "来れる？", None)  # Colloquial potential (not imperative)
        self.check(matcher, "見れた。", None)  # Colloquial potential past (not imperative)

    def test_verb_eba_forms(self):
        matcher = compile_matcher("{verb-eba}") # Assuming this compiles your pattern
        
        self.check(matcher, "試験 に 合格 し たけれ ば、毎日 勉強 す べき だ。", "したければ")
        self.check(matcher, "分から なけれ ば、質問 し て ください。。 ", "なけれ ば")
        self.check(matcher, "早く 行け ば、混雑 を 避け られ ます。 ", "行け ば")
        # --- Positive Tests ---

        # Irregular Verbs
        self.check(matcher, "勉強すれば、合格するだろう。", "すれ ば") # する -> すれば
        self.check(matcher, "彼が来れば、パーティーが始まる。", "来れ ば") # 来る -> くれば

        # Ichidan Verbs (Drop る, addれ ば)
        self.check(matcher, "食べれば、元気が出る。", "食べれ ば") # 食べる -> 食べれば
        self.check(matcher, "見れば、わかるはずだ。", "見れ ば") # 見る -> 見れば
        self.check(matcher, "起きれば、すぐに準備しよう。", "起きれ ば") # 起きる -> 起きれば
        self.check(matcher, "寝れば、疲れが取れる。", "寝れ ば") # 寝る -> 寝れば

        # Godan Verbs (Change final vowel to 'e' sound, add ば)
        #う ->え ば
        self.check(matcher, "買えば、ポイントがつく。", "買え ば") # 買う -> 買えば
        self.check(matcher, "会えば、話せるだろう。", "会え ば") # 会う -> 会えば

        # つ -> てば
        self.check(matcher, "待てば、そのうち来る。", "待て ば") # 待つ -> 待てば

        # る ->れ ば (Godan verbs)
        self.check(matcher, "帰れば、ゆっくりできる。", "帰れ ば") # 帰る -> 帰れば
        self.check(matcher, "取れば、もらえる。", "取れ ば") # 取る -> 取れば
        self.check(matcher, "切れば、短くなる。", "切れ ば") # 切る -> 切れば
        self.check(matcher, "あれば、便利だ。", "あれ ば") # ある -> あれば
        self.check(matcher, "入れば、座れる。", "入れ ば") # 入る -> 入れば

        # く -> けば
        self.check(matcher, "書けば、上達する。", "書け ば") # 書く -> 書けば
        self.check(matcher, "聞けば、教えてくれる。", "聞け ば") # 聞く -> 聞けば
        self.check(matcher, "歩けば、健康になる。", "歩け ば") # 歩く -> 歩けば

        # ぐ -> げば
        self.check(matcher, "泳げば、気持ちいい。", "泳げ ば") # 泳ぐ -> 泳げば
        self.check(matcher, "急げば、間に合う。", "急げ ば") # 急ぐ -> 急げば

        # す -> せば
        self.check(matcher, "話せば、わかる。", "話せ ば") # 話す -> 話せば

        # ぬ -> ねば (less common but valid)
        self.check(matcher, "死ねば、終わりだ。", "死ね ば") # 死ぬ -> 死ねば

        # ぶ -> べば
        self.check(matcher, "遊べば、リフレッシュできる。", "遊べ ば") # 遊ぶ -> 遊べば

        # む -> めば
        self.check(matcher, "読めば、知識が増える。", "読め ば") # 読む -> 読めば


        # --- Negative Tests (Likely to cause false positives if not careful) ---

        # Adjectives in Eba form (should NOT be matched if only targeting verbs)
        self.check(matcher, "安ければ、買う。", None) # 安い (i-adjective) -> 安ければ
        self.check(matcher, "静かならば、勉強できる。", None) # 静かだ (na-adjective/copula) -> 静かならば (also nara+ba)
        self.check(matcher, "好きならば、やればいい。", "やれ ば") # 好きだ (na-adjective/copula) -> 好きならば

        # Nouns + Copula + ば (should NOT be matched)
        self.check(matcher, "学生ならば、割引がある。", None) # 学生だ (noun+copula) -> 学生ならば
        self.check(matcher, "雨ならば、中止だ。", None) # 雨だ (noun+copula) -> 雨ならば

        # Adverbs/Other words ending in 'ば' or 'えば'
        self.check(matcher, "ならば、仕方ない。", None) # ならば - conjunction
        self.check(matcher, "いざという時。", None) #いざ - interjection/adverb
        self.check(matcher, "昔話。", None) # 話 - noun (not はなしば)
        self.check(matcher, "例えば。", None) # 例えば - adverb
        self.check(matcher, "並べば、買える。", "並べ ば") # 並べば is a verb, but check '並べ' itself isn't picked up wrongly as a stem.

        # Compound verbs, ensuring the correct base verb is matched
        self.check(matcher, "立ち上がれば、見える。", "立ち上がれ ば") # 立ち上がる -> 立ち上がれば
        self.check(matcher, "話し合えば、解決する。", "話し合え ば") # 話し合う -> 話し合えば

    def test_one(self):
        noun = compile_matcher("""
            {noun}
        """)
        to = compile_matcher("""
            {to}
        """)
        matcher = compile_matcher("""
            {noun}{to}{noun}|
            {to}{noun}⌉|
            {noun}{to}|
            {to}は{noun}
        """)

        self.check(noun, "友達 {と} 図書 館 に 行き ます。", "友達")
        self.check(noun, "図書 館 に 行き ます。", "図書館")
        self.check(to, "友達 {と} 図書 館 に 行き ます。", "と")
        self.check(matcher, "友達 {と} 図書 館 に 行き ます。", "友達 と 図書 館")
        self.check(matcher, "同級 生 {と} サッカー を やっ た。", "同級 生 と サッカー")
        self.check(matcher, "彼 {と} 一緒 に 日本 語 を 勉強 し ましょう。", "彼 と 一緒")
        
    def test_どう(self):
        matcher = compile_matcher("""
            ⌈ˢどうᵖadvᵇどうʳドー⌉{noun}?
            (?!.*{verb-te})
            (
                ⌈ˢ~ᵖauxv~ʳデス⌉|
                ⌈ˢだᵖauxv:auxv-da:terminalᵇだʳダ⌉|
                ⌈~ᵖv~(ʳ|ᵇ)~⌉て?|
                か？|
                ⌈ˢよᵖprt:sentence_final_particleᵇよʳヨ⌉⌈ˢ？ᵖauxs:periodᵇ？⌉|
                ？
            )
        """)


        self.check(matcher, "{どう} し て も、この 問題 が 解決 でき ない。", None)
        self.check(matcher, "{どう} だい？", "どう だ")
        self.check(matcher, "この 魚 は {どう} やっ て 料理 し ます か？", None)
        self.check(matcher, "図書 館 へ は {どう} 行け ばいい です か？", "どう 行け")
        self.check(matcher, "どうして遅れたの", None)
        self.check(matcher, "どう やっ て} 駅 へ 行き ます か？", None)
        self.check(matcher, "試験、{どう} よ？", "どう よ？")
        
    # def test_にする(self):
    #     matcher = compile_matcher("""
    #         {ni}{noun}?{suru}|({mo}|{ni}){shinai}
    #     """)

    #     self.check(matcher, "この 書類 を PDF {に し たら}、読み やすく なる", "に し たら")
    #     self.check(matcher, "この 書類 を PDF {に すれ ば}、読み やすく なる", "に すれ ば")
    #     self.check(matcher, "# 私 は アイス コーヒー {に 決まっ てい ます}", None)
    #     self.check(matcher, "私 は アイス コーヒー に する {こと に し ます}。", "に する")
    #     self.check(matcher, "これ を きれい に {する} の は 私 の 仕事 だ", "に する")
        

    # def test_XはYの一つだ(self):
    #     matcher = compile_matcher("""
    #         {noun}の{noun}⌈ˢつᵖsuff:noun_likeʳツ⌉{desu}
    #     """)

    #     self.check(matcher, "富士 山 は 日本 の 最も 高い 山 の {一 つ です}。", "山 の 一 つ です")

    def check(self, matcher, input, expected):
        if expected:
            expected = expected.replace(' ', '')
        result = matcher.match_japanese(input)
        if result:
            result = result.replace(' ', '')
        if not result and not expected: return
        if result != expected:
            compact = input.replace('{','').replace('}', '')
            compact = japanese_to_compact_sentence(compact)
            print(f"JAPANESE: {input}")
            print(f"COMPACT:  {compact}")

        self.assertEqual(result, expected)


    

if __name__ == '__main__':
    unittest.main()