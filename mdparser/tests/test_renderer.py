import pytest
from mdparser.markdown_parser.renderer import (
    HTMLRenderer, PlainTextRenderer, JSONRenderer,
    render_html, render_text, render_json
)
from mdparser.markdown_parser.ast_nodes import (
    Document, Paragraph, Heading, Text, Bold, Italic, Link,
    ListBlock, ListItem, CodeBlock, CodeSpan, BlockQuote, HorizontalRule
)


# -------------------------
# Helper: build inline node
# -------------------------
def T(x): return Text(x)


# ===========================================================
# HTML RENDERER TESTS
# ===========================================================

def test_html_empty_document():
    doc = Document(blocks=[])
    r = HTMLRenderer()
    assert r.render(doc) == ""


def test_html_paragraph():
    doc = Document(blocks=[Paragraph(inlines=[T("hello")])])
    out = HTMLRenderer().render(doc)
    assert out.strip() == "<p>hello</p>"


def test_html_heading_levels_clamped():
    doc = Document(blocks=[Heading(level=99, inlines=[T("X")])])
    out = HTMLRenderer().render(doc)
    assert "<h6>X</h6>" in out


def test_html_bold_italic():
    doc = Document(blocks=[
        Paragraph(inlines=[
            T("A "),
            Bold(children=[T("B")]),
            T(" "),
            Italic(children=[T("C")])
        ])
    ])
    out = render_html(doc)
    assert "<strong>B</strong>" in out
    assert "<em>C</em>" in out


def test_html_link():
    doc = Document(blocks=[
        Paragraph(inlines=[
            Link(url="https://x.y", text_nodes=[T("site")])
        ])
    ])
    out = render_html(doc)
    assert '<a href="https://x.y">site</a>' in out


def test_html_escape_text():
    doc = Document(blocks=[Paragraph(inlines=[T("<x> &")])])
    out = render_html(doc)
    assert "&lt;x&gt;" in out and "&amp;" in out


def test_html_list_unordered():
    doc = Document(blocks=[
        ListBlock(ordered=False, items=[
            ListItem(children=[Paragraph(inlines=[T("one")])]),
            ListItem(children=[Paragraph(inlines=[T("two")])]),
        ])
    ])
    out = render_html(doc)
    assert "<ul>" in out
    assert "<li>one</li>" in out
    assert "<li>two</li>" in out


def test_html_list_ordered():
    doc = Document(blocks=[
        ListBlock(ordered=True, items=[
            ListItem(children=[Paragraph(inlines=[T("a")])]),
            ListItem(children=[Paragraph(inlines=[T("b")])]),
        ])
    ])
    out = render_html(doc)
    assert "<ol>" in out


def test_html_nested_blocks():
    doc = Document(blocks=[
        BlockQuote(children=[
            Paragraph(inlines=[T("q1")]),
            Paragraph(inlines=[T("q2")])
        ])
    ])
    out = render_html(doc)
    assert "<blockquote>" in out
    assert "q1" in out and "q2" in out


def test_html_codeblock():
    doc = Document(blocks=[
        CodeBlock(code='x < y', language="py")
    ])
    out = render_html(doc)
    assert "<pre><code class=\"language-py\">" in out
    assert "x &lt; y" in out  # escaped


def test_html_codespan():
    doc = Document(blocks=[Paragraph(inlines=[CodeSpan(code="x < y")])])
    out = render_html(doc)
    assert "<code>x &lt; y</code>" in out


def test_html_hr():
    doc = Document(blocks=[HorizontalRule()])
    out = render_html(doc)
    assert "<hr />" in out


def test_html_pretty_off():
    doc = Document(blocks=[Paragraph(inlines=[T("hi")])])
    out = render_html(doc, pretty=False)
    assert "\n" not in out
    assert out == "<p>hi</p>"


# ===========================================================
# PLAINTEXT RENDERER
# ===========================================================

def test_plaintext_paragraph():
    doc = Document(blocks=[Paragraph(inlines=[T("a"), T("b")])])
    out = render_text(doc).strip()
    assert out == "ab"


def test_plaintext_heading():
    doc = Document(blocks=[Heading(level=2, inlines=[T("Hi")])])
    out = render_text(doc)
    assert "## Hi" in out


def test_plaintext_bold_italic():
    doc = Document(blocks=[
        Paragraph(inlines=[
            Bold(children=[T("B")]),
            T(" "),
            Italic(children=[T("I")])
        ])
    ])
    out = render_text(doc)
    assert "**B**" in out
    assert "*I*" in out


def test_plaintext_codespan():
    doc = Document(blocks=[Paragraph(inlines=[CodeSpan(code="x")])])
    out = render_text(doc)
    assert "`x`" in out


def test_plaintext_link():
    doc = Document(blocks=[
        Paragraph(inlines=[Link(url="http://x", text_nodes=[T("a")])])
    ])
    out = render_text(doc)
    assert "[a](http://x)" in out


def test_plaintext_list_ordered():
    doc = Document(blocks=[
        ListBlock(ordered=True, items=[
            ListItem(children=[Paragraph(inlines=[T("one")])]),
            ListItem(children=[Paragraph(inlines=[T("two")])]),
        ])
    ])
    out = render_text(doc)
    assert "1. one" in out
    assert "2. two" in out


def test_plaintext_list_unordered():
    doc = Document(blocks=[
        ListBlock(ordered=False, items=[
            ListItem(children=[Paragraph(inlines=[T("a")])]),
        ])
    ])
    out = render_text(doc)
    assert "- a" in out


def test_plaintext_codeblock():
    doc = Document(blocks=[
        CodeBlock(code="print(1)", language="py")
    ])
    out = render_text(doc)
    assert "```py" in out
    assert "print(1)" in out


def test_plaintext_blockquote():
    doc = Document(blocks=[
        BlockQuote(children=[Paragraph(inlines=[T("x")])])
    ])
    out = render_text(doc)
    assert "> x" in out


def test_plaintext_hr():
    doc = Document(blocks=[HorizontalRule()])
    out = render_text(doc)
    assert "---" in out


# ===========================================================
# JSON RENDERER
# ===========================================================

def test_json_renderer_basic(monkeypatch):
    # Fake to_dict for controlled output
    monkeypatch.setattr(Document, "to_dict", lambda self: {"a": 1})
    doc = Document(blocks=[])
    out = render_json(doc)
    assert out.strip() == '{\n  "a": 1\n}'


def test_json_indent_none(monkeypatch):
    monkeypatch.setattr(Document, "to_dict", lambda self: {"x": 2})
    doc = Document(blocks=[])
    out = render_json(doc, indent=None)
    assert out == '{"x": 2}'