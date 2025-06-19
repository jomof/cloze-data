import unittest
from python.grammar.matcher import compile_matcher
from python.mecab.compact_sentence import japanese_to_compact_sentence

class TestMatcher(unittest.TestCase):

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

        
        self.check(matcher, "いつ まで も {寂し がっ て ばかり は い られ ない}。何 か する こと を 見つけ ない と。", "がっ て")

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

        # 4. ぐ -> いで (イ音便 - ionbin, voiced)
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
        self.check(matcher, "寒くて、震えていた。", "震え て") # 寒くて (samukute) - い-adjective te-form (should NOT be matched if you only want VERBS)
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
        self.check(matcher, "本を売れ。", "売れ")
        self.check(matcher, "早く帰れ！", "帰れ")
        self.check(matcher, "部屋に入れ。", "入れ")
        self.check(matcher, "紙を切れ。", "切れ")
        self.check(matcher, "それを取れ。", "取れ")

        # 4. く ending -> け
        self.check(matcher, "漢字を書け。", "書け")
        self.check(matcher, "歩け！", "歩け")
        self.check(matcher, "よく聞け。", "聞け")
        self.check(matcher, "窓を開け。", "開け")

        # 5. ぐ ending -> げ
        self.check(matcher, "防げ！", "防げ")
        self.check(matcher, "急げ！", "急げ")
        self.check(matcher, "服を脱げ。", "脱げ")

        # 6. す ending -> せ
        self.check(matcher, "友達と話せ。", "話せ")
        self.check(matcher, "もっと出せ！", "出せ")
        self.check(matcher, "宿題を見せ。", "見せ")

        # 7. ぬ ending -> ね
        self.check(matcher, "死ね！", "死ね")  # Strong imperative

        # 8. ぶ ending -> べ
        self.check(matcher, "友達を呼べ。", "呼べ")
        self.check(matcher, "もっと学べ。", "学べ")

        # 9. む ending -> め
        self.check(matcher, "本を読め。", "読め")
        self.check(matcher, "痛みを止め。", "止め")
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
        self.check(matcher, "食べなさい。", "食べ")  # Polite imperative
        self.check(matcher, "勉強しなさい。", None)  # Polite imperative

        # Negative imperatives (should NOT match as they're different grammar)
        self.check(matcher, "行くな！", None)  # Negative imperative
        self.check(matcher, "するな。", None)  # Negative imperative
        self.check(matcher, "食べるな。", None)  # Negative imperative

        # Request forms (should NOT match)
        self.check(matcher, "座ってください。", None)  # Polite request
        self.check(matcher, "食べてくれ。", "食べ")   # Casual request
        self.check(matcher, "来てくれる？", None)   # Question request

        # --- False Positives (words ending in imperative-like sounds) ---

        # Nouns that end in imperative-like syllables
        self.check(matcher, "時計を見せてくれる？", "見せ")  # Here '見せ' should match
        self.check(matcher, "この瀬戸際で何をする？", None)  # 瀬戸際 (setogai) - noun
        self.check(matcher, "彼の姿勢がいい。", None)  # 姿勢 (shisei) - noun
        self.check(matcher, "会議の議題は何？", None)  # 議題 (gidai) - noun
        self.check(matcher, "新しい時代が来た。", None)  # 時代 (jidai) - noun

        # Adjectives ending in similar sounds
        self.check(matcher, "この部屋は広い。", None)  # い-adjective
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
        self.check(matcher, "彼が来れば良い。", "来れ")  # Conditional form
        self.check(matcher, "食べれる？", None)  # Potential form (colloquial)
        self.check(matcher, "見れない。", "見れ")  # Potential negative (colloquial)

        # --- Exploitation Tests (Critical edge cases) ---

        # I. Godan verbs with る ending (most commonly confused with ichidan)
        self.check(matcher, "家に帰れ！", "帰れ")
        self.check(matcher, "部屋に入れ。", "入れ")
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
        self.check(matcher, "食べれない。", "食べれ")  # Colloquial potential (not imperative)
        self.check(matcher, "来れる？", None)  # Colloquial potential (not imperative)
        self.check(matcher, "見れた。", "見れ")  # Colloquial potential past (not imperative)

    def test_verb_eba_forms(self):
        matcher = compile_matcher("{verb-eba}") # Assuming this compiles your pattern

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
        self.check(matcher, "いざという時。", None) # いざ - interjection/adverb
        self.check(matcher, "昔話。", None) # 話 - noun (not はなしば)
        self.check(matcher, "例えば。", None) # 例えば - adverb
        self.check(matcher, "並べば、買える。", "並べ ば") # 並べば is a verb, but check '並べ' itself isn't picked up wrongly as a stem.

        # Compound verbs, ensuring the correct base verb is matched
        self.check(matcher, "立ち上がれば、見える。", "立ち上がれ ば") # 立ち上がる -> 立ち上がれば
        self.check(matcher, "話し合えば、解決する。", "話し合え ば") # 話し合う -> 話し合えば

    def test_one(self):
        matcher = compile_matcher("""
            {noun}と{noun}|
            と{noun}⌉|
            {noun}と|
            とは{noun}
        """)


        result = matcher.match_japanese("友達 {と} 図書 館 に 行き ます。")
        self.assertEqual(result, "友達 と 図書 館")
        result = matcher.match_japanese("同級 生 {と} サッカー を やっ た。")
        self.assertEqual(result, "同級 生 と サッカー")
        result = matcher.match_japanese("彼 {と} 一緒 に 日本 語 を 勉強 し ましょう。")
        self.assertEqual(result, "彼 と 一緒")
        
    def test_どう(self):
        matcher = compile_matcher("""
            ⌈ˢどうᵖadvʳドウ⌉{noun}?
            (?!.*{verb-te})
            (
                ⌈ˢ~ᵖauxv~ʳデス⌉|
                ⌈~ᵖauxv~ʳダ⌉|
                ⌈~ᵖv~(ʳ|ᵇ)~⌉て?|
                か？|
                よ？|
                ？
            )
        """)


        self.check(matcher, "{どう} し て も、この 問題 が 解決 でき ない。", None)
        self.check(matcher, "{どう} だ い？", "どう だ")
        self.check(matcher, "この 魚 は {どう} やっ て 料理 し ます か？", None)
        self.check(matcher, "図書 館 へ は {どう} 行け ば いい です か？", "どう 行け")
        self.check(matcher, "どうして遅れたの", None)
        self.check(matcher, "どう やっ て} 駅 へ 行き ます か？", None)
        self.check(matcher, "試験、{どう} よ？", "どう よ？")
        
    def test_にする(self):
        matcher = compile_matcher("""
            {ni}{noun}?{suru}|({mo}|{ni}){shinai}
        """)

        self.check(matcher, "この 書類 を PDF {に し たら}、読み やすく なる", "に し たら")
        self.check(matcher, "この 書類 を PDF {に すれ ば}、読み やすく なる", "に すれ ば")
        self.check(matcher, "# 私 は アイス コーヒー {に 決まっ て い ます}", None)
        self.check(matcher, "私 は アイス コーヒー に する {こと に し ます}。", "に する")
        self.check(matcher, "これ を きれい に {する} の は 私 の 仕事 だ", "に する")
        

    def test_XはYの一つだ(self):
        matcher = compile_matcher("""
            {noun}の{noun}⌈ˢつᵖsuff:noun_likeʳツ⌉{desu}
        """)

        self.check(matcher, "富士 山 は 日本 の 最も 高い 山 の {一 つ です}。", "山 の 一 つ です")

    def check(self, matcher, input, expected):
        result = matcher.match_japanese(input)
        if result != expected:
            compact = input.replace('{','').replace('}', '')
            compact = japanese_to_compact_sentence(compact)
            print(f"JAPANESE: {input}")
            print(f"COMPACT:  {compact}")
        self.assertEqual(result, expected)


    

if __name__ == '__main__':
    unittest.main()