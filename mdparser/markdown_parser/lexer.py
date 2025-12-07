from dataclasses import dataclass
from enum import Enum, auto
import re


# -----------------------------------------------------------
# Token Types
# -----------------------------------------------------------

class TokenType(Enum):
    HASH = auto()               # #
    STAR = auto()               # *
    TEXT = auto()               # будь-який текст
    LBRACKET = auto()           # [
    RBRACKET = auto()           # ]
    LPAREN = auto()             # (
    RPAREN = auto()             # )
    NEWLINE = auto()            # \n
    EOF = auto()                # кінець файлу
    DASH = auto()               # "-"
    UNDERSCORE = auto()         # "_" (курсив)
    DOUBLE_STAR = auto()        # "**" (жирний)
    BACKTICK = auto()           # ` (inline code)
    NUMBER = auto()             # 1. 2. 3.
    INDENT = auto()             # відступи
    SPACE = auto()              # ' '


# -----------------------------------------------------------
# Token Dataclass
# -----------------------------------------------------------

@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# -----------------------------------------------------------
# Lexer
# -----------------------------------------------------------

class Lexer:
    def __init__(self, text: str):
        if not isinstance(text, str):
            raise TypeError(f"Lexer expects str, got {type(text)}: {repr(text)}")
        self.text = text
        self.pos = 0
        self.length = len(text)   # <--- обов’язково, бо next_token його використовує

    # -------------------------------------------------------
    # Основний метод
    # -------------------------------------------------------
    def tokenize(self):
        tokens = []

        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break

        return tokens

    # -------------------------------------------------------
    # Зчитування наступного токена
    # -------------------------------------------------------
    def next_token(self) -> Token:
        if self.pos >= self.length:
            return Token(TokenType.EOF, "", self.pos)

        ch = self.text[self.pos]

        # --- NEWLINE ---
        if ch == "\n":
            self.pos += 1
            return Token(TokenType.NEWLINE, "\n", self.pos)

        # --- SPACE / INDENT ---
        if ch == " ":
            start = self.pos
            while self.pos < self.length and self.text[self.pos] == " ":
                self.pos += 1
            value = self.text[start:self.pos]
            if len(value) >= 4:
                return Token(TokenType.INDENT, value, start)
            return Token(TokenType.SPACE, value, start)

        # --- HASH (#) ---
        if ch == "#":
            self.pos += 1
            return Token(TokenType.HASH, "#", self.pos)

        # --- DASH (-) for list items ---
        if ch == "-":
            self.pos += 1
            return Token(TokenType.DASH, "-", self.pos)

        # --- DOUBLE STAR (**) ---
        if self._peek("**"):
            self.pos += 2
            return Token(TokenType.DOUBLE_STAR, "**", self.pos)

        # --- UNDERSCORE (_) italics ---
        if ch == "_":
            self.pos += 1
            return Token(TokenType.UNDERSCORE, "_", self.pos)

        # --- STAR (*) list item or italics ---
        if ch == "*":
            self.pos += 1
            return Token(TokenType.STAR, "*", self.pos)

        # --- BACKTICK (`) code ---
        if ch == "`":
            self.pos += 1
            return Token(TokenType.BACKTICK, "`", self.pos)

        # --- BRACKETS [ ] ( ) ---
        if ch == "[":
            self.pos += 1
            return Token(TokenType.LBRACKET, "[", self.pos)

        if ch == "]":
            self.pos += 1
            return Token(TokenType.RBRACKET, "]", self.pos)

        if ch == "(":
            self.pos += 1
            return Token(TokenType.LPAREN, "(", self.pos)

        if ch == ")":
            self.pos += 1
            return Token(TokenType.RPAREN, ")", self.pos)

        # --- NUMBER LIST (e.g. "1.") ---
        # --- NUMBER LIST (e.g. "1.") ---
        number_match = None
        if self.text is not None and self.pos < self.length:
            number_match = re.match(r"\d+\.", self.text[self.pos:])

        if number_match:
            value = number_match.group(0)
            self.pos += len(value)
            return Token(TokenType.NUMBER, value, self.pos)

        # --- TEXT ---
        start = self.pos
        while self.pos < self.length and self.text[self.pos] not in "#*[]()_\n`- ":
            self.pos += 1
        value = self.text[start:self.pos]
        return Token(TokenType.TEXT, value, start)

    # -------------------------------------------------------
    # Допоміжний метод
    # -------------------------------------------------------
    def _peek(self, sequence: str) -> bool:
        """
        Перевіряє, чи наступні кілька символів тексту відповідають послідовності.
        """
        end = self.pos + len(sequence)
        if end > self.length:
            return False
        return self.text[self.pos:end] == sequence


# -----------------------------------------------------------
# Функція для швидкого тестування лексера
# (включена в основний проєкт, використовується unit-тестами)
# -----------------------------------------------------------

def tokenize_markdown(text: str):
    """
    Зручна обгортка навколо Lexer для простих викликів.
    """
    lexer = Lexer(text)
    return lexer.tokenize()


# -----------------------------------------------------------
# Ручний тест (буде виконуватись лише при прямому запуску)
# -----------------------------------------------------------

if __name__ == "__main__":
    sample = "# Title\n* Item 1\n* Item 2 with **bold** and _italic_"
    tokens = tokenize_markdown(sample)
    for t in tokens:
        print(t)