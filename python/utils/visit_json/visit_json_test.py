import unittest

from visit_json import visit_json  # adjust import path as needed


class TestVisitJsonInlineTypeNames(unittest.TestCase):
    def test_single_alias_chain_calls(self):
        # Schema with definitions "english" -> {type: string}, "exampleEnglish" -> $ref english
        schema = {
            "definitions": {
                "english": {"type": "string"},
                "exampleEnglish": {"$ref": "#/definitions/english"}
            },
            "type": "object",
            "properties": {
                "foo": {"$ref": "#/definitions/exampleEnglish"}
            }
        }
        obj = {"foo": "hello"}

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            return None

        result = visit_json(obj, schema, fn)
        self.assertEqual(result["foo"], "hello")

        # Expect three calls in order:
        # 1. root → ({"foo": "hello"}, None, "")
        # 2. general ("english") → ("hello", "english", "foo")
        # 3. alias  ("exampleEnglish") → ("hello", "exampleEnglish", "foo")
        self.assertEqual(calls, [
            ({"foo": "hello"}, None, ""),
            ("hello", "english", "foo"),
            ("hello", "exampleEnglish", "foo")
        ])

    def test_single_alias_chain_replacement_at_english(self):
        # Same schema as above
        schema = {
            "definitions": {
                "english": {"type": "string"},
                "exampleEnglish": {"$ref": "#/definitions/english"}
            },
            "type": "object",
            "properties": {
                "foo": {"$ref": "#/definitions/exampleEnglish"}
            }
        }
        obj = {"foo": "hello"}

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            # Replace at the "english" (general) level
            if type_name == "english":
                return "HELLO"
            return None

        result = visit_json(obj, schema, fn)
        self.assertEqual(result["foo"], "HELLO")

        # Calls should be:
        # 1. root → ({"foo": "HELLO"}, None, "")
        # 2. general ("english") → ("hello", "english", "foo")
        self.assertEqual(calls, [
            ({"foo": "HELLO"}, None, ""),
            ("hello", "english", "foo")
        ])

    def test_multi_level_alias_and_replacement_at_mid(self):
        # definitions: base -> {type:string}, mid -> $ref base, top -> $ref mid
        schema = {
            "definitions": {
                "base": {"type": "string"},
                "mid": {"$ref": "#/definitions/base"},
                "top": {"$ref": "#/definitions/mid"}
            },
            "type": "object",
            "properties": {
                "field": {"$ref": "#/definitions/top"}
            }
        }
        obj = {"field": "data"}

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            # Replace at "mid" level
            if type_name == "mid":
                return "MIDREPL"
            return None

        result = visit_json(obj, schema, fn)
        self.assertEqual(result["field"], "MIDREPL")

        # The call sequence should be:
        # 1. root → ({"field": "MIDREPL"}, None, "")
        # 2. general ("base") → ("data", "base", "field")
        # 3. mid ("mid") → ("data", "mid", "field")
        self.assertEqual(calls, [
            ({"field": "MIDREPL"}, None, ""),
            ("data", "base", "field"),
            ("data", "mid", "field")
        ])

    def test_array_of_aliases(self):
        # definitions: "Num" -> {type: number}, "MyNum" -> $ref Num
        schema = {
            "definitions": {
                "Num": {"type": "number"},
                "MyNum": {"$ref": "#/definitions/Num"}
            },
            "type": "object",
            "properties": {
                "arr": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/MyNum"}
                }
            }
        }
        obj = {"arr": [1, 2, 3]}

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            if type_name == "Num" and isinstance(value, (int, float)):
                return value * 10
            return None

        result = visit_json(obj, schema, fn)
        self.assertEqual(result["arr"], [10, 20, 30])

        # Expected call sequence:
        # 1. root → ({"arr":[10,20,30]}, None, "")
        # 2. container "arr" → ([10,20,30], "arr/array", "arr")
        # 3. each element: (1,"Num","arr[0]"), (2,"Num","arr[1]"), (3,"Num","arr[2]")
        expected_calls = [
            ({"arr": [10, 20, 30]}, None, ""),
            ([10, 20, 30], "arr/array", "arr"),
            (1, "Num", "arr[0]"),
            (2, "Num", "arr[1]"),
            (3, "Num", "arr[2]")
        ]
        self.assertEqual(calls, expected_calls)

    def test_no_alias_inline_types(self):
        # Schema without any $ref: property "bar" is inline {"type":"string"}
        schema = {
            "type": "object",
            "properties": {
                "bar": {"type": "string"}
            }
        }
        obj = {"bar": "world"}

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            return None

        result = visit_json(obj, schema, fn)
        self.assertEqual(result, {"bar": "world"})

        # Calls:
        # 1. root → ({"bar":"world"}, None, "")
        # 2. inline prop "bar" (string) → ("world", "bar/string", "bar")
        self.assertEqual(calls, [
            ({"bar": "world"}, None, ""),
            ("world", "bar/string", "bar")
        ])

    def test_mixed_types_and_replacement_by_path(self):
        # Schema with definitions "Person" and "Address", nested objects
        schema = {
            "definitions": {
                "Person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "number"},
                        "address": {"$ref": "#/definitions/Address"}
                    }
                },
                "Address": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "zip": {"type": "string"}
                    }
                }
            },
            "type": "object",
            "properties": {
                "person": {"$ref": "#/definitions/Person"}
            }
        }
        obj = {
            "person": {
                "name": "Alice",
                "age": 30,
                "address": {
                    "city": "Seattle",
                    "zip": "98101"
                }
            }
        }

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            # Replace based on path
            if path == "person.age" and isinstance(value, (int, float)):
                return value + 1
            if path == "person.address.city" and isinstance(value, str):
                return value + " City"
            return None

        result = visit_json(obj, schema, fn)
        self.assertEqual(result["person"]["age"], 31)
        self.assertEqual(result["person"]["address"]["city"], "Seattle City")
        self.assertEqual(result["person"]["name"], "Alice")
        self.assertEqual(result["person"]["address"]["zip"], "98101")

        # Verify that expected visit calls occurred (in any order):
        expected_entries = [
            ({"person": obj["person"]}, None, ""),
            (obj["person"], "Person", "person"),
            ("Alice", "name/string", "person.name"),
            (30, "age/number", "person.age"),
            (obj["person"]["address"], "Address", "person.address"),
            ("Seattle", "city/string", "person.address.city"),
            ("98101", "zip/string", "person.address.zip")
        ]
        for expected in expected_entries:
            self.assertIn(expected, calls)


if __name__ == "__main__":
    unittest.main()
