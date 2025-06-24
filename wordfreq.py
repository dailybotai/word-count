"""
Word frequency counter with two different implementations.
No built-in dictionaries (dict, Counter, etc.) are used.

Modes:
1. hashtable - Custom hash table (default)
2. sqlite - Disk-backed SQLite counter  
"""

import sys
import re
import argparse
import sqlite3
import os
import tempfile
from collections.abc import Generator


class SimpleHashTable:
    """Custom hash table implementation using linear probing."""
    
    def __init__(self, initial_size: int = 1000) -> None:
        self.size: int = initial_size
        self.keys: list[str | None] = [None] * self.size
        self.values: list[int] = [0] * self.size
        self.count: int = 0
    
    def _hash(self, key: str) -> int:
        """Simple hash function."""
        hash_value = 0
        for char in key:
            hash_value = (hash_value * 31 + ord(char)) % self.size
        return hash_value
    
    def _resize(self) -> None:
        """Resize table when load factor gets too high."""
        old_keys = self.keys
        old_values = self.values
        old_size = self.size
        
        self.size *= 2
        self.keys = [None] * self.size
        self.values = [0] * self.size
        self.count = 0
        
        # Rehash all existing items
        for i in range(old_size):
            if old_keys[i]:
                self.put(old_keys[i], old_values[i])
    
    def put(self, key: str, value: int) -> None:
        """Insert or update key-value pair."""
        if self.count >= self.size * 0.7:  # Load factor threshold
            self._resize()
        
        index = self._hash(key)
        original_index = index
        
        while self.keys[index] is not None:
            if self.keys[index] == key:
                self.values[index] = value
                return
            index = (index + 1) % self.size
            if index == original_index:  # Table is full (shouldn't happen with resize)
                raise Exception("Hash table is full")
        
        self.keys[index] = key
        self.values[index] = value
        self.count += 1
    
    def get(self, key: str) -> int:
        """Get value for key, return 0 if not found."""
        index = self._hash(key)
        original_index = index
        
        while self.keys[index] is not None:
            if self.keys[index] == key:
                return self.values[index]
            index = (index + 1) % self.size
            if index == original_index:
                break
        return 0
    
    def increment(self, key: str) -> None:
        """Increment counter for key."""
        current_value = self.get(key)
        self.put(key, current_value + 1)
    
    def get_all_items(self) -> list[tuple[str, int]]:
        """Return all key-value pairs."""
        items = []
        for i in range(self.size):
            if self.keys[i]:
                items.append((self.keys[i], self.values[i]))
        return items


class SQLiteCounter:
    """SQLite-backed word counter."""
    
    def __init__(self) -> None:
        self.db_path: str = tempfile.mktemp(suffix='.db')
        self.conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        self.conn.execute('''
            CREATE TABLE word_counts (
                word TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()
    
    def increment(self, word: str) -> None:
        """Increment count for a word."""
        self.conn.execute('''
            INSERT INTO word_counts (word, count) VALUES (?, 1)
            ON CONFLICT(word) DO UPDATE SET count = count + 1
        ''', (word,))
    
    def get_top_words(self, limit: int = 20) -> list[tuple[str, int]]:
        """Get top N words by count."""
        cursor = self.conn.execute('''
            SELECT word, count FROM word_counts 
            ORDER BY count DESC, word ASC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def close(self) -> None:
        """Clean up database."""
        self.conn.close()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass



def tokenize_text(text: str) -> list[str]:
    """Extract alphanumeric words from text, case-insensitive."""
    # Find all sequences of alphanumeric characters
    words = re.findall(r'[a-zA-Z0-9]+', text)
    return [word.lower() for word in words]


def read_file_words(filepath: str) -> Generator[str, None, None]:
    """Generator that yields words from a file one at a time."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                words = tokenize_text(line)
                for word in words:
                    yield word
    except (IOError, OSError) as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def process_file_hashtable(filepath: str) -> list[tuple[str, int]]:
    """Process file using custom hash table."""
    word_counts = SimpleHashTable()
    
    # Use generator to process words without loading entire file into memory
    for word in read_file_words(filepath):
        word_counts.increment(word)
    
    return get_top_words_hashtable(word_counts)


def process_file_sqlite(filepath: str) -> list[tuple[str, int]]:
    """Process file using SQLite backend."""
    counter = SQLiteCounter()
    
    try:
        # Use generator to process words without loading entire file into memory
        for word in read_file_words(filepath):
            counter.increment(word)
        
        # Commit all changes
        counter.conn.commit()
        
        # Get results
        results = counter.get_top_words(20)
        counter.close()
        
        return results
        
    except Exception as e:
        counter.close()
        print(f"Unexpected error during processing: {e}", file=sys.stderr)
        sys.exit(1)




def get_top_words_hashtable(word_counts: SimpleHashTable, top_n: int = 20) -> list[tuple[str, int]]:
    """Get top N most frequent words from hash table."""
    all_items = word_counts.get_all_items()
    
    # Sort by count (descending), then by word (ascending) for ties
    sorted_items = sorted(all_items, key=lambda x: (-x[1], x[0]))
    
    return sorted_items[:top_n]


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Count word frequencies in a text file (top 20)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wordfreq document.txt
  wordfreq --mode=sqlite document.txt
  python wordfreq.py /path/to/file.txt
        """
    )
    parser.add_argument('filepath', help='Path to text file to analyze')
    parser.add_argument(
        '--mode', 
        choices=['hashtable', 'sqlite'], 
        default='hashtable',
        help='Processing mode (default: hashtable)'
    )
    
    args = parser.parse_args()
    
    # Process the file based on mode
    if args.mode == 'hashtable':
        top_words = process_file_hashtable(args.filepath)
    elif args.mode == 'sqlite':
        top_words = process_file_sqlite(args.filepath)
    else:
        print(f"Unknown mode: {args.mode}", file=sys.stderr)
        sys.exit(1)
    
    # Display results
    if not top_words:
        print("No words found in file.")
        return
    
    for word, count in top_words:
        print(f"{count} {word}")


if __name__ == "__main__":
    main() 