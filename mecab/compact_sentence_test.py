import unittest
from mecab.compact_sentence import sentence_to_tokens, tokens_to_sentence, Token

class TestTokenParser(unittest.TestCase):

    def test_sentence_to_tokens(self):
        input_string = "⌈ˢThisᵖNOUNᵇthis⌉⌈ˢisᵖVERB⌉⌈ˢaᵖDET⌉⌈ˢtestᵖNOUN⌉"
        tokens = sentence_to_tokens(input_string)
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
        reconstructed_string = tokens_to_sentence(tokens)
        expected_string = "⌈ˢThisᵖNOUNᵇthis⌉⌈ˢisᵖVERB⌉⌈ˢaᵖDET⌉⌈ˢtestᵖNOUN⌉"
        self.assertEqual(reconstructed_string, expected_string)

if __name__ == "__main__":
    unittest.main()
