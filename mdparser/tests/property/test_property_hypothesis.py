from hypothesis import given, strategies as st
from  mdparser.markdown_parser.parser import Parser
from  mdparser.markdown_parser.renderer import render_html

# Генеруємо випадкові Markdown-фрагменти
markdown_chars = st.text(
    alphabet=st.characters(whitelist_categories=('Lu','Ll','Nd','Zs')) |
             st.just("#") | st.just("*") | st.just("[") | st.just("]") |
             st.just("(") | st.just(")") | st.just("`") | st.just("-"),
    min_size=1,
    max_size=300
)

@given(markdown_chars)
def test_parser_never_raises_random_input(md_text):
    parser = Parser(md_text)
    doc = parser.parse()
    html = render_html(doc)
    assert isinstance(html, str)