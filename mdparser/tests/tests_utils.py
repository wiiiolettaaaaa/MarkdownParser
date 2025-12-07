# tests/test_utils.py
import hashlib
from mdparser.markdown_parser.utils import hash_text

def test_hash_text_returns_sha256():
    text = "hello world"
    expected = hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert hash_text(text) == expected

def test_hash_text_consistency():
    text = "consistent text"
    first = hash_text(text)
    second = hash_text(text)
    assert first == second

def test_hash_text_length():
    text = "any text"
    result = hash_text(text)
    assert isinstance(result, str)
    assert len(result) == 64