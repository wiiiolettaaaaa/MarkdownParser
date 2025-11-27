from mdparser.lexer import Lexer
from mdparser.parser import Parser
from mdparser.factory import NodeFactory
from mdparser.renderer import render

def test_simple_heading_paragraph():
    md = "# Title\n\nThis is **bold** and *italic*."
    tokens = Lexer(md).tokenize()
    parser = Parser(tokens, factory=NodeFactory())
    ast = parser.parse()
    html = render(ast)
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html