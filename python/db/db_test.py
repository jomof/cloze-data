import os
import sqlite3
import unittest
from python.db.db import Database

class TestDatabase(unittest.TestCase):
    """Simple tests for core database functionality using actual Database class"""
    
    def setUp(self):
        """Create a test database instance"""
        print("Setting up test database...")
        self.test_db_path = 'test.db'
        self.db = Database(db_path=self.test_db_path)

    def tearDown(self):
        """Clean up test database file"""
        print("Tearing down test database...")
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    
    def test_database_schema_creation(self):
        """Test that database schema is created correctly"""
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Verify table exists
        conn = sqlite3.connect(self.test_db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='english_to_japanese'"
            )
            self.assertIsNotNone(cursor.fetchone())
        finally:
            conn.close()
    
    def test_add_single_translation(self):
        """Test adding a single translation"""
        self.db.add_single_translation("hello", "こんにちは")
        self.assertTrue(self.db.has_translation("hello", "こんにちは"))
    
    def test_add_multiple_translations(self):
        """Test adding multiple translations for one English term"""
        translations = ["こんにちは", "こんばんは", "おはよう"]
        result = self.db.add_japanese_translations("hello", translations)
        self.assertEqual(result, 3)
        
        retrieved = self.db.get_japanese_translations("hello")
        self.assertEqual(retrieved, set(translations))
        self.assertEqual(self.db.get_translation_count("hello"), 3)
    
    def test_duplicate_handling(self):
        """Test that duplicates are handled correctly"""
        # Add same translation twice
        self.db.add_single_translation("test", "テスト")
        self.db.add_single_translation("test", "テスト")
        
        # Should only have one entry
        self.assertEqual(self.db.get_translation_count("test"), 1)
    
    def test_unicode_support(self):
        """Test Unicode character support"""
        test_cases = [
            ("emoji", "😀"),
            ("kanji", "漢字"),
            ("katakana", "カタカナ"),
            ("hiragana", "ひらがな"),
            ("mixed", "Hello世界123")
        ]
        
        for english, japanese in test_cases:
            self.db.add_single_translation(english, japanese)
            self.assertTrue(self.db.has_translation(english, japanese))
    
    def test_special_characters(self):
        """Test handling of special characters"""
        special_english = "test'with\"quotes"
        special_japanese = "テスト'引用符\"付き"
        
        self.db.add_single_translation(special_english, special_japanese)
        self.assertTrue(self.db.has_translation(special_english, special_japanese))
    
    def test_empty_result_handling(self):
        """Test handling of queries for non-existent data"""
        result = self.db.get_japanese_translations("nonexistent")
        self.assertEqual(result, set())
        
        count = self.db.get_translation_count("nonexistent")
        self.assertEqual(count, 0)
        
        exists = self.db.has_translation("nonexistent", "anything")
        self.assertFalse(exists)
    
    def test_database_stats(self):
        """Test database statistics calculation"""
        # Add test data
        self.db.add_single_translation("color", "色")
        self.db.add_single_translation("color", "カラー")
        self.db.add_single_translation("red", "赤")
        
        stats = self.db.get_database_stats()
        self.assertEqual(stats['total_translation_pairs'], 3)
        self.assertEqual(stats['unique_english_terms'], 2)
        self.assertEqual(stats['average_translations_per_term'], 1.5)
    
    def test_feedback_method(self):
        """Test the add_japanese_translations_with_feedback method"""
        # Test adding new translations
        feedback = self.db.add_japanese_translations_with_feedback("feedback", ["フィードバック", "返答"])
        self.assertEqual(feedback['attempted'], 2)
        self.assertEqual(feedback['inserted'], 2)
        self.assertEqual(feedback['duplicates'], 0)
        
        # Test adding duplicates
        feedback2 = self.db.add_japanese_translations_with_feedback("feedback", ["フィードバック", "新しい"])
        self.assertEqual(feedback2['attempted'], 2)
        self.assertEqual(feedback2['inserted'], 1)  # Only "新しい" is new
        self.assertEqual(feedback2['duplicates'], 1)  # "フィードバック" already exists
    
    def test_additional_methods(self):
        """Test other Database methods"""
        # Test contains_english_term
        self.assertFalse(self.db.contains_english_term("nonexistent"))
        
        self.db.add_single_translation("exists", "存在する")
        self.assertTrue(self.db.contains_english_term("exists"))
        
        # Test get_english_term_stats
        stats = self.db.get_english_term_stats("exists")
        self.assertEqual(stats['english_term'], "exists")
        self.assertEqual(stats['translation_count'], 1)
        self.assertTrue(stats['exists'])
        
        # Test get_all_english_terms
        self.db.add_single_translation("another", "別の")
        terms = self.db.get_all_english_terms()
        self.assertIn("exists", terms)
        self.assertIn("another", terms)


if __name__ == '__main__':
    unittest.main()