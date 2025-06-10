import sqlite3
import time
import random
from contextlib import contextmanager
from typing import List, Set
import os

class Database:
    def __init__(self, db_path: str = '/workspaces/cloze-data/db/grammar.db'):
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self._setup_database()
    
    def _setup_database(self):
        """One-time schema setup - only creates tables/indexes if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Check if we need to do initial setup
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='english_to_japanese'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # First-time setup: create schema and optimize
                print(f"Initializing database schema: {self.db_path}")
                
                # Schema with optimized indexing - composite primary key provides set semantics
                conn.execute('''
                    CREATE TABLE english_to_japanese (
                        japanese TEXT NOT NULL,
                        english TEXT NOT NULL,
                        PRIMARY KEY (japanese, english)
                    )
                ''')
                
                conn.execute('CREATE INDEX idx_english_to_japanese_japanese ON english_to_japanese(japanese)')
                conn.execute('CREATE INDEX idx_english_to_japanese_english ON english_to_japanese(english)')
                
                conn.commit()
            
            # Always set WAL mode (safe to run multiple times, but only takes effect once)
            result = conn.execute('PRAGMA journal_mode=WAL').fetchone()
            if result[0] != 'wal':
                print(f"Enabled WAL mode for: {self.db_path}")
            
            # These settings are connection-specific but database-wide, 
            # so we set them once per connection in get_connection()
            conn.commit()
        finally:
            conn.close()
    
    @contextmanager
    def get_connection(self):
        """Connection optimized for frequent japanese term updates"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=45.0)
                
                # Set all the performance optimizations per connection
                conn.execute('PRAGMA busy_timeout=45000')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=50000')  # Larger cache for frequent japanese term lookups
                conn.execute('PRAGMA temp_store=MEMORY')
                
                # WAL-specific optimizations (only effective if WAL mode is enabled)
                conn.execute('PRAGMA wal_autocheckpoint=5000')  # Less frequent checkpointing
                conn.execute('PRAGMA journal_size_limit=134217728')  # 128MB WAL limit
                
                yield conn
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    # Exponential backoff with jitter for high contention
                    backoff = min(2 ** attempt * 0.1 + random.uniform(0, 0.1), 2.0)
                    time.sleep(backoff)
                    continue
                raise
            finally:
                if 'conn' in locals():
                    conn.close()
    
    def add_english_translations(self, japanese: str, english_translations: List[str]):
        """Add multiple English translations to an existing or new Japanese term"""
        if not english_translations:
            return
        
        # Pre-filter duplicates to reduce database work
        unique_translations = list(set(english_translations))
        batch_data = [(japanese, english) for english in unique_translations]
        
        with self.get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                # INSERT OR IGNORE is perfect for adding to existing japanese terms
                # It handles both new terms and adding to existing terms seamlessly
                # The composite primary key (japanese, english) provides set semantics automatically
                conn.executemany(
                    'INSERT OR IGNORE INTO english_to_japanese (japanese, english) VALUES (?, ?)',
                    batch_data
                )
                conn.commit()
                return len(batch_data)  # Return number of translations attempted
            except Exception:
                conn.rollback()
                raise
    
    def add_english_translations_with_feedback(self, japanese: str, english_translations: List[str]) -> dict:
        """Add English translations and return detailed feedback about what was inserted"""
        if not english_translations:
            return {'attempted': 0, 'inserted': 0, 'duplicates': 0}
        
        unique_translations = list(set(english_translations))
        
        with self.get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                # Check existing translations first
                existing_cursor = conn.execute(
                    f'SELECT english FROM english_to_japanese WHERE japanese = ? AND english IN ({",".join("?" * len(unique_translations))})',
                    [japanese] + unique_translations
                )
                existing_translations = {row[0] for row in existing_cursor.fetchall()}
                
                # Only insert truly new translations
                new_translations = [t for t in unique_translations if t not in existing_translations]
                inserted_count = 0
                
                if new_translations:
                    batch_data = [(japanese, english) for english in new_translations]
                    conn.executemany(
                        'INSERT INTO english_to_japanese (japanese, english) VALUES (?, ?)',
                        batch_data
                    )
                    inserted_count = len(new_translations)
                
                conn.commit()
                
                return {
                    'attempted': len(unique_translations),
                    'inserted': inserted_count,
                    'duplicates': len(existing_translations)
                }
            except Exception:
                conn.rollback()
                raise
    
    def add_single_translation(self, japanese: str, english: str):
        """Add single Japanese-English translation pair (convenience method)"""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT OR IGNORE INTO english_to_japanese (japanese, english) VALUES (?, ?)',
                (japanese, english)
            )
            conn.commit()
    
    def contains_japanese_term(self, japanese: str) -> bool:
        """Fast Japanese term existence check"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT 1 FROM english_to_japanese WHERE japanese = ? LIMIT 1', (japanese,))
            return cursor.fetchone() is not None
    
    def get_english_translations(self, japanese: str) -> Set[str]:
        """Get all English translations for a Japanese term as a set"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT english FROM english_to_japanese WHERE japanese = ?', (japanese,))
            return {row[0] for row in cursor.fetchall()}
    
    def get_translation_count(self, japanese: str) -> int:
        """Get count of English translations for a Japanese term"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM english_to_japanese WHERE japanese = ?', (japanese,))
            return cursor.fetchone()[0]
    
    def get_japanese_term_stats(self, japanese: str) -> dict:
        """Get statistics for a specific Japanese term"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM english_to_japanese WHERE japanese = ?', (japanese,))
            count = cursor.fetchone()[0]
            return {
                'japanese_term': japanese,
                'translation_count': count,
                'exists': count > 0
            }
    
    def has_translation(self, japanese: str, english: str) -> bool:
        """Check if a specific English translation exists for a Japanese term"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT 1 FROM english_to_japanese WHERE japanese = ? AND english = ? LIMIT 1',
                (japanese, english)
            )
            return cursor.fetchone() is not None
    
    def get_all_japanese_terms(self) -> Set[str]:
        """Get all Japanese terms in the database"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT DISTINCT japanese FROM english_to_japanese')
            return {row[0] for row in cursor.fetchall()}
    
    def get_database_stats(self) -> dict:
        """Get overall database statistics"""
        with self.get_connection() as conn:
            # Total number of japanese-english pairs
            cursor = conn.execute('SELECT COUNT(*) FROM english_to_japanese')
            total_pairs = cursor.fetchone()[0]
            
            # Number of unique Japanese terms
            cursor = conn.execute('SELECT COUNT(DISTINCT japanese) FROM english_to_japanese')
            unique_japanese_terms = cursor.fetchone()[0]
            
            # Average translations per Japanese term
            avg_translations = total_pairs / unique_japanese_terms if unique_japanese_terms > 0 else 0
            
            return {
                'total_translation_pairs': total_pairs,
                'unique_japanese_terms': unique_japanese_terms,
                'average_translations_per_term': round(avg_translations, 2)
            }
    
    def vacuum(self):
        """Optimize database file size - typically not needed for append-only workloads"""
        with self.get_connection() as conn:
            conn.execute('VACUUM')
    
    def maintenance(self, force_vacuum: bool = False):
        """Perform database maintenance operations"""
        with self.get_connection() as conn:
            # Always update query planner statistics (lightweight)
            conn.execute('ANALYZE')
            
            # Optional vacuum (expensive, usually not needed)
            if force_vacuum:
                conn.execute('VACUUM')
    
    def get_file_size_mb(self) -> float:
        """Get database file size in MB"""
        import os
        try:
            size_bytes = os.path.getsize(self.db_path)
            return round(size_bytes / (1024 * 1024), 2)
        except OSError:
            return 0.0
    
    def should_vacuum(self) -> bool:
        """Heuristic to determine if VACUUM might be beneficial"""
        with self.get_connection() as conn:
            # Get page count and freelist size
            cursor = conn.execute('PRAGMA page_count')
            page_count = cursor.fetchone()[0]
            
            cursor = conn.execute('PRAGMA freelist_count') 
            freelist_count = cursor.fetchone()[0]
            
            # If more than 25% of pages are free, VACUUM might help
            if page_count > 0:
                free_percentage = freelist_count / page_count
                return free_percentage > 0.25
            return False


# Global instance
_db_instance = Database()

# Export the instance
db = _db_instance