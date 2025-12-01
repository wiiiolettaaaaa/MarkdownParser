# tests/test_tokenize.py
import pytest
from  mdparser.markdown_parser.lexer import Lexer, Token

def test_tokenize_basic_heading():
    txt = "# Hello\n"
    tokens = Lexer(txt).tokenize()
    types = [t.type for t in tokens]
    assert 'HASHES' in types
    assert 'TEXT' in types
    assert 'NEWLINE' in types

def test_tokenize_emphasis_and_link():
    txt = "This is **bold** and *italic* and [x](y)\n"
    toks = Lexer(txt).tokenize()
    assert any(t.type == 'DOUBLESTAR' for t in toks)
    assert any(t.type == 'LBRACK' for t in toks)