import pytest
from mdparser.markdown_parser.parser import parse_markdown
from mdparser.markdown_parser.renderer import render_html

# -----------------------------------------------------------
# Golden Master / Snapshot tests for HTML output
# -----------------------------------------------------------

@pytest.mark.parametrize(
    "md_text",
    [
        "# Heading 1\n\nSome **bold** text and *italic* text.",
        "1. First\n2. Second\n3. Third",
        "Normal paragraph\nwith line break.",
        "```\nprint('code block')\n```",
        "Inline `code` example",
        "---"
    ]
)
def test_html_golden(snapshot, md_text):
    """
    Golden master test: parses Markdown and renders HTML,
    compares against stored snapshot.
    """
    doc = parse_markdown(md_text)
    html_output = render_html(doc, pretty=True)
    snapshot.assert_match(html_output, "html_snapshot")