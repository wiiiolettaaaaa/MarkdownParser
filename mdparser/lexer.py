from .tokens import Token, TokenType
import re

SPECIAL_CHARS = {'#','-','*','[',']','(',')','\n','`','>','.'}

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)

    def peek(self, k=0):
        idx = self.i + k
        return self.text[idx] if idx < self.n else ''

    def advance(self, steps=1):
        self.i += steps

    def next_token(self):
        if self.i >= self.n:
            return Token(TokenType.EOF, '', self.i)
        ch = self.peek()
        pos = self.i

        # Normalize CRLF
        if ch == '\r':
            if self.peek(1) == '\n':
                self.advance(2)
            else:
                self.advance(1)
            return Token(TokenType.NEWLINE, '\n', pos)
        if ch == '\n':
            self.advance(1)
            return Token(TokenType.NEWLINE, '\n', pos)

        # code fence ```
        if ch == '`' and self.peek(1) == '`' and self.peek(2) == '`':
            # consume leading ```
            self.advance(3)
            # optionally capture language name following fence until newline
            lang = []
            while self.peek() and self.peek() != '\n' and self.peek() != '\r':
                lang.append(self.peek())
                self.advance(1)
            lang_str = ''.join(lang).strip()
            return Token(TokenType.CODE_FENCE, lang_str, pos)

        # double star
        if ch == '*' and self.peek(1) == '*':
            self.advance(2)
            return Token(TokenType.DOUBLE_STAR, '**', pos)
        if ch == '*':
            self.advance(1)
            return Token(TokenType.STAR, '*', pos)

        # hashes
        if ch == '#':
            count = 0
            while self.peek() == '#':
                count += 1
                self.advance(1)
            return Token(TokenType.HASH, '#' * count, pos)

        # blockquote '>'
        if ch == '>':
            self.advance(1)
            return Token(TokenType.GT, '>', pos)

        # dash (list)
        if ch == '-':
            self.advance(1)
            return Token(TokenType.DASH, '-', pos)

        # number ordered list marker at line start: digits + '.' e.g. '1.'
        # we check if at start of line (previous char is newline or pos == 0)
        if ch.isdigit():
            # capture digits and dot without consuming text mid-line incorrectly
            m = re.match(r'(\d+)\.', self.text[self.i:])
            if m:
                num = m.group(0)  # e.g. '1.'
                self.advance(len(num))
                return Token(TokenType.NUMBER, num, pos)

        if ch == '[':
            self.advance(1)
            return Token(TokenType.LBRACKET, '[', pos)
        if ch == ']':
            self.advance(1)
            return Token(TokenType.RBRACKET, ']', pos)
        if ch == '(':
            self.advance(1)
            return Token(TokenType.LPAREN, '(', pos)
        if ch == ')':
            self.advance(1)
            return Token(TokenType.RPAREN, ')', pos)

        # TEXT until next special or newline
        start = self.i
        parts = []
        while self.i < self.n and self.peek() not in SPECIAL_CHARS:
            parts.append(self.peek())
            self.advance(1)
        return Token(TokenType.TEXT, ''.join(parts), start)

    def tokenize(self):
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == TokenType.EOF:
                break
        return tokens