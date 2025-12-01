import pytest
from  mdparser.markdown_parser.parser import Parser
from  mdparser.markdown_parser.renderer import render_html

GOLDEN = {
    "heading_paragraph": {
        "md": "# Title\nParagraph",
        "html": ["<h1>Title</h1>", "<p>Paragraph</p>"]
    },
    "bold_italic": {
        "md": "This is **bold** and *italic*",
        "html": ["<strong>bold</strong>", "<em>italic</em>"]
    },
    "list_nested": {
        "md": "- item1\n  - subitem1\n- item2",
        "html": ["<ul>", "<li>item1", "<li>subitem1"]
    }
}

@pytest.mark.parametrize("name,case", GOLDEN.items())
def test_golden(name, case):
    parser = Parser(case["md"])
    doc = parser.parse()
    html = render_html(doc)
    for snippet in case["html"]:
        assert snippet in html