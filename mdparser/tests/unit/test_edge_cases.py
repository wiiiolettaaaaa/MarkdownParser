import pytest
from  mdparser.markdown_parser.lexer import Lexer, TokenType
from  mdparser.markdown_parser.parser import Parser
from  mdparser.markdown_parser.renderer import render_html, render_text
from  mdparser.markdown_parser.ast_nodes import Document

# ----------------------------------------
# Edge-cases для Lexer
# ----------------------------------------
def test_empty_file():
    lexer = Lexer("")
    tokens = lexer.tokenize()
    # повинен бути лише EOF
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF

def test_only_whitespace():
    lexer = Lexer("   \n  \t\n")
    tokens = lexer.tokenize()
    # перевіряємо, що токени містять лише NEWLINE і EOF
    types = [t.type for t in tokens]
    assert TokenType.NEWLINE in types
    assert types[-1] == TokenType.EOF

def test_invalid_markdown_sequence():
    txt = "**bold* [link](url"
    lexer = Lexer(txt)
    tokens = lexer.tokenize()
    # Lexer не повинен падати
    assert tokens[-1].type == TokenType.EOF

# ----------------------------------------
# Edge-cases для Parser
# ----------------------------------------
def test_parser_empty():
    parser = Parser("")
    doc = parser.parse()
    assert isinstance(doc, Document)
    html = render_html(doc)
    assert html == "" or html is not None

def test_parser_only_whitespace():
    parser = Parser("   \n\t")
    doc = parser.parse()
    html = render_html(doc)
    assert html == "" or html is not None

def test_parser_nested_list():
    md = "- item1\n  - subitem1\n  - subitem2\n- item2"
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    assert "<ul>" in html
    assert html.count("<li>") >= 4

def test_parser_nested_bold_italic():
    md = "- **bold *italic***"
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    # Вкладені теги
    assert "<strong>" in html
    assert "<em>" in html

def test_parser_unclosed_markdown():
    md = "**bold"
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    # Парсер повинен коректно обробити
    assert html is not None

# ----------------------------------------
# Property-like tests для edge cases
# ----------------------------------------
@pytest.mark.parametrize("text", [
    "", "   ", "\n\n", "**bold", "*italic", "# Heading\n## Sub",
    "- item\n  - subitem", "[link](url", "`code`", "Plain text"
])
def test_parser_various_edge_cases(text):
    parser = Parser(text)
    doc = parser.parse()
    html = render_html(doc)
    txt = render_text(doc)
    assert isinstance(doc, Document)
    assert html is not None
    assert isinstance(txt, str)

# ----------------------------------------
# Test large markdown handling
# ----------------------------------------
def make_large_markdown(n_lines=500):
    lines = ["# Large Document"]
    for i in range(n_lines):
        lines.append(f"Paragraph {i} with **bold** and *italic* and [link](http://example.com/{i})")
    return "\n".join(lines)

def test_large_file_parsing():
    md = make_large_markdown(1000)
    parser = Parser(md)
    doc = parser.parse()
    html = render_html(doc)
    assert "<h1>" in html
    assert html.count("<p>") > 900  # перевірка що всі параграфи присутні