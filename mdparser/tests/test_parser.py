import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from mdparser.markdown_parser.parser import Parser, TokenStream, ParseError, parse_markdown
from mdparser.markdown_parser.lexer import Token, TokenType
from mdparser.markdown_parser.ast_nodes import (
    Document, Heading, Paragraph, Text, Bold, Italic,
    Link, ListBlock, ListItem, CodeBlock, CodeSpan,
    BlockQuote, HorizontalRule
)

# ----------------------------------------------------------
# TokenStream tests
# ----------------------------------------------------------

def test_tokenstream_peek_next_expect_match_eof():
    tokens = [
        Token(TokenType.TEXT, "a", 0),
        Token(TokenType.SPACE, " ", 1),
        Token(TokenType.EOF, "", 2)
    ]
    ts = TokenStream(tokens)

    assert ts.peek().type == TokenType.TEXT
    assert ts.next().value == "a"

    assert ts.match(TokenType.SPACE)
    ts.expect(TokenType.SPACE)

    assert ts.eof() is True
    ts.expect(TokenType.EOF)

def test_tokenstream_expect_error():
    ts = TokenStream([
        Token(TokenType.TEXT, "x", 0)
    ])
    with pytest.raises(ParseError):
        ts.expect(TokenType.HASH)

# ----------------------------------------------------------
# Heading
# ----------------------------------------------------------

def test_parse_heading():
    doc = parse_markdown("### Title\n")
    h = doc.blocks[0]
    assert isinstance(h, Heading)
    assert h.level == 3
    assert h.inlines[0].text == "Title"

# Paragraph
def test_parse_paragraph_single():
    doc = parse_markdown("Hello world")
    p = doc.blocks[0]
    assert isinstance(p, Paragraph)
    assert [t.text for t in p.inlines] == ["Hello", " ", "world"]

def test_parse_paragraph_soft_break():
    doc = parse_markdown("Hello\nworld")
    p = doc.blocks[0]
    assert isinstance(p, Paragraph)
    assert [t.text for t in p.inlines] == ["Hello", " ", "world"]

# ----------------------------------------------------------
# Lists
# ----------------------------------------------------------

def test_parse_unordered_list():
    doc = parse_markdown("- item1\n- item2\n")
    lst = doc.blocks[0]
    assert isinstance(lst, ListBlock)
    assert not lst.ordered
    assert len(lst.items) == 2

def test_parse_ordered_list():
    doc = parse_markdown("1. first\n2. second\n")
    lst = doc.blocks[0]
    assert lst.ordered
    assert len(lst.items) == 2

# ----------------------------------------------------------
# Blockquote
# ----------------------------------------------------------

def test_parse_blockquote():
    doc = parse_markdown("> Quote\n> More\n")
    bq = doc.blocks[0]
    assert isinstance(bq, BlockQuote)
    assert len(bq.children) == 2
    # перевіримо текст
    texts = []
    for child in bq.children:
        if isinstance(child, Paragraph):
            for n in child.inlines:
                if isinstance(n, Text):
                    texts.append(n.text)
    assert texts == ["Quote", "More"]

# ----------------------------------------------------------
# Horizontal rule
# ----------------------------------------------------------

def test_parse_horizontal_rule():
    doc = parse_markdown("---\n")
    assert isinstance(doc.blocks[0], HorizontalRule)

# ----------------------------------------------------------
# Fenced codeblock
# ----------------------------------------------------------

def test_parse_fenced_codeblock_simple():
    doc = parse_markdown("```\ncode\n```")
    cb = doc.blocks[0]
    assert isinstance(cb, CodeBlock)
    assert cb.code.strip() == "code"

def test_parse_fenced_codeblock_with_lang():
    doc = parse_markdown("```python\nprint(1)\n```")
    cb = doc.blocks[0]
    assert cb.language == "python"
    assert "print" in cb.code

# ----------------------------------------------------------
# Inline elements: bold, italic, codespan, links
# ----------------------------------------------------------

def test_parse_heading():
    doc = parse_markdown("### Title\n")
    h = doc.blocks[0]
    assert isinstance(h, Heading)
    assert h.level == 3
    assert h.inlines[0].text == "Title"

# Paragraph
def test_parse_paragraph_single():
    doc = parse_markdown("Hello world")
    p = doc.blocks[0]
    assert isinstance(p, Paragraph)
    assert [t.text for t in p.inlines] == ["Hello", " ", "world"]

def test_parse_paragraph_soft_break():
    doc = parse_markdown("Hello\nworld")
    p = doc.blocks[0]
    assert isinstance(p, Paragraph)
    assert [t.text for t in p.inlines] == ["Hello", " ", "world"]

def test_parse_codespan():
    doc = parse_markdown("`code`")
    cs = doc.blocks[0].inlines[0]
    assert isinstance(cs, CodeSpan)
    assert cs.code == "code"

def test_parse_codespan_multiple_backticks():
    doc = parse_markdown("``code``")
    cs = doc.blocks[0].inlines[0]
    assert cs.code == "code"

def test_parse_link():
    doc = parse_markdown("[text](url)")
    ln = doc.blocks[0].inlines[0]
    assert isinstance(ln, Link)
    assert ln.url == "url"
    assert ln.text_nodes[0].text == "text"

# ----------------------------------------------------------
# _is_open_fence, _is_close_fence
# ----------------------------------------------------------

def test_internal_fence_detection():
    p = Parser("```code```")
    ts = p.tokens
    assert p._is_open_fence() is True

def test_close_fence_detection():
    p = Parser("```\ncode\n```")
    # Рухаємося до BACKTICK закриття
    while not p.tokens.eof():
        if p._is_close_fence(3):
            break
        p.tokens.next()
    assert p._is_close_fence(3)

# ----------------------------------------------------------
# parse_inline_until: mixed content
# ----------------------------------------------------------

def test_parse_inline_until_mix():
    doc = parse_markdown("Hello **bold** `code` *i*")
    p = doc.blocks[0]
    types = [type(n).__name__ for n in p.inlines]
    assert types == ["Text", "Text", "Bold", "Text", "CodeSpan", "Text", "Italic"]
    assert [n.text if isinstance(n, Text) else None for n in p.inlines] == ["Hello", " ", None, " ", None, " ", None]

def test_parse_link_with_formatting():
    doc = parse_markdown("[**b** _i_](x)")
    ln = doc.blocks[0].inlines[0]
    assert isinstance(ln.text_nodes[0], Bold)
    assert isinstance(ln.text_nodes[1], Text)  # пробіл
    assert isinstance(ln.text_nodes[2], Italic)

# ----------------------------------------------------------
# parse_paragraph stop at blockstart (hash)
# ----------------------------------------------------------

def test_paragraph_stops_at_heading():
    doc = parse_markdown("hello\n# title")
    assert isinstance(doc.blocks[0], Paragraph)
    assert isinstance(doc.blocks[1], Heading)

# ----------------------------------------------------------
# ERROR: unmatched link bracket
# ----------------------------------------------------------

def test_unmatched_link_raises():
    with pytest.raises(ParseError):
        parse_markdown("[abc")


def test_complex_document():
    text = """# Title

Paragraph text

> Quote

- item 1
- item 2
"""
    doc = parse_markdown(text)

    assert isinstance(doc.blocks[0], Heading)
    assert isinstance(doc.blocks[1], Paragraph)
    assert isinstance(doc.blocks[2], BlockQuote)
    assert isinstance(doc.blocks[3], ListBlock)