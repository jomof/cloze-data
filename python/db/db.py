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
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        PRIMARY KEY (key, value)
                    )
                ''')
                
                conn.execute('CREATE INDEX idx_english_to_japanese_key ON english_to_japanese(key)')
                conn.execute('CREATE INDEX idx_english_to_japanese_value ON english_to_japanese(value)')
                
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
        """Connection optimized for frequent key updates"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=45.0)
                
                # Set all the performance optimizations per connection
                conn.execute('PRAGMA busy_timeout=45000')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=50000')  # Larger cache for frequent key lookups
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
    
    def add_values_to_key(self, key: str, values: List[str]):
        """Add multiple values to an existing or new key"""
        if not values:
            return
        
        # Pre-filter duplicates to reduce database work
        unique_values = list(set(values))
        batch_data = [(key, value) for value in unique_values]
        
        with self.get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                # INSERT OR IGNORE is perfect for adding to existing keys
                # It handles both new keys and adding to existing keys seamlessly
                # The composite primary key (key, value) provides set semantics automatically
                conn.executemany(
                    'INSERT OR IGNORE INTO english_to_japanese (key, value) VALUES (?, ?)',
                    batch_data
                )
                conn.commit()
                return len(batch_data)  # Return number of values attempted
            except Exception:
                conn.rollback()
                raise
    
    def add_values_to_key_with_feedback(self, key: str, values: List[str]) -> dict:
        """Add values and return detailed feedback about what was inserted"""
        if not values:
            return {'attempted': 0, 'inserted': 0, 'duplicates': 0}
        
        unique_values = list(set(values))
        
        with self.get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                # Check existing values first
                existing_cursor = conn.execute(
                    f'SELECT value FROM english_to_japanese WHERE key = ? AND value IN ({",".join("?" * len(unique_values))})',
                    [key] + unique_values
                )
                existing_values = {row[0] for row in existing_cursor.fetchall()}
                
                # Only insert truly new values
                new_values = [v for v in unique_values if v not in existing_values]
                inserted_count = 0
                
                if new_values:
                    batch_data = [(key, value) for value in new_values]
                    conn.executemany(
                        'INSERT INTO english_to_japanese (key, value) VALUES (?, ?)',
                        batch_data
                    )
                    inserted_count = len(new_values)
                
                conn.commit()
                
                return {
                    'attempted': len(unique_values),
                    'inserted': inserted_count,
                    'duplicates': len(existing_values)
                }
            except Exception:
                conn.rollback()
                raise
    
    def add_single_value(self, key: str, value: str):
        """Add single key-value pair (convenience method)"""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT OR IGNORE INTO english_to_japanese (key, value) VALUES (?, ?)',
                (key, value)
            )
            conn.commit()
    
    def contains_key(self, key: str) -> bool:
        """Fast key existence check"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT 1 FROM english_to_japanese WHERE key = ? LIMIT 1', (key,))
            return cursor.fetchone() is not None
    
    def get_values(self, key: str) -> Set[str]:
        """Get all values for a key as a set"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT value FROM english_to_japanese WHERE key = ?', (key,))
            return {row[0] for row in cursor.fetchall()}
    
    def get_value_count(self, key: str) -> int:
        """Get count of values for a key"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM english_to_japanese WHERE key = ?', (key,))
            return cursor.fetchone()[0]
    
    def get_key_stats(self, key: str) -> dict:
        """Get statistics for a specific key"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM english_to_japanese WHERE key = ?', (key,))
            count = cursor.fetchone()[0]
            return {
                'key': key,
                'value_count': count,
                'exists': count > 0
            }
    
    def is_value_in_key(self, key: str, value: str) -> bool:
        """Check if a specific value exists for a key"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT 1 FROM english_to_japanese WHERE key = ? AND value = ? LIMIT 1',
                (key, value)
            )
            return cursor.fetchone() is not None
    
    def get_all_keys(self) -> Set[str]:
        """Get all keys in the database"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT DISTINCT key FROM english_to_japanese')
            return {row[0] for row in cursor.fetchall()}
    
    def get_database_stats(self) -> dict:
        """Get overall database statistics"""
        with self.get_connection() as conn:
            # Total number of key-value pairs
            cursor = conn.execute('SELECT COUNT(*) FROM english_to_japanese')
            total_pairs = cursor.fetchone()[0]
            
            # Number of unique keys
            cursor = conn.execute('SELECT COUNT(DISTINCT key) FROM english_to_japanese')
            unique_keys = cursor.fetchone()[0]
            
            # Average values per key
            avg_values = total_pairs / unique_keys if unique_keys > 0 else 0
            
            return {
                'total_key_value_pairs': total_pairs,
                'unique_keys': unique_keys,
                'average_values_per_key': round(avg_values, 2)
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