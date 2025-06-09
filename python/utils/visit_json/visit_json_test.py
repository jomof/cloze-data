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

        # Calls should be (with fixed visit_json that continues alias chains):
        # 1. root → ({"foo": "HELLO"}, None, "")
        # 2. general ("english") → ("hello", "english", "foo")
        # 3. specific ("exampleEnglish") → ("HELLO", "exampleEnglish", "foo")  # Now continues with modified value
        self.assertEqual(calls, [
            ({"foo": "HELLO"}, None, ""),
            ("hello", "english", "foo"),
            ("HELLO", "exampleEnglish", "foo")  # Now continues with modified value
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

        # The call sequence should be (with fixed visit_json that continues alias chains):
        # 1. root → ({"field": "MIDREPL"}, None, "")
        # 2. general ("base") → ("data", "base", "field")
        # 3. mid ("mid") → ("data", "mid", "field")
        # 4. top ("top") → ("MIDREPL", "top", "field")  # Now continues with modified value
        self.assertEqual(calls, [
            ({"field": "MIDREPL"}, None, ""),
            ("data", "base", "field"),
            ("data", "mid", "field"),
            ("MIDREPL", "top", "field")  # Now continues with modified value
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

        # Expected call sequence (with fixed visit_json that continues alias chains):
        # 1. root → ({"arr":[10,20,30]}, None, "")
        # 2. container "arr" → ([10,20,30], "arr/array", "arr")
        # 3. each element gets both "Num" and "MyNum" calls: 
        #    (1,"Num","arr[0]"), (10,"MyNum","arr[0]"), (2,"Num","arr[1]"), (20,"MyNum","arr[1]"), etc.
        expected_calls = [
            ({"arr": [10, 20, 30]}, None, ""),
            ([10, 20, 30], "arr/array", "arr"),
            (1, "Num", "arr[0]"),
            (10, "MyNum", "arr[0]"),  # Now continues with modified value
            (2, "Num", "arr[1]"),
            (20, "MyNum", "arr[1]"),  # Now continues with modified value
            (3, "Num", "arr[2]"),
            (30, "MyNum", "arr[2]")   # Now continues with modified value
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


    def test_grammar_type_and_well_formed_grammar_type(self):
        # Test the grammar schema pattern: grammarType -> string, wellFormedGrammarType -> $ref grammarType
        schema = {
            "definitions": {
                "grammarType": {"type": "string"},
                "wellFormedGrammarType": {"$ref": "#/definitions/grammarType"}
            },
            "type": "object",
            "properties": {
                "direct_grammar": {"$ref": "#/definitions/grammarType"},
                "false_friends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "grammar_point": {"$ref": "#/definitions/wellFormedGrammarType"}
                        }
                    }
                }
            }
        }
        obj = {
            "direct_grammar": "だ (casual copula)",
            "false_friends": [
                {"grammar_point": "です (polite copula)"},
                {"grammar_point": "ときたら (when it comes to)"}
            ]
        }

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            # Test renaming logic like split-join-rename
            if type_name == 'grammarType' and value == "ときたら (when it comes to)":
                return "ときたら・と来たら (when it comes to)"
            return None

        result = visit_json(obj, schema, fn)
        
        # Verify the rename worked
        self.assertEqual(result["false_friends"][1]["grammar_point"], "ときたら・と来たら (when it comes to)")
        
        # Verify the function gets called with grammarType for all grammar fields
        grammar_type_calls = [call for call in calls if call[1] == 'grammarType']
        
        # Should have grammarType calls for all grammar references
        self.assertTrue(any(call[2] == 'direct_grammar' for call in grammar_type_calls))
        self.assertTrue(any(call[2] == 'false_friends[0].grammar_point' for call in grammar_type_calls))
        self.assertTrue(any(call[2] == 'false_friends[1].grammar_point' for call in grammar_type_calls))
        
        # The rename should have worked - verify the value was actually changed
        self.assertEqual(result["direct_grammar"], "だ (casual copula)")  # unchanged
        self.assertEqual(result["false_friends"][0]["grammar_point"], "です (polite copula)")  # unchanged
        # This should be the renamed value

    def test_root_modification_with_continued_processing(self):
        """Test that when root object is modified and returned, visit_json continues processing nested fields"""
        schema = {
            "definitions": {
                "grammarType": {"type": "string"},
                "wellFormedGrammarType": {"$ref": "#/definitions/grammarType"}
            },
            "type": "object",
            "properties": {
                "grammar_point": {"$ref": "#/definitions/grammarType"},
                "learn_before": {
                    "type": "array", 
                    "items": {"$ref": "#/definitions/grammarType"}
                },
                "false_friends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "grammar_point": {"$ref": "#/definitions/wellFormedGrammarType"}
                        }
                    }
                }
            }
        }
        obj = {
            "grammar_point": "に限って (ironic exception or disbelief)",
            "learn_before": ["だけ (only・just)", "ときたら (when it comes to)"],
            "false_friends": [
                {"grammar_point": "だけ (only・just)"},
                {"grammar_point": "ときたら (when it comes to)"}
            ]
        }

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            
            if type_name == None:  # Root object processing
                # Modify learn_before array in-place (like split-join-rename does)
                learn = value.get('learn_before', [])
                result = []
                for grammar_point in learn:
                    if grammar_point == "ときたら (when it comes to)":
                        result.append("ときたら・と来たら (when it comes to)")
                    else:
                        result.append(grammar_point)
                value['learn_before'] = result
                return value  # Return the modified object
            
            if type_name == 'grammarType':
                # This should also rename individual grammarType fields
                if value == "ときたら (when it comes to)":
                    return "ときたら・と来たら (when it comes to)"
            
            return None

        result = visit_json(obj, schema, fn)
        
        # Verify that learn_before was processed correctly (this should work)
        self.assertEqual(result["learn_before"], ["だけ (only・just)", "ときたら・と来たら (when it comes to)"])
        
        # Debug: Print all calls to see what happened
        print(f"All function calls: {calls}")
        
        # Verify that the function was called for individual grammarType fields
        grammar_type_calls = [call for call in calls if call[1] == 'grammarType']
        print(f"GrammarType calls: {grammar_type_calls}")
        
        # Print the actual result to see what happened
        print(f"Result: {result}")
        
        # Verify that learn_before was processed correctly (this should work)
        self.assertEqual(result["learn_before"], ["だけ (only・just)", "ときたら・と来たら (when it comes to)"])
        
        # Should have grammarType calls for individual fields even after root object modification
        individual_field_calls = [call for call in grammar_type_calls if 'false_friends' in call[2]]
        
        # This should now work - the bug is fixed!
        # The false_friends[1].grammar_point should be renamed to "ときたら・と来たら (when it comes to)"
        # because visit_json now continues processing after root returns a modification
        self.assertEqual(result["false_friends"][1]["grammar_point"], "ときたら・と来たら (when it comes to)")
        
        # Verify that the function was called for individual grammarType fields
        self.assertTrue(len(individual_field_calls) > 0, 
                       f"Expected grammarType calls for false_friends fields, but got calls: {calls}")

    def test_continued_processing_after_any_modification(self):
        """Test that visit_json continues processing nested fields even when any call returns a modification"""
        schema = {
            "definitions": {
                "grammarType": {"type": "string"}
            },
            "type": "object",
            "properties": {
                "container": {
                    "type": "object",
                    "properties": {
                        "field1": {"$ref": "#/definitions/grammarType"},
                        "field2": {"$ref": "#/definitions/grammarType"},
                        "nested": {
                            "type": "object",
                            "properties": {
                                "field3": {"$ref": "#/definitions/grammarType"}
                            }
                        }
                    }
                }
            }
        }
        obj = {
            "container": {
                "field1": "value1",
                "field2": "value2", 
                "nested": {
                    "field3": "value3"
                }
            }
        }

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            
            # Modify field1 when encountered
            if type_name == 'grammarType' and path == 'container.field1':
                return "MODIFIED_VALUE1"
            
            # This should still be called even though field1 was modified
            if type_name == 'grammarType' and path == 'container.field2':
                return "MODIFIED_VALUE2"
                
            # This should also still be called 
            if type_name == 'grammarType' and path == 'container.nested.field3':
                return "MODIFIED_VALUE3"
            
            return None

        result = visit_json(obj, schema, fn)
        
        print(f"All function calls: {calls}")
        print(f"Result: {result}")
        
        # All fields should be modified regardless of return order
        self.assertEqual(result["container"]["field1"], "MODIFIED_VALUE1")
        self.assertEqual(result["container"]["field2"], "MODIFIED_VALUE2") 
        self.assertEqual(result["container"]["nested"]["field3"], "MODIFIED_VALUE3")
        
        # Verify all grammarType fields were processed
        grammar_type_calls = [call for call in calls if call[1] == 'grammarType']
        self.assertEqual(len(grammar_type_calls), 3)

    def test_root_vs_non_root_modification_behavior(self):
        """Test that demonstrates the difference in behavior between root and non-root modifications"""
        schema = {
            "definitions": {
                "grammarType": {"type": "string"}
            },
            "type": "object",
            "properties": {
                "field1": {"$ref": "#/definitions/grammarType"},
                "field2": {"$ref": "#/definitions/grammarType"}
            }
        }
        obj = {
            "field1": "value1",
            "field2": "value2"
        }

        # Test 1: Modify at root level
        calls1 = []
        def fn1(value, type_name, path):
            calls1.append((value, type_name, path))
            
            if type_name == None:  # Root modification
                # Modify field1 in-place
                value['field1'] = "MODIFIED_BY_ROOT"
                return value  # Return modified root
            
            if type_name == 'grammarType' and path == 'field2':
                return "MODIFIED_FIELD2"
            
            return None

        result1 = visit_json(obj.copy(), schema, fn1)
        print(f"Root modification calls: {calls1}")
        print(f"Root modification result: {result1}")
        
        # Test 2: Don't modify at root level
        calls2 = []
        def fn2(value, type_name, path):
            calls2.append((value, type_name, path))
            
            if type_name == None:  # Root - DON'T return anything
                pass  # Don't return, let processing continue
            
            if type_name == 'grammarType' and path == 'field1':
                return "MODIFIED_FIELD1"
                
            if type_name == 'grammarType' and path == 'field2':
                return "MODIFIED_FIELD2"
            
            return None

        result2 = visit_json(obj.copy(), schema, fn2)
        print(f"Non-root modification calls: {calls2}")
        print(f"Non-root modification result: {result2}")
        
        # The behavior should be the same, but currently isn't
        # Root modification stops processing: field2 won't be called
        # Non-root modification continues: both fields get called
        grammar_calls1 = [call for call in calls1 if call[1] == 'grammarType']
        grammar_calls2 = [call for call in calls2 if call[1] == 'grammarType']
        
        print(f"Grammar calls after root modification: {len(grammar_calls1)}")
        print(f"Grammar calls without root modification: {len(grammar_calls2)}")
        
        # The behavior should now be the same - both should process all grammar fields
        self.assertEqual(len(grammar_calls1), 2)  # Both grammar calls made after root return (fixed!)
        self.assertEqual(len(grammar_calls2), 2)  # Both grammar calls made

    def test_continued_processing_after_grammartype_modification(self):
        """Test that visit_json continues to wellFormedGrammarType even if grammarType returns a modification"""
        schema = {
            "definitions": {
                "grammarType": {"type": "string"},
                "wellFormedGrammarType": {"$ref": "#/definitions/grammarType"}
            },
            "type": "object",
            "properties": {
                "false_friends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "grammar_point": {"$ref": "#/definitions/wellFormedGrammarType"}
                        }
                    }
                }
            }
        }
        obj = {
            "false_friends": [
                {"grammar_point": "ときたら (when it comes to)"}
            ]
        }

        calls = []
        def fn(value, type_name, path):
            calls.append((value, type_name, path))
            
            # Modify when called with grammarType
            if type_name == 'grammarType' and value == "ときたら (when it comes to)":
                return "ときたら・と来たら (when it comes to)"
            
            # This should also be called even though grammarType returned a modification
            if type_name == 'wellFormedGrammarType':
                # Could do additional processing here
                pass
            
            return None

        result = visit_json(obj, schema, fn)
        
        print(f"All function calls: {calls}")
        print(f"Result: {result}")
        
        # Verify the modification worked
        self.assertEqual(result["false_friends"][0]["grammar_point"], "ときたら・と来たら (when it comes to)")
        
        # Verify both grammarType and wellFormedGrammarType were called
        grammar_type_calls = [call for call in calls if call[1] == 'grammarType']
        well_formed_calls = [call for call in calls if call[1] == 'wellFormedGrammarType']
        
        print(f"GrammarType calls: {grammar_type_calls}")
        print(f"WellFormedGrammarType calls: {well_formed_calls}")
        
        # Both should be called according to the alias chain
        self.assertEqual(len(grammar_type_calls), 1)
        # This might currently fail if visit_json stops after grammarType returns a value
        self.assertEqual(len(well_formed_calls), 1)


if __name__ == "__main__":
    unittest.main()
