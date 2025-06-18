import unittest
from python.grammar.matcher import compile_matcher

class TestMatcher(unittest.TestCase):

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
        

        

if __name__ == '__main__':
    unittest.main()