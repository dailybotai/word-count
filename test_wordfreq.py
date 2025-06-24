import unittest
import tempfile
import os
from wordfreq import (
    SimpleHashTable, 
    SQLiteCounter, 
    tokenize_text, 
    read_file_words,
    process_file_hashtable,
    process_file_sqlite
)


class TestSimpleHashTable(unittest.TestCase):
    """Test cases for the custom hash table implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hash_table = SimpleHashTable(initial_size=10)
    
    def test_put_and_get_basic(self):
        """Test basic put and get operations."""
        self.hash_table.put("hello", 5)
        self.hash_table.put("world", 3)
        
        self.assertEqual(self.hash_table.get("hello"), 5)
        self.assertEqual(self.hash_table.get("world"), 3)
        self.assertEqual(self.hash_table.get("nonexistent"), 0)
    
    def test_put_update_existing(self):
        """Test updating existing keys."""
        self.hash_table.put("test", 1)
        self.hash_table.put("test", 5)
        
        self.assertEqual(self.hash_table.get("test"), 5)
    
    def test_increment_method(self):
        """Test the increment functionality."""
        self.hash_table.increment("word")
        self.assertEqual(self.hash_table.get("word"), 1)
        
        self.hash_table.increment("word")
        self.assertEqual(self.hash_table.get("word"), 2)
        
        self.hash_table.increment("word")
        self.assertEqual(self.hash_table.get("word"), 3)
    
    def test_get_all_items(self):
        """Test retrieving all key-value pairs."""
        self.hash_table.put("apple", 5)
        self.hash_table.put("banana", 3)
        self.hash_table.put("cherry", 8)
        
        items = self.hash_table.get_all_items()
        items_dict = dict(items)
        
        self.assertEqual(len(items), 3)
        self.assertEqual(items_dict["apple"], 5)
        self.assertEqual(items_dict["banana"], 3)
        self.assertEqual(items_dict["cherry"], 8)
    
    def test_hash_table_resize(self):
        """Test that hash table resizes properly when load factor is high."""
        # Create small table to force resize
        small_table = SimpleHashTable(initial_size=4)
        
        # Add enough items to trigger resize (>70% load factor)
        words = ["one", "two", "three", "four", "five"]
        for word in words:
            small_table.put(word, 1)
        
        # Verify all items are still accessible after resize
        for word in words:
            self.assertEqual(small_table.get(word), 1)
        
        # Table should have grown
        self.assertGreater(small_table.size, 4)
    
    def test_collision_handling(self):
        """Test that collisions are handled correctly with linear probing."""
        # Create a small table to force collisions
        small_table = SimpleHashTable(initial_size=3)
        
        # Add multiple items that may collide
        small_table.put("a", 1)
        small_table.put("b", 2)
        small_table.put("c", 3)
        
        # All should be retrievable despite potential collisions
        self.assertEqual(small_table.get("a"), 1)
        self.assertEqual(small_table.get("b"), 2)
        self.assertEqual(small_table.get("c"), 3)
    
    def test_empty_table(self):
        """Test operations on empty table."""
        empty_table = SimpleHashTable()
        
        self.assertEqual(empty_table.get("anything"), 0)
        self.assertEqual(empty_table.get_all_items(), [])
        self.assertEqual(empty_table.count, 0)


class TestSQLiteCounter(unittest.TestCase):
    """Test cases for the SQLite counter implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.counter = SQLiteCounter()
    
    def tearDown(self):
        """Clean up after each test."""
        self.counter.close()
    
    def test_increment_basic(self):
        """Test basic increment functionality."""
        self.counter.increment("hello")
        self.counter.increment("world")
        self.counter.increment("hello")
        
        results = self.counter.get_top_words(10)
        results_dict = dict(results)
        
        self.assertEqual(results_dict["hello"], 2)
        self.assertEqual(results_dict["world"], 1)
    
    def test_get_top_words_ordering(self):
        """Test that top words are returned in correct order."""
        # Add words with different frequencies
        words_counts = [("apple", 5), ("banana", 3), ("cherry", 8), ("date", 1)]
        
        for word, count in words_counts:
            for _ in range(count):
                self.counter.increment(word)
        
        self.counter.conn.commit()
        top_words = self.counter.get_top_words(4)
        
        # Should be ordered by count (descending), then alphabetically
        expected_order = [("cherry", 8), ("apple", 5), ("banana", 3), ("date", 1)]
        self.assertEqual(top_words, expected_order)
    
    def test_get_top_words_limit(self):
        """Test that the limit parameter works correctly."""
        for i in range(10):
            self.counter.increment(f"word{i}")
        
        self.counter.conn.commit()
        
        top_5 = self.counter.get_top_words(5)
        top_3 = self.counter.get_top_words(3)
        
        self.assertEqual(len(top_5), 5)
        self.assertEqual(len(top_3), 3)
    
    def test_alphabetical_tiebreaker(self):
        """Test alphabetical ordering for tied counts."""
        # Add words with same frequency
        words = ["zebra", "apple", "banana"]
        for word in words:
            self.counter.increment(word)
        
        self.counter.conn.commit()
        top_words = self.counter.get_top_words(3)
        
        # Should be alphabetically ordered for same counts
        expected = [("apple", 1), ("banana", 1), ("zebra", 1)]
        self.assertEqual(top_words, expected)
    
    def test_database_cleanup(self):
        """Test that database file is cleaned up properly."""
        db_path = self.counter.db_path
        self.assertTrue(os.path.exists(db_path))
        
        self.counter.close()
        self.assertFalse(os.path.exists(db_path))


class TestTokenization(unittest.TestCase):
    """Test cases for text tokenization."""
    
    def test_basic_tokenization(self):
        """Test basic word extraction."""
        text = "Hello world! How are you?"
        words = tokenize_text(text)
        
        expected = ["hello", "world", "how", "are", "you"]
        self.assertEqual(words, expected)
    
    def test_alphanumeric_only(self):
        """Test that only alphanumeric characters are kept."""
        text = "test123 @#$% abc-def hello_world"
        words = tokenize_text(text)
        
        expected = ["test123", "abc", "def", "hello", "world"]
        self.assertEqual(words, expected)
    
    def test_case_insensitive(self):
        """Test case insensitive processing."""
        text = "Hello HELLO hElLo"
        words = tokenize_text(text)
        
        expected = ["hello", "hello", "hello"]
        self.assertEqual(words, expected)
    
    def test_empty_and_whitespace(self):
        """Test handling of empty strings and whitespace."""
        self.assertEqual(tokenize_text(""), [])
        self.assertEqual(tokenize_text("   "), [])
        self.assertEqual(tokenize_text("\n\t\r"), [])
    
    def test_special_characters(self):
        """Test handling of various special characters."""
        text = "café naïve résumé"  # Non-ASCII characters
        words = tokenize_text(text)
        
        # Should extract only ASCII alphanumeric parts
        expected = ["caf", "na", "ve", "r", "sum"]
        self.assertEqual(words, expected)


class TestFileProcessing(unittest.TestCase):
    """Test cases for file processing functions."""
    
    def setUp(self):
        """Create temporary test files."""
        self.temp_files = []
    
    def tearDown(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except OSError:
                pass
    
    def create_temp_file(self, content: str) -> str:
        """Create a temporary file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def test_read_file_words_generator(self):
        """Test the file word generator."""
        content = "hello world\nhello universe\nworld hello"
        temp_file = self.create_temp_file(content)
        
        words = list(read_file_words(temp_file))
        expected = ["hello", "world", "hello", "universe", "world", "hello"]
        
        self.assertEqual(words, expected)
    
    def test_process_file_hashtable(self):
        """Test complete file processing with hash table."""
        content = "hello world hello universe world hello"
        temp_file = self.create_temp_file(content)
        
        results = process_file_hashtable(temp_file)
        results_dict = dict(results)
        
        self.assertEqual(results_dict["hello"], 3)
        self.assertEqual(results_dict["world"], 2)
        self.assertEqual(results_dict["universe"], 1)
    
    def test_process_file_sqlite(self):
        """Test complete file processing with SQLite."""
        content = "hello world hello universe world hello"
        temp_file = self.create_temp_file(content)
        
        results = process_file_sqlite(temp_file)
        results_dict = dict(results)
        
        self.assertEqual(results_dict["hello"], 3)
        self.assertEqual(results_dict["world"], 2)
        self.assertEqual(results_dict["universe"], 1)
    
    def test_both_methods_same_results(self):
        """Test that both processing methods give identical results."""
        content = """
        The quick brown fox jumps over the lazy dog.
        The dog was lazy, but the fox was quick.
        Brown foxes and lazy dogs are common in stories.
        """
        temp_file = self.create_temp_file(content)
        
        hashtable_results = process_file_hashtable(temp_file)
        sqlite_results = process_file_sqlite(temp_file)
        
        # Both should produce identical results
        self.assertEqual(hashtable_results, sqlite_results)
    
    def test_empty_file(self):
        """Test processing empty file."""
        temp_file = self.create_temp_file("")
        
        hashtable_results = process_file_hashtable(temp_file)
        sqlite_results = process_file_sqlite(temp_file)
        
        self.assertEqual(hashtable_results, [])
        self.assertEqual(sqlite_results, [])
    
    def test_large_text_processing(self):
        """Test processing larger text with repeated words."""
        # Create text with known word frequencies
        words = ["apple"] * 10 + ["banana"] * 7 + ["cherry"] * 15 + ["date"] * 3
        content = " ".join(words)
        temp_file = self.create_temp_file(content)
        
        results = process_file_hashtable(temp_file)
        results_dict = dict(results)
        
        self.assertEqual(results_dict["cherry"], 15)
        self.assertEqual(results_dict["apple"], 10)
        self.assertEqual(results_dict["banana"], 7)
        self.assertEqual(results_dict["date"], 3)
    
    def test_binary_content_handling(self):
        """Test handling of files with binary content."""
        # Create file with some binary data
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Mix of text and binary
            f.write(b"hello world\x00\x01\x02invalid\xff\xfe\ntest data")
            temp_path = f.name
        
        self.temp_files.append(temp_path)
        
        # Should not crash, should extract valid words
        try:
            results = process_file_hashtable(temp_path)
            # Should find some words despite binary content
            words_found = [word for word, count in results]
            self.assertIn("hello", words_found)
            self.assertIn("world", words_found)
        except Exception as e:
            self.fail(f"Processing binary file should not crash: {e}")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        with self.assertRaises(SystemExit):
            list(read_file_words("/path/that/does/not/exist.txt"))
    
    def test_very_long_words(self):
        """Test handling of very long words."""
        hash_table = SimpleHashTable()
        
        # Test with very long word
        long_word = "a" * 1000
        hash_table.increment(long_word)
        
        self.assertEqual(hash_table.get(long_word), 1)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        text = "Hello 世界 café naïve 🌍"
        words = tokenize_text(text)
        
        # Should handle Unicode gracefully, extracting ASCII parts
        self.assertIn("hello", words)
        self.assertIn("caf", words)
    
    def test_hash_collision_stress(self):
        """Stress test hash table with many potential collisions."""
        # Create very small table to force many collisions
        small_table = SimpleHashTable(initial_size=2)
        
        # Add many words
        test_words = [f"word{i}" for i in range(20)]
        for word in test_words:
            small_table.increment(word)
        
        # All words should still be accessible
        for word in test_words:
            self.assertEqual(small_table.get(word), 1)
