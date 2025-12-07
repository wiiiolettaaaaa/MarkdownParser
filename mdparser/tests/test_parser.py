import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from mdparser.markdown_parser.parser import Parser, TokenStream, ParseError, parse_markdown
from mdparser.markdown_parser.lexer import Token, TokenType
from mdparser.markdown_parser.ast_nodes import (
    Document, Heading, Paragraph, Text, Bold, Italic,
    Link, ListBlock, ListItem, CodeBlock, CodeSpan,
    BlockQuote, HorizontalRule,
    mk_text, mk_bold, mk_italic, mk_link, mk_paragraph, mk_heading, mk_codeblock, mk_list,
    _node_from_dict
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

def test_text_to_from_dict():
    t = Text("hello")
    d = t.to_dict()
    t2 = Text.from_dict(d)
    assert t2.text == "hello"

def test_bold_to_from_dict():
    b = Bold([Text("x"), Italic([Text("y")])])
    d = b.to_dict()
    b2 = Bold.from_dict(d)
    assert isinstance(b2.children[0], Text)
    assert b2.children[0].text == "x"
    assert isinstance(b2.children[1], Italic)
    assert b2.children[1].children[0].text == "y"

def test_link_to_from_dict():
    l = Link([Text("txt")], url="u", title="t")
    d = l.to_dict()
    l2 = Link.from_dict(d)
    assert l2.url == "u"
    assert l2.title == "t"
    assert l2.text_nodes[0].text == "txt"


def test_document_to_from_dict():
    doc = Document(blocks=[Paragraph([Text("x")]), Heading(2, [Text("h")])])
    d = doc.to_dict()
    doc2 = Document.from_dict(d)
    assert len(doc2.blocks) == 2
    assert isinstance(doc2.blocks[0], Paragraph)
    assert doc2.blocks[0].inlines[0].text == "x"
    assert isinstance(doc2.blocks[1], Heading)
    assert doc2.blocks[1].level == 2

def test_listblock_to_from_dict():
    item1 = ListItem([Paragraph([Text("a")])])
    item2 = ListItem([Paragraph([Text("b")])])
    lst = ListBlock([item1, item2], ordered=True)
    d = lst.to_dict()
    lst2 = ListBlock.from_dict(d)
    assert lst2.ordered is True
    assert len(lst2.items) == 2
    assert lst2.items[0].children[0].inlines[0].text == "a"

def test_mk_helpers():
    t = mk_text("x")
    b = mk_bold(t)
    i = mk_italic(t)
    l = mk_link("url", t, title="t")
    p = mk_paragraph(t, b)
    h = mk_heading(1, t)
    cb = mk_codeblock("code")
    lst = mk_list(ListItem([p]), ordered=True)

    assert isinstance(t, Text)
    assert isinstance(b, Bold)
    assert isinstance(i, Italic)
    assert isinstance(l, Link)
    assert isinstance(p, Paragraph)
    assert isinstance(h, Heading)
    assert isinstance(cb, CodeBlock)
    assert isinstance(lst, ListBlock)

import pytest

def test_node_from_dict_unknown_type():
    with pytest.raises(ValueError):
        _node_from_dict({"type": "Unknown"})

def test_node_from_dict_missing_type():
    with pytest.raises(ValueError):
        _node_from_dict({})