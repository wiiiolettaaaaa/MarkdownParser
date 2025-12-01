# tests/test_parse_line.py
from  mdparser.markdown_parser.parser import Parser
from  mdparser.markdown_parser.renderer import HTMLRenderer

def test_parse_heading_paragraph():
    md = "# Title\nParagraph text\n"
    p = Parser(md)
    doc = p.parse()
    html = HTMLRenderer().render(doc)
    assert '<h1>' in html
    assert '<p>' in html

def test_parse_code_span_and_block():
    md = "Inline `code` here.\n\n```python\nprint(1)\n```\n"
    p = Parser(md)
    doc = p.parse()
    html = HTMLRenderer().render(doc)
    assert '<code>' in html
    assert '<pre><code' in html