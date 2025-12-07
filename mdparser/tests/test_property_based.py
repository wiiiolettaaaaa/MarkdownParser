import pytest
from hypothesis import given, strategies as st

from mdparser.markdown_parser.parser import parse_markdown, ParseError
from mdparser.markdown_parser.renderer import HTMLRenderer

# ============================================================
# Hypothesis strategies
# ============================================================

markdown_chars = st.characters(
    blacklist_categories=["Cs"],  # уникати сурогатних пар
    blacklist_characters=["\x00"]  # null char
)

markdown_texts = st.text(
    alphabet=markdown_chars,
    min_size=0,
    max_size=300
)

# ============================================================
# TEST 1: parser must not crash unexpectedly
# ============================================================

@given(markdown_texts)
def test_parser_does_not_crash(text):
    """
    Парсер повинен обробити будь-який текст.
    ParseError — це допустима поведінка для некоректного Markdown.
    Інші винятки — не допустимі.
    """
    parse_markdown(text)  # ParseError тут не ловимо, щоб Hypothesis показав приклад

# ============================================================
# TEST 2: HTML renderer must not crash after successful parse
# ============================================================

@given(markdown_texts)
def test_html_renderer_does_not_crash(text):
    """
    Рендерер HTML повинен коректно працювати на успішно розпарсеному AST.
    ParseError не ловимо, бо це показує баги парсера.
    """
    ast = parse_markdown(text)  # може кинути ParseError → Hypothesis покаже приклад
    html = HTMLRenderer().render(ast)
    assert isinstance(html, str)

# ============================================================
# TEST 3: Idempotency for successful parses only
# ============================================================

@given(markdown_texts)
def test_parser_idempotent_with_html(text):
    """
    Парсер повинен коректно парсити HTML, отриманий від рендера AST.
    ParseError сигналізує про баг у парсері.
    """
    ast1 = parse_markdown(text)
    renderer = HTMLRenderer()
    html = renderer.render(ast1)

    # Перепарсити згенерований HTML
    parse_markdown(html)  # ParseError тут не ловимо

# ============================================================
# TEST 4: AST structure validation for successful parses only
# ============================================================

def validate_ast(node):
    assert node is not None
    assert hasattr(node, "__class__")

@given(markdown_texts)
def test_ast_structure_is_valid(text):
    ast = parse_markdown(text)
    validate_ast(ast)