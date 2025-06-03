import unittest

from python.grammar.clean_lint import (
    strip_matching_quotes,
    lint_quotes,
    lint_english_brackets,
    lint_schema_enums_with_jsonschema,
    clean_lint,
    reorder_keys
)

class TestLintSchemaUtils(unittest.TestCase):
    def test_strip_matching_quotes_english(self):
        # English quotes
        self.assertEqual(strip_matching_quotes('"hello"'), 'hello')
        self.assertEqual(strip_matching_quotes("'world'"), 'world')
        # Nested quotes
        self.assertEqual(strip_matching_quotes('""nested""'), 'nested')

    def test_strip_matching_quotes_japanese(self):
        # Japanese quotes
        self.assertEqual(strip_matching_quotes('「こんにちは」'), 'こんにちは')
        self.assertEqual(strip_matching_quotes('『テスト』'), 'テスト')

    def test_strip_matching_quotes_unmatched(self):
        # Mixed unmatched does nothing
        self.assertEqual(strip_matching_quotes('"hello'), '"hello')
        self.assertEqual(strip_matching_quotes('world"'), 'world"')
        # No quotes remains unchanged
        self.assertEqual(strip_matching_quotes('no quotes'), 'no quotes')

    def test_lint_quotes_detects_quotes(self):
        grammar_point = {
            "examples": [
                {"english": 'This has "quotes" inside.'},
                {"english": 'No quotes here.'},
            ]
        }
        warnings = lint_quotes(grammar_point)
        self.assertEqual(len(warnings), 1)
        self.assertIn('examples[0].english has quotes', warnings[0])

    def test_lint_english_brackets_detects_brackets(self):
        grammar_point = {
            "examples": [
                {"english": 'This has (parentheses) inside.'},
                {"english": 'This has [brackets] inside.'},
                {"english": 'This has {curly} inside.'},
                {"english": 'This has <angle> inside.'},
                {"english": 'No brackets here.'},
            ]
        }
        warnings = lint_english_brackets(grammar_point)
        # Four examples should trigger warnings
        self.assertEqual(len(warnings), 4)
        self.assertIn('examples[0].english has bracket characters ()', warnings[0])
        self.assertIn('examples[1].english has bracket characters []', warnings[1])
        self.assertIn('examples[2].english has bracket characters {}', warnings[2])
        self.assertIn('examples[3].english has bracket characters <>', warnings[3])

    def test_lint_schema_enums_valid(self):
        schema = {
            "type": "object",
            "properties": {
                "color": {"type": "string", "enum": ["red", "green", "blue"]}
            }
        }
        instance_valid = {"color": "green"}
        errors_valid = lint_schema_enums_with_jsonschema(instance_valid, schema)
        self.assertEqual(errors_valid, [])

    def test_lint_schema_enums_invalid(self):
        schema = {
            "type": "object",
            "properties": {
                "color": {"type": "string", "enum": ["red", "green", "blue"]}
            }
        }
        instance_invalid = {"color": "yellow"}
        errors_invalid = lint_schema_enums_with_jsonschema(instance_invalid, schema)
        self.assertEqual(len(errors_invalid), 1)
        self.assertIn("color had an invalid enum value", errors_invalid[0])

    def test_clean_lint_migrates_japanese_string_to_array(self):
        grammar_point = {
            "examples": [
                {"english": 'Hello', "japanese": '単語'}  # string input should be converted
            ],
        }
        cleaned = clean_lint(grammar_point)
        example = cleaned['examples'][0]
        self.assertIsInstance(example['japanese'], list)
        self.assertEqual(example['japanese'], ['単語'])

    def test_clean_lint_array_input_preserves_array(self):
        grammar_point = {
            "examples": [
                {"english": 'Hello', "japanese": ['テスト例']}  # already array
            ],
        }
        cleaned = clean_lint(grammar_point)
        example = cleaned['examples'][0]
        self.assertIsInstance(example['japanese'], list)
        self.assertEqual(example['japanese'], ['テスト 例'])

    def test_clean_lint_strips_english_quotes(self):
        grammar_point = {
            "examples": [
                {"english": '"Quoted"', "japanese": ['テスト  例']}  # array with no space issue handled separately
            ],
        }
        cleaned = clean_lint(grammar_point)
        example = cleaned['examples'][0]
        self.assertEqual(example['english'], 'Quoted')

    def test_clean_lint_bracket_warning(self):
        grammar_point = {
            "examples": [
                {"english": '(Bracketed)', "japanese": ['テスト  例']}
            ],
        }
        cleaned = clean_lint(grammar_point)
        errors = cleaned['lint-errors']
        self.assertTrue(any('has bracket characters' in e for e in errors))

    def test_clean_lint_prunes_empty_fields(self):
        grammar_point = {
            "title": "",  # should be pruned
            "metadata": {},  # should be pruned
            "tags": [],  # should be pruned
            "notes": None,  # should be pruned
            "extra": "null",  # should be pruned
            "examples": [
                {
                    "english": "Test",  # kept
                    "japanese": ['テスト'],  # kept
                    "comment": "",  # pruned
                }
            ]
        }
        cleaned = clean_lint(grammar_point)
        self.assertNotIn('title', cleaned)
        self.assertNotIn('metadata', cleaned)
        self.assertNotIn('tags', cleaned)
        self.assertNotIn('notes', cleaned)
        self.assertNotIn('extra', cleaned)
        example = cleaned['examples'][0]
        self.assertNotIn('comment', example)

    def test_reorder_keys_simple(self):
        obj = {'b': 1, 'a': 2, 'c': 3}
        # Using plain dict: insertion order a -> b -> c in literal
        schema = {'properties': {'a': {}, 'b': {}, 'c': {}}}
        ordered = reorder_keys(obj, schema)
        self.assertEqual(list(ordered.keys()), ['a', 'b', 'c'])

    def test_reorder_keys_with_extra_fields(self):
        obj = {'x': 0, 'b': 1, 'a': 2, 'c': 3, 'y': 4}
        schema = {'properties': {'a': {}, 'b': {}, 'c': {}}}
        ordered = reorder_keys(obj, schema)
        # Keys a, b, c first in schema order, then extras in original order: x, y
        self.assertEqual(list(ordered.keys()), ['a', 'b', 'c', 'x', 'y'])

    def test_clean_lint_array_input_preserves_array(self):
        grammar_point = {
            "grammar_point": "テスト",
            "id": "gp0000",
            "pronunciation": {"katakana": "テスト", "romaji": "tesuto"},
            "formation": {"X は Y": "test"},
            "jlpt": "N5",
            "meaning": "test",
            "details": {},
            "etymology": "test origin",
            "writeup": "test writeup",
            "examples": [
                {
                    "english": 'Hello',
                    "japanese": ['テスト例'],
                    "scene": "scene", "register": "casual", "setting": "informative"
                }
            ],
            "false_friends": [],
            "post_false_friends_writeup": "",
        }
        cleaned = clean_lint(grammar_point)
        example = cleaned['examples'][0]
        self.assertIsInstance(example['japanese'], list)
        self.assertEqual(example['japanese'], ['テスト 例'])

if __name__ == '__main__':
    unittest.main()
