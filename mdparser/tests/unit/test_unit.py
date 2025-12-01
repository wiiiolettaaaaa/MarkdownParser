import pytest
from  mdparser.markdown_parser.lexer import Lexer, TokenType
from  mdparser.markdown_parser.parser import Parser
from  mdparser.markdown_parser.ast_nodes import Document, Heading, Paragraph, Text
from  mdparser.markdown_parser.renderer import render_html, render_text

# ------------------------
# Lexer tests
# ------------------------
def test_empty_file():
    lexer = Lexer("")
    tokens = lexer.tokenize()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF

def test_whitespace_file():
    lexer = Lexer("   \n\t")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert TokenType.NEWLINE in types
    assert types[-1] == TokenType.EOF

def test_simple_heading_and_paragraph():
    md = "# Heading\nParagraph"
    lexer = Lexer(md)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert TokenType.HASH in types
    assert TokenType.TEXT in types

# ------------------------
# Parser tests
# ------------------------
def test_parse_empty():
    parser = Parser("")
    doc = parser.parse()
    assert isinstance(doc, Document)

def test_parse_heading_paragraph():
    md = "# Title\nThis is a paragraph."
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    assert "<h1>" in html
    assert "<p>" in html

def test_parse_bold_italic_text():
    md = "This is **bold** and *italic*."
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    assert "<strong>" in html
    assert "<em>" in html

def test_nested_list():
    md = "- item1\n  - subitem1\n  - subitem2\n- item2"
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    assert "<ul>" in html
    assert html.count("<li>") >= 4