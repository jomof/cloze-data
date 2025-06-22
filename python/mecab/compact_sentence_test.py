import unittest
from python.mecab.compact_sentence import (
    compact_sentence_to_japanese,
    japanese_to_japanese_with_spaces,
    japanese_to_compact_sentence
)

class TestTokenParser(unittest.TestCase):
        
    def test_compact_sentence_to_japanese(self):
        compact = japanese_to_compact_sentence("あいう")
        self.assertEqual(compact_sentence_to_japanese(compact), "あいう")
        self.assertEqual(compact_sentence_to_japanese(compact, spaces=True), "あ いう")
    
    def test_compact_sentence_to_japanese_real_case(self):
        compact_sentence_to_japanese("⌈ˢ窓ᵖnʳマド⌉が⌈ˢ開いᵖvᵇ開くʳヒラク⌉て⌈ˢいᵖvᵇいるʳイル⌉⌈ˢますᵖauxvʳマス⌉。")

    def test_normalize_spaces(self):
        def check(japanese, expected):
            spaced = japanese_to_japanese_with_spaces(japanese)
            self.assertEqual(spaced, expected)
            spaced2 = japanese_to_japanese_with_spaces(japanese)
            self.assertEqual(spaced2, expected)
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
