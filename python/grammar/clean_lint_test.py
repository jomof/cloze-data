import unittest

from python.grammar.clean_lint import (
    strip_matching_quotes,
    lv_quotes,
    lv_english_brackets,
    lv_japanese_braces,
    lv_missing_competing_grammar,
    lv_example_count,
    lv_japanese_count,
    lv_better_grammar_name,
    lv_validate_parenthetical_meaning,
    lv_learn_before,
    lv_learn_after,
    lv_false_friends_grammar_point,
    lint_schema_enums_with_jsonschema,
    clean_lint,
    reorder_keys
)

from python.utils.visit_json.visit_json import visit_json
from python.grammar.grammar_schema import GRAMMAR_SCHEMA

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

    def test_lv_quotes_detects_quotes(self):
        grammar_point = {
            "examples": [
                {"english": 'This has "quotes" inside.'},
                {"english": 'No quotes here.'},
            ]
        }
        warnings = []
        def fn(value, type_name, path):
            lv_quotes(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)
        self.assertEqual(len(warnings), 1)
        self.assertIn('examples[0].english has quotes', warnings[0])

    def test_lv_english_brackets_detects_brackets(self):
        grammar_point = {
            "examples": [
                {"english": 'This has (parentheses) inside.'},
                {"english": 'This has [brackets] inside.'},
                {"english": 'This has {curly} inside.'},
                {"english": 'This has <angle> inside.'},
                {"english": 'No brackets here.'},
            ]
        }
        warnings = []
        def fn(value, type_name, path):
            lv_english_brackets(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        # Four examples should trigger warnings
        self.assertEqual(len(warnings), 4)
        self.assertIn('examples[0].english has bracket characters ()', warnings[0])
        self.assertIn('examples[1].english has bracket characters []', warnings[1])
        self.assertIn('examples[2].english has bracket characters {}', warnings[2])
        self.assertIn('examples[3].english has bracket characters <>', warnings[3])

    def test_lv_english_brackets_detects_brackets(self):
        grammar_point = {
            "examples": [
                {"japanese": ['沈黙 は 金 {だ}。']},
                {"japanese": ['沈黙 は 金 だ。']},
            ]
        }
        warnings = []
        def fn(value, type_name, path):
            lv_japanese_braces(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertEqual(len(warnings), 1)
        self.assertIn("[rule-5] warning examples[1].japanese[0] missing {bold} grammar point: 沈黙 は 金 だ。", warnings[0])

    def test_lv_missing_competing_grammar(self):
        grammar_point = {
            "examples": [
                {"english": "here I am"},
            ]
        }
        warnings = []
        def fn(value, type_name, path):
            lv_missing_competing_grammar(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertEqual(len(warnings), 1)
        self.assertIn("[rule-4] warning examples[0] has no competing_grammar", warnings[0])

    def test_lv_example_count(self):
        grammar_point = {
            "examples": [
                {},
            ]
        }
        warnings = []
        def fn(value, type_name, path):
            lv_japanese_count(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertEqual(len(warnings), 1)
        self.assertIn("[rule-7] warning examples[0] only has 0 element(s); should should be every way of saying 'english' that adheres to the grammar point", warnings[0])

    def test_lv_example_count(self):
        grammar_point = {
            "examples": [
                {"english": "here I am"},
            ]
        }
        warnings = []
        def fn(value, type_name, path):
            lv_example_count(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        # Four examples should trigger warnings
        self.assertEqual(len(warnings), 1)
        self.assertIn("[rule-6] at examples there are only 1 example(s); should have at least 10", warnings[0])

    def test_lv_better_grammar_name(self):
        grammar_point = {
            "better_grammar_point_name": ["Better Name"],
            "grammar_point": "Original Name",
            "id": "gp0001"
        }
        warnings = []
        def fn(value, type_name, path):
            lv_better_grammar_name(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], "[rule-8] warning grammar_point 'Original Name' lacks a valid “(meaning)” section; better_grammar_point_name should include a name with parentheses starting with a lowercase English letter or ~")

    def test_lv_validate_parenthetical_meaning(self):
        grammar_point = {
            "better_grammar_point_name": [
                "test grammar point",
                "test grammar point (valid meaning)",
                "test grammar point (~valid meaning)",
                "test grammar point (valid meaning よ)",                
                "test grammar point (無効 invalid meaning)",
                "test grammar point (I think this is a valid meaning)",
                "test grammar point (Invalid Meaning)",
                ]                
        }
        warnings = []
        def fn(value, type_name, path):
            lv_validate_parenthetical_meaning(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertIn("[rule-8] warning better_grammar_point_name[0] 'test grammar point' lacks a '(meaning)' section", warnings)
        self.assertIn("[rule-9] warning better_grammar_point_name[4] (meaning) starts with invalid char: 無", warnings)
        self.assertIn("[rule-9] warning better_grammar_point_name[6] (meaning) starts with invalid char: I", warnings)
        self.assertEqual(len(warnings), 3)

    def test_lv_dont_complain_if_two_better_grammar_point_name(self):
        grammar_point = {
            "grammar_point": "test grammar point (meaning)",
            "better_grammar_point_name": [
                "test grammar point (different meaning)",
                "test grammar point (meaning)",
                ]                
        }
        warnings = []
        def fn(value, type_name, path):
            lv_better_grammar_name(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertEqual(len(warnings), 0)

    def test_lv_better_grammar_point_name_should_be_different(self):
        grammar_point = {
            "grammar_point": "test grammar point (meaning)",
            "better_grammar_point_name": [
                "test grammar point (meaning)",
            ]                
        }
        warnings = []
        def fn(value, type_name, path):
            print(f"Validating {type_name} {path} : {value}")
            lv_better_grammar_name(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertIn("[rule-14] warning better_grammar_point_name[0] should not be the same as grammar_point: test grammar point (meaning)", warnings)
        self.assertEqual(len(warnings), 1)

    def test_lv_learn_before(self):
        grammar_point = {
            "grammar_point": "test grammar point (meaning)"            
        }
        warnings = []
        def fn(value, type_name, path):
            lv_learn_before(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertIn("[rule-10] warning learn_before has 0 item(s); must have at least 2", warnings)
        self.assertEqual(len(warnings), 1)

    def test_lv_learn_after(self):
        grammar_point = {
            "grammar_point": "test grammar point (meaning)"            
        }
        warnings = []
        def fn(value, type_name, path):
            lv_learn_after(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertIn("[rule-11] warning learn_after has 0 item(s); must have at least 2", warnings)
        self.assertEqual(len(warnings), 1)
      
    def test_lv_false_friends_grammar_point(self):
        grammar_point = {
            "grammar_point": "test grammar point (meaning)",
            "false_friends": [
                {
                    "term": "ね",
                }
            ],           
        }
        warnings = []
        def fn(value, type_name, path):

            lv_false_friends_grammar_point(value, type_name, path, warnings)
        visit_json(grammar_point, GRAMMAR_SCHEMA, fn)

        self.assertIn("[rule-12] warning false_friends[0].grammar_point is missing or empty", warnings)
        self.assertEqual(len(warnings), 1)
      
    
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
