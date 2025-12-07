import pytest
from mdparser.markdown_parser.lexer import (
    Lexer,
    TokenType,
    Token,
    tokenize_markdown
)

# -----------------------------------------------------------
# Тестування токенізації простих символів
# -----------------------------------------------------------

def test_hash_token():
    lexer = Lexer("#")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.HASH
    assert tokens[1].type == TokenType.EOF


def test_dash_token():
    lexer = Lexer("-")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.DASH
    assert tokens[1].type == TokenType.EOF


def test_star_token():
    lexer = Lexer("*")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STAR
    assert tokens[1].type == TokenType.EOF


def test_underscore_token():
    lexer = Lexer("_")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.UNDERSCORE
    assert tokens[1].type == TokenType.EOF


def test_backtick_token():
    lexer = Lexer("`")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.BACKTICK
    assert tokens[1].type == TokenType.EOF


def test_double_star_token():
    lexer = Lexer("**")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.DOUBLE_STAR
    assert tokens[1].type == TokenType.EOF


# -----------------------------------------------------------
# Тестування пробілів та INDENT
# -----------------------------------------------------------

def test_space_token():
    lexer = Lexer(" ")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.SPACE


def test_indent_token():
    lexer = Lexer("    hello")  # 4 space
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.INDENT
    assert tokens[1].type == TokenType.TEXT


# -----------------------------------------------------------
# Тестування NEWLINE і EOF
# -----------------------------------------------------------

def test_newline_token():
    lexer = Lexer("\n")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.NEWLINE
    assert tokens[1].type == TokenType.EOF


def test_eof_direct():
    lexer = Lexer("")
    token = lexer.next_token()
    assert token.type == TokenType.EOF


# -----------------------------------------------------------
# Тестування дужок
# -----------------------------------------------------------

def test_brackets():
    lexer = Lexer("[]()")
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.LBRACKET
    assert tokens[1].type == TokenType.RBRACKET
    assert tokens[2].type == TokenType.LPAREN
    assert tokens[3].type == TokenType.RPAREN


# -----------------------------------------------------------
# NUMBER токен (1., 23.)
# -----------------------------------------------------------

def test_number_token():
    lexer = Lexer("12. text")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == "12."
    assert tokens[1].type == TokenType.SPACE
    assert tokens[2].type == TokenType.TEXT


# -----------------------------------------------------------
# TEXT токени
# -----------------------------------------------------------

def test_text_token_simple():
    lexer = Lexer("hello")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.TEXT
    assert tokens[0].value == "hello"
    assert tokens[1].type == TokenType.EOF


def test_text_with_symbols_edge_case():
    lexer = Lexer("abc#def")
    tokens = lexer.tokenize()
    # 'abc' = TEXT, '#' = HASH, 'def' = TEXT
    assert tokens[0].type == TokenType.TEXT
    assert tokens[1].type == TokenType.HASH
    assert tokens[2].type == TokenType.TEXT


# -----------------------------------------------------------
# Тестування змішаного рядка — найважливіше
# -----------------------------------------------------------

def test_complex_markdown_line():
    text = "# Title\n* Item **bold** and _i_ `code` 1."
    tokens = tokenize_markdown(text)

    # Перевіримо кілька ключових токенів
    types = [t.type for t in tokens]

    assert TokenType.HASH in types
    assert TokenType.STAR in types
    assert TokenType.DOUBLE_STAR in types
    assert TokenType.UNDERSCORE in types
    assert TokenType.BACKTICK in types
    assert TokenType.NUMBER in types
    assert TokenType.TEXT in types
    assert TokenType.NEWLINE in types
    assert TokenType.EOF == tokens[-1].type


# -----------------------------------------------------------
# Тестування _peek()
# -----------------------------------------------------------

def test_peek_true():
    lexer = Lexer("**bold")
    assert lexer._peek("**") is True


def test_peek_false():
    lexer = Lexer("*x")
    assert lexer._peek("**") is False


# -----------------------------------------------------------
# Повна інтеграція tokenize_markdown()
# -----------------------------------------------------------

def test_tokenize_markdown_wrapper():
    tokens = tokenize_markdown("# a")
    assert tokens[0].type == TokenType.HASH
    assert tokens[-1].type == TokenType.EOF