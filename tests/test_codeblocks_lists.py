from mdparser.lexer import Lexer
from mdparser.parser import Parser
from mdparser.factory import NodeFactory
from mdparser.renderer import render

def test_code_fence_and_lists():
    md = """```python
print("hello")
    	1.	one
    	2.	two

    	•	a
    	•	b

    quoted line
    """

    tokens = Lexer(md).tokenize()
    parser = Parser(tokens, factory=NodeFactory())
    ast = parser.parse()
    html = render(ast)

    # Code block must be rendered
    assert '<pre><code' in html
    assert 'print(&quot;hello&quot;)' in html

    # Ordered list must exist
    assert '<ol>' in html
    assert '<li>one</li>' in html
    assert '<li>two</li>' in html

    # Unordered list must exist
    assert '<ul>' in html
    assert '<li>a</li>' in html
    assert '<li>b</li>' in html

    # Blockquote must exist
    assert '<blockquote>' in html
    assert 'quoted line' in html