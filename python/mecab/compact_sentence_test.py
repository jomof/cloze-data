import unittest
import json
from python.mecab.compact_sentence import (
    compact_sentence_to_tokens,
    parse_raw_mecab_output,
    tokens_to_compact_sentence,
    mecab_raw_to_compact_sentence,
    Token,
    tokens_to_japanese,
    compact_sentence_to_japanese,
    japanese_to_japanese_with_spaces,
    japanese_to_tokens,
    raw_tokens_to_compact_sentence
)
from python.mecab.tagger import get_mecab_tagger

class TestTokenParser(unittest.TestCase):

    def test_mecab_raw_to_compact_sentence(self):
        wakati = get_mecab_tagger()
        term = "机の上に本はあります。"
        raw = wakati.parse(term)
        compact_sentence = mecab_raw_to_compact_sentence(raw)

        # Expect particles and punctuation to remain unbracketed
        self.assertEqual(
            compact_sentence,
            "⌈ˢ机ᵖnʳツクエ⌉の⌈ˢ上ᵖnʳウエ⌉に⌈ˢ本ᵖnʳホン⌉は⌈ˢありᵖvᵇあるʳアル⌉⌈ˢますᵖauxvʳマス⌉。"
        )
        
    def test_mecab_compact_and_parse(self):
        # Generate a compact sentence from MeCab
        wakati = get_mecab_tagger()
        term = "机の上に本はあります。"
        raw = wakati.parse(term)
        compact_sentence = mecab_raw_to_compact_sentence(raw)

        # Parse tokens from the compact sentence
        tokens = compact_sentence_to_tokens(compact_sentence)
        self.assertTrue(len(tokens) >= 1)
        self.assertEqual(tokens[0].surface, "机")

        # Round-trip: reconstruct and compare
        reconstructed = tokens_to_compact_sentence(tokens)
        self.assertEqual(reconstructed, compact_sentence)

    def test_sentence_to_tokens(self):
        input_string = "⌈ˢThisᵖNOUNᵇthis⌉⌈ˢisᵖVERB⌉⌈ˢaᵖDET⌉⌈ˢtestᵖNOUN⌉"
        tokens = compact_sentence_to_tokens(input_string)
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens[0].surface, "This")
        self.assertEqual(tokens[0].pos, "NOUN")
        self.assertEqual(tokens[0].base_form, "this")
        self.assertEqual(tokens[1].surface, "is")
        self.assertEqual(tokens[1].pos, "VERB")
        self.assertEqual(tokens[1].base_form, "")
        self.assertEqual(tokens[2].surface, "a")
        self.assertEqual(tokens[2].pos, "DET")
        self.assertEqual(tokens[2].base_form, "")
        self.assertEqual(tokens[3].surface, "test")
        self.assertEqual(tokens[3].pos, "NOUN")
        self.assertEqual(tokens[3].base_form, "")

    def test_tokens_to_sentence(self):
        tokens = [
            Token(surface="This", pos="NOUN", base_form="this"),
            Token(surface="is", pos="VERB"),
            Token(surface="a", pos="DET"),
            Token(surface="test", pos="NOUN")
        ]
        reconstructed_string = tokens_to_compact_sentence(tokens)
        expected_string = "⌈ˢThisᵖNOUNᵇthis⌉⌈ˢisᵖVERB⌉⌈ˢaᵖDET⌉⌈ˢtestᵖNOUN⌉"
        self.assertEqual(reconstructed_string, expected_string)

    def test_tokens_to_japanese(self):
        tokens = [
            Token(surface="あ"), Token(surface="い"), Token(surface="う")
        ]
        self.assertEqual(tokens_to_japanese(tokens), "あいう")
        self.assertEqual(tokens_to_japanese(tokens, spaces=True), "あ い う")

    def test_compact_sentence_to_japanese(self):
        compact = "⌈ˢあᵖひらがな⌉い⌈ˢうᵖひらがな⌉"
        # 'あ' and 'う' are bracketed, 'い' is single
        self.assertEqual(compact_sentence_to_japanese(compact), "あいう")
        self.assertEqual(compact_sentence_to_japanese(compact, spaces=True), "あ い う")
    
    def test_compact_sentence_to_japanese_real_case(self):
        compact_sentence_to_japanese("⌈ˢ窓ᵖnʳマド⌉が⌈ˢ開いᵖvᵇ開くʳヒラク⌉て⌈ˢいᵖvᵇいるʳイル⌉⌈ˢますᵖauxvʳマス⌉。")


    def test_roundtrip_compact_to_japanese_and_back(self):
        original_japanese = "テストだよ。"
        # Simulate compacting via MeCab
        wakati = get_mecab_tagger()
        raw = wakati.parse(original_japanese)
        compact = mecab_raw_to_compact_sentence(raw)
        # Convert compact back to Japanese surface
        recovered = compact_sentence_to_japanese(compact)
        self.assertEqual(recovered, original_japanese)

        # Now tokenize surfaces and reconstruct compact
        tokens = compact_sentence_to_tokens(compact)
        reconstructed_compact = tokens_to_compact_sentence(tokens)
        self.assertEqual(reconstructed_compact, compact)


    def test_japanese_to_japanese_with_spaces_impl_1(self):
        japanese = "{これ}、京都 の お 土産 な ん だ よ。"
        wakati = get_mecab_tagger()
        raw = wakati.parse(japanese)
        raw_tokens = parse_raw_mecab_output(raw)
        print(f"RAW TOKENS: {json.dumps(raw_tokens, ensure_ascii=False, indent=2)}")
        compact_sentence = raw_tokens_to_compact_sentence(raw_tokens)
        print(f"COMPACT: {compact_sentence}")
        tokens = compact_sentence_to_tokens(compact_sentence)
        print(f"TOKENS: {json.dumps(tokens, ensure_ascii=False, indent=2, default=self.default)}")
        result = tokens_to_japanese(tokens, spaces=True)
        print(f"RESULT: {result}")
        self.assertEqual(result, "{これ}、京都 の お 土産 な ん だ よ。")

    def test_japanese_to_japanese_with_spaces_impl_2(self):
        japanese = "今日はいい{天気}ですね。"
        wakati = get_mecab_tagger()
        raw = wakati.parse(japanese)
        raw_tokens = parse_raw_mecab_output(raw)
        compact_sentence = raw_tokens_to_compact_sentence(raw_tokens)
        tokens = compact_sentence_to_tokens(compact_sentence)
        result = tokens_to_japanese(tokens, spaces=True)
        print(f"COMPACT: {compact_sentence}")
        print(f"TOKENS: {json.dumps(tokens, ensure_ascii=False, indent=2, default=self.default)}")
        print(f"RESULT: {result}")
        self.assertEqual(result, "今日 は いい {天気} です ね。")

    def test_japanese_to_japanese_with_spaces_impl_3(self):
        japanese = "{ですね。}"
        wakati = get_mecab_tagger()
        raw = wakati.parse(japanese)
        raw_tokens = parse_raw_mecab_output(raw)
        compact_sentence = raw_tokens_to_compact_sentence(raw_tokens)
        tokens = compact_sentence_to_tokens(compact_sentence)
        result = tokens_to_japanese(tokens, spaces=True)
        print(f"COMPACT: {compact_sentence}")
        print(f"TOKENS: {json.dumps(tokens, ensure_ascii=False, indent=2, default=self.default)}")
        print(f"RESULT: {result}")
        self.assertEqual(result, "{です ね。}")

    def test_japanese_to_japanese_with_spaces_impl_4(self):
        japanese = "A:この レポート は 正しい です か。B:ええ、確認 し た ところ、その {よう です} ね。"
        wakati = get_mecab_tagger()
        raw = wakati.parse(japanese)
        raw_tokens = parse_raw_mecab_output(raw)
        print(f"RAW TOKENS: {json.dumps(raw_tokens, ensure_ascii=False, indent=2)}")
        compact_sentence = raw_tokens_to_compact_sentence(raw_tokens)
        print(f"COMPACT: {compact_sentence}")
        tokens = compact_sentence_to_tokens(compact_sentence)
        print(f"TOKENS: {json.dumps(tokens, ensure_ascii=False, indent=2, default=self.default)}")
        result = tokens_to_japanese(tokens, spaces=True)
        print(f"RESULT: {result}")
        self.assertEqual(result, "A:この レポート は 正しい です か。B:ええ、確認 し た ところ、その {よう です} ね。")

    def test_japanese_to_japanese_with_spaces_impl_5(self):
        japanese = "彼女 は {寂し そう} で、{話しかけ} づらかった。"
        wakati = get_mecab_tagger()
        raw = wakati.parse(japanese)
        raw_tokens = parse_raw_mecab_output(raw)
        print(f"RAW TOKENS: {json.dumps(raw_tokens, ensure_ascii=False, indent=2)}")
        compact_sentence = raw_tokens_to_compact_sentence(raw_tokens)
        print(f"COMPACT: {compact_sentence}")
        tokens = compact_sentence_to_tokens(compact_sentence)
        print(f"TOKENS: {json.dumps(tokens, ensure_ascii=False, indent=2, default=self.default)}")
        result = tokens_to_japanese(tokens, spaces=True)
        print(f"RESULT: {result}")
        self.assertEqual(result, "彼女 は {寂し そう} で、{話しかけ} づらかっ た。")

    def test_japanese_to_japanese_with_spaces_impl_6(self):
        japanese = "彼女 は {寂し そう} で、{話しかけ} づらかった。"
        wakati = get_mecab_tagger()
        raw = wakati.parse(japanese)
        raw_tokens = parse_raw_mecab_output(raw)
        print(f"RAW TOKENS: {json.dumps(raw_tokens, ensure_ascii=False, indent=2)}")
        compact_sentence = raw_tokens_to_compact_sentence(raw_tokens)
        print(f"COMPACT: {compact_sentence}")
        tokens = compact_sentence_to_tokens(compact_sentence)
        print(f"TOKENS: {json.dumps(tokens, ensure_ascii=False, indent=2, default=self.default)}")
        result = tokens_to_japanese(tokens, spaces=True)
        print(f"RESULT: {result}")
        self.assertEqual(result, "彼女 は {寂し そう} で、{話しかけ} づらかっ た。")

    def test_normalize_spaces(self):
        def check(japanese, expected):
            spaced = japanese_to_japanese_with_spaces(japanese)
            self.assertEqual(spaced, expected)
            spaced2 = japanese_to_japanese_with_spaces(japanese)
            self.assertEqual(spaced2, expected)
        check("A:この レポート は 正しい です か。B:ええ、確認 し た ところ、その {よう です} ね。", "A:この レポート は 正しい です か。B:ええ、確認 し た ところ、その {よう です} ね。")
        check("{これ}、 京都 の お 土産 な ん だ よ。", "{これ}、京都 の お 土産 な ん だ よ。")
        check("今日はいい天気ですね。", "今日 は いい 天気 です ね。")
        check("今日はいい{天気}ですね。", "今日 は いい {天気} です ね。")
        check("{今日はいい天気ですね。}", "{今日 は いい 天気 です ね。}")
        check("私、ジョンです。", "私、ジョン です。")
        check("{。}","{。}")
        check("","")
        check("{}","{}")
        check("{","{")
        check("}","}")

    def test_japanese_to_japanese_with_spaces_roundtrip(self):
        # This sentence didn't round-trip through MeCab correctly because of space before っ
        # added by genai.
        japanese_to_japanese_with_spaces("入 っ て い ま す。")
        japanese_to_japanese_with_spaces("明日 {の} 天気、晴れっ て さ。")


    @staticmethod
    def default(obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        raise TypeError(f"{type(obj)} not serializable")


if __name__ == "__main__":
    unittest.main()
