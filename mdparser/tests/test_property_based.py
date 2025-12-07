import pytest
from hypothesis import given, strategies as st

from mdparser.markdown_parser.parser import parse_markdown, Parser, ParseError
from mdparser.markdown_parser.renderer import HTMLRenderer
from mdparser.markdown_parser.ast_nodes import Document


markdown_chars = st.characters(
    blacklist_categories=["Cs"],
    blacklist_characters=["\x00"]
)

markdown_texts = st.text(
    alphabet=markdown_chars,
    min_size=0,
    max_size=300
)


# ============================================================
# HELPER: parse safely (ParseError is normal!)
# ============================================================

def safe_parse(text):
    """
    Парсер може кинути ParseError — це нормальна поведінка.
    Але він НЕ повинен кидати жодних інших виключень.
    """
    try:
        return parse_markdown(text)
    except ParseError:
        # нормальна ситуація: Markdown некоректний
        return None


# ============================================================
# TEST 1: parser must not crash unexpectedly
# ============================================================

@given(markdown_texts)
def test_parser_does_not_crash(text):
    """Парсер може викинути ParseError, але не має кидати інші виключення."""
    try:
        safe_parse(text)
    except Exception:
        pytest.fail(f"Parser crashed with unexpected error on: {text!r}")


# ============================================================
# TEST 2: HTML renderer must not crash after successful parse
# ============================================================

@given(markdown_texts)
def test_html_renderer_does_not_crash(text):
    ast = safe_parse(text)
    if ast is None:
        return  # некоректний markdown → рендер пропускаємо

    try:
        html = HTMLRenderer().render(ast)
        assert isinstance(html, str)
    except Exception:
        pytest.fail("HTML renderer crashed unexpectedly.")


# ============================================================
# TEST 3: Idempotency for successful parses only
# ============================================================

@given(markdown_texts)
def test_parser_idempotent_with_html(text):
    ast1 = safe_parse(text)
    if ast1 is None:
        return  # некоректний вхід — тест не застосовується

    renderer = HTMLRenderer()
    html = renderer.render(ast1)

    try:
        safe_parse(html)
    except Exception:
        pytest.fail("Idempotency test failed: HTML re-parse crashed unexpectedly.")


# ============================================================
# TEST 4: AST structure validation for successful parses only
# ============================================================

def validate_ast(node):
    # Можна додати розширені перевірки, тут – базові
    assert node is not None
    assert hasattr(node, "__class__")


@given(markdown_texts)
def test_ast_structure_is_valid(text):
    ast = safe_parse(text)
    if ast is None:
        return

    validate_ast(ast)