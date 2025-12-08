import pytest
from mdparser.markdown_parser.renderer import (
    HTMLRenderer, PlainTextRenderer, JSONRenderer,
    render_html, render_text, render_json, BaseRenderer
)
from mdparser.markdown_parser.ast_nodes import (
    Document, Paragraph, Heading, Text, Bold, Italic, Link,
    ListBlock, ListItem, CodeBlock, CodeSpan, BlockQuote, HorizontalRule, Node
)

def test_base_renderer_get_output_not_implemented():
    class DummyRenderer(BaseRenderer):
        pass
    r = DummyRenderer()
    with pytest.raises(NotImplementedError):
        r.get_output()
# -------------------------
# Helper: build inline node
# -------------------------
def T(x): return Text(x)


# ===========================================================
# HTML RENDERER TESTS
# ===========================================================


def test_html_empty_document():
    doc = Document(blocks=[])
    out = render_html(doc)
    assert out == ""


def test_html_paragraph():
    doc = Document(blocks=[Paragraph(inlines=[T("hello")])])
    expected = "<p>hello</p>\n"
    assert render_html(doc) == expected


def test_html_heading_levels_clamped():
    doc = Document(blocks=[Heading(level=99, inlines=[T("X")])])
    expected = "<h6>X</h6>\n"
    assert render_html(doc) == expected


def test_html_bold_italic():
    doc = Document(blocks=[
        Paragraph(inlines=[T("A "), Bold(children=[T("B")]), T(" "), Italic(children=[T("C")])])
    ])
    expected = "<p>A <strong>B</strong> <em>C</em></p>\n"
    assert render_html(doc) == expected


def test_html_link():
    doc = Document(blocks=[
        Paragraph(inlines=[Link(url="https://x.y", text_nodes=[T("site")])])
    ])
    expected = '<p><a href="https://x.y">site</a></p>\n'
    assert render_html(doc) == expected


def test_html_escape_text():
    doc = Document(blocks=[Paragraph(inlines=[T("<x> &")])])
    expected = "<p>&lt;x&gt; &amp;</p>\n"
    assert render_html(doc) == expected


def test_html_list_unordered():
    doc = Document(blocks=[
        ListBlock(ordered=False, items=[
            ListItem(children=[Paragraph(inlines=[T("one")])]),
            ListItem(children=[Paragraph(inlines=[T("two")])]),
        ])
    ])
    expected = (
        "<ul>\n"
        "  <li>one</li>\n"
        "  <li>two</li>\n"
        "</ul>\n"
    )
    assert render_html(doc) == expected


def test_html_list_ordered():
    doc = Document(blocks=[
        ListBlock(ordered=True, items=[
            ListItem(children=[Paragraph(inlines=[T("a")])]),
            ListItem(children=[Paragraph(inlines=[T("b")])]),
        ])
    ])
    expected = (
        "<ol>\n"
        "  <li>a</li>\n"
        "  <li>b</li>\n"
        "</ol>\n"
    )
    assert render_html(doc) == expected


def test_html_nested_blocks():
    doc = Document(blocks=[
        BlockQuote(children=[
            Paragraph(inlines=[T("q1")]),
            Paragraph(inlines=[T("q2")])
        ])
    ])
    expected = (
        "<blockquote>\n"
        "  <p>q1</p>\n"
        "  <p>q2</p>\n"
        "</blockquote>\n"
    )
    assert render_html(doc) == expected


def test_html_codeblock():
    doc = Document(blocks=[CodeBlock(code='x < y', language="py")])
    expected = '<pre><code class="language-py">x &lt; y</code></pre>\n'
    assert render_html(doc) == expected


def test_html_codespan():
    doc = Document(blocks=[Paragraph(inlines=[CodeSpan(code="x < y")])])
    expected = "<p><code>x &lt; y</code></p>\n"
    assert render_html(doc) == expected


def test_html_hr():
    doc = Document(blocks=[HorizontalRule()])
    expected = "<hr />\n"
    assert render_html(doc) == expected


def test_html_pretty_off():
    doc = Document(blocks=[Paragraph(inlines=[T("hi")])])
    expected = "<p>hi</p>"
    assert render_html(doc, pretty=False) == expected


def test_html_list_item_nested_block():
    doc = Document(blocks=[
        ListBlock(ordered=False, items=[
            ListItem(children=[
                Paragraph(inlines=[T("p")]),
                CodeBlock(code="x", language=None)
            ])
        ])
    ])
    expected = (
        "<ul>\n"
        "  <li>p\n"
        "<pre><code>x</code></pre>\n"
        "  </li>\n"
        "</ul>\n"
    )
    assert render_html(doc) == expected


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

def test_html_list_item_nested_block():
    doc = Document(blocks=[
        ListBlock(ordered=False, items=[
            ListItem(children=[
                Paragraph(inlines=[T("p")]),
                CodeBlock(code="x", language=None)
            ])
        ])
    ])
    out = render_html(doc, pretty=True)
    # Перевіряємо, що <ul> і <li> з вкладеним <pre><code> присутні
    assert "<ul>" in out
    assert "<li>" in out
    assert "<pre><code>x</code></pre>" in out
    assert "</li>" in out
    assert "</ul>" in out

def test_plaintext_renderer_render_inlines_complex():
    from mdparser.markdown_parser.renderer import PlainTextRenderer
    bold = Bold(children=[T("B")])
    italic = Italic(children=[T("I")])
    link = Link(url="url", text_nodes=[T("L")])
    inlines = [T("A"), bold, italic, link]
    r = PlainTextRenderer()
    out = r._render_inlines(inlines)
    assert ''.join(out) == "ABIL"

def test_json_renderer_no_indent(monkeypatch):
    monkeypatch.setattr(Document, "to_dict", lambda self: {"key": "val"})
    doc = Document(blocks=[])
    out = render_json(doc, indent=None)
    assert out == '{"key": "val"}'