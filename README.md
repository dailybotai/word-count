# Word Frequency Counter

A command-line tool that counts the 20 most frequent words in a text file with two different implementations (no built-in dictionaries).

## Two Implementations

### 1. Custom Hash Table (default)
- **Performance**: O(N) scan time, near-O(1) per lookup
- **Memory**: Efficient for most use cases
- **Use case**: General purpose, fast processing

### 2. SQLite Disk-Backed Counter
- **Storage**: Uses SQLite database for word counts
- **Memory**: Very low memory usage, disk-based
- **Use case**: Very large files, persistent storage needs

## Features

- **No built-in dicts**: Custom data structures only
- **Memory efficient**: Streams large files line by line
- **Case insensitive**: "The" and "the" are counted as the same word
- **Robust**: Handles binary/malformed input gracefully
- **Containerized**: Runs in Docker with Poetry

## Local Development

### Prerequisites
- Python 3.11+
- Poetry
- Docker (Optional, but recommended)

### Setup
```bash
# Install dependencies
poetry install

# Run with different modes
poetry run python wordfreq.py document.txt                   # hashtable (default)
poetry run python wordfreq.py --mode=sqlite document.txt     # SQLite backend

# Or run directly
python3 wordfreq.py document.txt
python3 wordfreq.py --mode=sqlite document.txt
```

## Docker Usage

### Build the container
```bash
docker build -t wordfreq .
```

### Run with a file
```bash
# Mount your file directory and analyze a file (default hashtable mode)
docker run -v /path/to/your/files:/data wordfreq /data/document.txt

# SQLite mode
docker run -v /path/to/your/files:/data wordfreq --mode=sqlite /data/document.txt
```

### Example with sample file
```bash
# Create a test file
echo "Hello world hello universe world hello" > sample.txt

# Test both modes
docker run -v $(pwd):/data wordfreq /data/sample.txt                   # hashtable
docker run -v $(pwd):/data wordfreq --mode=sqlite /data/sample.txt     # SQLite
```

Expected output (both modes):
```
3 hello
2 world
1 universe
```

## Running Tests
```bash
# Run all tests
python3 test_wordfreq.py

# Run with Poetry
poetry run python test_wordfreq.py

# Run with verbose output
python3 -m unittest test_wordfreq -v
```

## Design Details

### Hash Table Mode (default)
- **Data Structure**: Custom hash table with linear probing and dynamic resizing
- **Memory**: O(unique_words) space complexity  
- **Performance**: O(N) time, O(1) average lookup/insert
- **Best for**: General purpose, fast processing

### SQLite Mode
- **Storage**: Embedded SQLite database with UPSERT operations
- **Memory**: Very low (disk-based storage)
- **Performance**: O(N log N) due to B-tree indexes
- **Best for**: Very large files, memory-constrained environments

### Common Features
- **Tokenization**: Regex-based alphanumeric extraction, case-insensitive
- **Streaming**: Line-by-line processing for memory efficiency
- **Error Handling**: Graceful handling of encoding errors and malformed input
- **Identical Results**: Both modes produce exactly the same word counts and rankings 