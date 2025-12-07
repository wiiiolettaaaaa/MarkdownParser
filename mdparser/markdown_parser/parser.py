from __future__ import annotations
from typing import List, Optional, Tuple
from dataclasses import dataclass

# Імпортуємо лексер і AST-вузли
from mdparser.markdown_parser.lexer import Token, TokenType, Lexer
from mdparser.markdown_parser.ast_nodes import (
    Document, Heading, Paragraph, Text, Bold, Italic, Link, ListBlock,
    ListItem, CodeBlock, CodeSpan, BlockQuote, HorizontalRule, mk_paragraph
)

# -----------------------------------------------------------
# TokenStream - обгортка навколо списку токенів (зручні методи)
# -----------------------------------------------------------

class ParseError(Exception):
    pass

@dataclass
class TokenStream:
    tokens: List[Token]
    pos: int = 0

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        # Повертаємо EOF-style token
        return Token(TokenType.EOF, "", self.pos)

    def next(self) -> Token:
        tok = self.peek()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def expect(self, ttype: TokenType) -> Token:
        tok = self.peek()
        if tok.type != ttype:
            raise ParseError(f"Expected token {ttype} but got {tok.type} (value={tok.value!r}) at pos {tok.position}")
        return self.next()

    def match(self, *ttypes: TokenType) -> bool:
        tok = self.peek()
        return tok.type in ttypes

    def eof(self) -> bool:
        return self.peek().type == TokenType.EOF


# -----------------------------------------------------------
# Parser
# -----------------------------------------------------------

class Parser:
    """
    Recursive-descent parser for a subset of Markdown.
    """

    def __init__(self, tokens: list[Token]):
        """
        Ініціалізація парсера зі списком токенів.
        """
        if not isinstance(tokens, list) or not all(isinstance(t, Token) for t in tokens):
            raise TypeError(f"Parser expects list of Tokens, got {type(tokens)}")
        self.tokens = TokenStream(tokens)

    def _is_hr_line(self) -> bool:
        """
        Перевіряє, чи поточна лінія — горизонтальна лінія (--- або ***).
        """
        count_dash = 0
        count_star = 0
        pos = self.tokens.pos
        while not self.tokens.eof() and self.tokens.peek().type in (TokenType.DASH, TokenType.STAR):
            tok = self.tokens.next()
            if tok.type == TokenType.DASH:
                count_dash += 1
            elif tok.type == TokenType.STAR:
                count_star += 1

        # HR мінімум 3 символи одного типу
        if count_dash >= 3 or count_star >= 3:
            return True
        self.tokens.pos = pos  # відкотимо позицію, якщо це не HR
        return False
    # -------------------------------------------------------
    # Верхній рівень: parse whole document
    # -------------------------------------------------------
    def parse(self) -> Document:
        blocks: List = []
        # Skip leading newlines
        while self.tokens.match(TokenType.NEWLINE):
            self.tokens.next()
        while not self.tokens.eof():
            block = self.parse_block()
            if block is not None:
                blocks.append(block)
            # skip trailing newlines between blocks
            while self.tokens.match(TokenType.NEWLINE):
                self.tokens.next()
        return Document(blocks=blocks)

    # -------------------------------------------------------
    # Parse a block-level element
    # -------------------------------------------------------
    def parse_block(self):
        tok = self.tokens.peek()

        # Heading: starts with HASH (one or multiple)
        if tok.type == TokenType.HASH:
            return self.parse_heading()

        # Fenced code block: triple backtick represented as BACKTICK repeated?
        # Our lexer returns BACKTICK for single backtick; fenced code detection relies on text pattern in lexer
        # For simplicity, treat a line starting with three backticks as start of codeblock:
        if tok.type == TokenType.BACKTICK:
            # Check if there are multiple backticks contiguous (lexer returns one backtick token per `)
            # If next two tokens are also BACKTICK, assume fence
            if self._is_open_fence():
                return self.parse_fenced_codeblock()
            # else fallthrough to paragraph (inline code)

        # Blockquote: leading '>' - we used 'DASH' for -, but blockquote is not tokenized specially in lexer.
        # To keep backward compatibility, detect lines starting with '>' in TEXT via the value.
        if tok.type == TokenType.TEXT and tok.value.startswith('>'):
            return self.parse_blockquote()

        # Horizontal rule: a line starting with three or more '-' or '*' may be tokenized as multiple DASH/STAR tokens.
        if self._is_hr_line():
            # consume until newline
            while not self.tokens.eof() and not self.tokens.match(TokenType.NEWLINE):
                self.tokens.next()
            # consume newline if present
            if self.tokens.match(TokenType.NEWLINE):
                self.tokens.next()
            return HorizontalRule()

        # List items: '-' or NUMBER + '.' as NUMBER token
        if tok.type == TokenType.DASH or tok.type == TokenType.NUMBER:
            return self.parse_list()

        # Otherwise paragraph (one or more lines merged)
        return self.parse_paragraph()

    # -------------------------------------------------------
    # Parse heading
    # "#" repeated one or more times at beginning of line
    # -------------------------------------------------------
    def parse_heading(self) -> Heading:
        # Count continuous HASH tokens at start of line
        level = 0
        # We may have multiple HASH tokens representing multiple '#' characters
        while self.tokens.match(TokenType.HASH):
            # Each HASH token from lexer is a single '#', so increment level per token
            self.tokens.next()
            level += 1
        # optional spaces
        if self.tokens.match(TokenType.SPACE):
            self.tokens.next()
        # then rest of line as inline content until NEWLINE
        inlines = self.parse_inline_until(TokenType.NEWLINE)
        # consume newline if present
        if self.tokens.match(TokenType.NEWLINE):
            self.tokens.next()
        return Heading(level=level, inlines=inlines)

    # -------------------------------------------------------
    # Parse fenced code block: starting with three backticks on its own line
    # We detect three consecutive BACKTICK tokens as fence open.
    # -------------------------------------------------------
    def _is_open_fence(self) -> bool:
        # Ensure at least 3 backtick tokens in a row before newline
        pos = self.tokens.pos
        count = 0
        while pos < len(self.tokens.tokens) and self.tokens.tokens[pos].type == TokenType.BACKTICK:
            count += 1
            pos += 1
        return count >= 3

    def parse_fenced_codeblock(self) -> CodeBlock:
        # consume fence (count backticks)
        fence_count = 0
        while self.tokens.match(TokenType.BACKTICK):
            self.tokens.next()
            fence_count += 1
        # optional language identifier as TEXT tokens until NEWLINE
        lang_parts = []
        while not self.tokens.eof() and not self.tokens.match(TokenType.NEWLINE):
            t = self.tokens.next()
            if t.type == TokenType.TEXT or t.type == TokenType.SPACE:
                lang_parts.append(t.value)
            else:
                lang_parts.append(t.value)
        lang = ''.join(lang_parts).strip() or None
        # consume newline
        if self.tokens.match(TokenType.NEWLINE):
            self.tokens.next()
        # collect code lines until we find closing fence of same length
        code_parts: List[str] = []
        while not self.tokens.eof():
            # check for potential closing fence
            if self._is_close_fence(fence_count):
                # consume fence tokens
                for _ in range(fence_count):
                    self.tokens.next()
                # swallow rest of line until newline
                while not self.tokens.eof() and not self.tokens.match(TokenType.NEWLINE):
                    self.tokens.next()
                if self.tokens.match(TokenType.NEWLINE):
                    self.tokens.next()
                break
            # otherwise collect raw token values respecting newlines
            t = self.tokens.next()
            code_parts.append(t.value)
        code_text = ''.join(code_parts)
        return CodeBlock(code=code_text, language=lang)

    def _is_close_fence(self, fence_count: int) -> bool:
        pos = self.tokens.pos
        for i in range(fence_count):
            if pos + i >= len(self.tokens.tokens) or self.tokens.tokens[pos + i].type != TokenType.BACKTICK:
                return False
        return True

    # -------------------------------------------------------
    # Parse blockquote lines starting with '>' at beginning of line.
    # Our lexer currently includes '>' inside TEXT tokens; handle both cases.
    # -------------------------------------------------------
    def parse_blockquote(self) -> BlockQuote:
        children: List[Paragraph] = []

        while not self.tokens.eof():
            tok = self.tokens.peek()
            if tok.type != TokenType.TEXT or not tok.value.startswith('>'):
                break

            # Збираємо всі рядки blockquote в один буфер
            buffer_lines: List[str] = []
            while not self.tokens.eof():
                line_tok = self.tokens.peek()
                if line_tok.type != TokenType.TEXT or not line_tok.value.startswith('>'):
                    break
                line = line_tok.value[1:]  # видаляємо '>'
                if line.startswith(" "):
                    line = line[1:]
                buffer_lines.append(line)
                self.tokens.next()
                if self.tokens.match(TokenType.NEWLINE):
                    self.tokens.next()

            paragraph_text = "\n".join(buffer_lines)
            # Створюємо новий Lexer/Parser для inline розмітки
            inline_tokens = Lexer(paragraph_text).tokenize()
            inline_parser = Parser([])
            inline_parser.tokens = TokenStream(inline_tokens)
            inlines = inline_parser.parse_inline_until(TokenType.EOF)
            children.append(Paragraph(inlines=inlines))

        return BlockQuote(children=children)



    # -------------------------------------------------------
    # Parse lists (ordered and unordered). Handles consecutive list items.
    # Each list item consumes tokens up to newline; nested lists not fully implemented,
    # but paragraph-level inlines are parsed in list items.
    # -------------------------------------------------------
    def parse_list(self) -> ListBlock:
        items: List[ListItem] = []
        ordered = False
        while not self.tokens.eof():
            tok = self.tokens.peek()
            if tok.type == TokenType.DASH:
                # unordered
                self.tokens.next()
                # optional space
                if self.tokens.match(TokenType.SPACE):
                    self.tokens.next()
                inlines = self.parse_inline_until(TokenType.NEWLINE)
                # consume newline if present
                if self.tokens.match(TokenType.NEWLINE):
                    self.tokens.next()
                items.append(ListItem(children=[Paragraph(inlines=inlines)]))
                continue
            elif tok.type == TokenType.NUMBER:
                # ordered (e.g., "1.")
                ordered = True
                self.tokens.next()  # consume number token
                if self.tokens.match(TokenType.SPACE):
                    self.tokens.next()
                inlines = self.parse_inline_until(TokenType.NEWLINE)
                if self.tokens.match(TokenType.NEWLINE):
                    self.tokens.next()
                items.append(ListItem(children=[Paragraph(inlines=inlines)]))
                continue
            else:
                break
        return ListBlock(items=items, ordered=ordered)

    # -------------------------------------------------------
    # Parse paragraph: one or more lines joined until blank line or block-start token.
    # -------------------------------------------------------
    def parse_paragraph(self) -> Paragraph:
        inlines: List = []
        first = True
        while not self.tokens.eof():
            # stop when next block-start token encountered at line start
            if self._is_block_start_lookahead():
                break
            # parse inline content until newline
            part = self.parse_inline_until(TokenType.NEWLINE)
            inlines.extend(part)
            # if newline present, consume it and check for blank line (paragraph boundary)
            if self.tokens.match(TokenType.NEWLINE):
                # consume one newline
                self.tokens.next()
                # if next token is also NEWLINE -> paragraph end (we'll consume in outer loop)
                if self.tokens.match(TokenType.NEWLINE):
                    # don't consume second here; outer parse() consumes continuous newlines
                    break
                # else continue: soft line break => insert space
                inlines.append(Text(" "))
                continue
            else:
                break
        return Paragraph(inlines=inlines)

    def _is_block_start_lookahead(self) -> bool:
        """
        Determines if upcoming tokens start a block-level element. This helps to
        decide paragraph termination when encountering tokens like HASH, DASH, NUMBER, BACKTICK fences, etc.
        """
        tok = self.tokens.peek()
        if tok.type in (TokenType.HASH, TokenType.DASH, TokenType.NUMBER, TokenType.BACKTICK):
            # If BACKTICK is fence (>=3), treat as block start
            if tok.type == TokenType.BACKTICK:
                return self._is_open_fence()
            return True
        # Additionally, if TEXT token begins with '>' treat as blockquote
        if tok.type == TokenType.TEXT and tok.value.startswith('>'):
            return True
        # horizontal rule: sequence of '-' or '*' tokens at line start; we approximate by looking at text
        if tok.type == TokenType.TEXT and tok.value.strip().startswith('---'):
            return True
        return False

    # -------------------------------------------------------
    # Inline parsing helpers
    # parse_inline_until(stop_token_type): parse inlines until stop_type encountered (do not consume stop token).
    # Supports nested inline constructs.
    # -------------------------------------------------------
    def parse_inline_until(self, stop_token_type: TokenType) -> List:
        nodes: List = []
        while not self.tokens.eof() and not self.tokens.match(stop_token_type):
            tok = self.tokens.peek()
            if tok.type == TokenType.DOUBLE_STAR:
                nodes.append(self.parse_bold())
                continue
            if tok.type == TokenType.STAR:
                # could be list marker or italic depending on context; here we treat as italic if inline
                # if star at start of line and followed by space => list; but this function is called after handling lists
                nodes.append(self.parse_italic())
                continue
            if tok.type == TokenType.UNDERSCORE:
                nodes.append(self.parse_italic())
                continue
            if tok.type == TokenType.BACKTICK:
                # if three backticks => should be fence handled at block-level, so here it's codespan
                if self._is_open_fence():
                    # if we encounter a fence within paragraph (rare), break to let block parser handle
                    break
                nodes.append(self.parse_codespan())
                continue
            if tok.type == TokenType.LBRACKET:
                nodes.append(self.parse_link())
                continue
            if tok.type == TokenType.TEXT:
                nodes.append(Text(self.tokens.next().value))
                continue
            if tok.type == TokenType.SPACE:
                # preserve spaces as Text nodes (parser merges them)
                nodes.append(Text(self.tokens.next().value))
                continue
            # fallback: consume token as text
            nodes.append(Text(self.tokens.next().value))
        return nodes

    # -------------------------------------------------------
    # parse bold: **...**, lexer emits DOUBLE_STAR token for '**'
    # -------------------------------------------------------
    def parse_bold(self) -> Bold:
        # consume opening **
        if not self.tokens.match(TokenType.DOUBLE_STAR):
            # defensive: if there's single STAR but we expected bold, fallback
            self.tokens.next()
            return Bold(children=[Text("")])
        self.tokens.next()
        children: List = []
        while not self.tokens.eof() and not self.tokens.match(TokenType.DOUBLE_STAR) and not self.tokens.match(TokenType.NEWLINE):
            if self.tokens.match(TokenType.STAR):
                children.append(self.parse_italic())
            elif self.tokens.match(TokenType.LBRACKET):
                children.append(self.parse_link())
            elif self.tokens.match(TokenType.BACKTICK):
                children.append(self.parse_codespan())
            elif self.tokens.match(TokenType.TEXT) or self.tokens.match(TokenType.SPACE):
                t = self.tokens.next()
                children.append(Text(t.value))
            else:
                children.append(Text(self.tokens.next().value))
        # consume closing **
        if self.tokens.match(TokenType.DOUBLE_STAR):
            self.tokens.next()
        return Bold(children=children)

    # -------------------------------------------------------
    # parse italic: *...* or _..._
    # -------------------------------------------------------
    def parse_italic(self) -> Italic:
        # opening token may be STAR or UNDERSCORE
        opener = self.tokens.next()
        children: List = []
        while not self.tokens.eof() and not self.tokens.match(opener.type) and not self.tokens.match(TokenType.NEWLINE):
            if self.tokens.match(TokenType.DOUBLE_STAR):
                children.append(self.parse_bold())
            elif self.tokens.match(TokenType.BACKTICK):
                children.append(self.parse_codespan())
            elif self.tokens.match(TokenType.LBRACKET):
                children.append(self.parse_link())
            elif self.tokens.match(TokenType.TEXT) or self.tokens.match(TokenType.SPACE):
                t = self.tokens.next()
                children.append(Text(t.value))
            else:
                children.append(Text(self.tokens.next().value))
        # closing token
        if self.tokens.match(opener.type):
            self.tokens.next()
        return Italic(children=children)

    # -------------------------------------------------------
    # parse codespan `inline`
    # -------------------------------------------------------
    def parse_codespan(self) -> CodeSpan:
        # determine number of backticks delimiting the span (lexer returns one token per backtick)
        # count consecutive BACKTICK tokens
        count = 0
        while self.tokens.match(TokenType.BACKTICK):
            self.tokens.next()
            count += 1
        # collect tokens until we see same number of backticks again
        parts: List[str] = []
        while not self.tokens.eof():
            # check next sequence for closing
            if self._peek_backtick_sequence(count):
                # consume closing sequence
                for _ in range(count):
                    self.tokens.next()
                break
            t = self.tokens.next()
            parts.append(t.value)
        return CodeSpan(code=''.join(parts).strip())

    def _peek_backtick_sequence(self, count: int) -> bool:
        pos = self.tokens.pos
        for i in range(count):
            if pos + i >= len(self.tokens.tokens) or self.tokens.tokens[pos + i].type != TokenType.BACKTICK:
                return False
        return True

    # -------------------------------------------------------
    # parse link: [text](url) or reference-like; we support inline links
    # -------------------------------------------------------
    def parse_link(self) -> Link:
        # consume '['
        self.tokens.expect(TokenType.LBRACKET)
        text_nodes: List = []
        # parse until closing ']'
        while not self.tokens.eof() and not self.tokens.match(TokenType.RBRACKET):
            if self.tokens.match(TokenType.DOUBLE_STAR):
                text_nodes.append(self.parse_bold())
            elif self.tokens.match(TokenType.STAR) or self.tokens.match(TokenType.UNDERSCORE):
                text_nodes.append(self.parse_italic())
            elif self.tokens.match(TokenType.BACKTICK):
                text_nodes.append(self.parse_codespan())
            elif self.tokens.match(TokenType.TEXT) or self.tokens.match(TokenType.SPACE):
                t = self.tokens.next()
                text_nodes.append(Text(t.value))
            else:
                text_nodes.append(Text(self.tokens.next().value))
        # closing bracket
        self.tokens.expect(TokenType.RBRACKET)
        url = ""
        # if following LPAREN, gather URL until RPAREN
        if self.tokens.match(TokenType.LPAREN):
            self.tokens.next()
            url_parts: List[str] = []
            while not self.tokens.eof() and not self.tokens.match(TokenType.RPAREN):
                t = self.tokens.next()
                url_parts.append(t.value)
            # consume RPAREN
            if self.tokens.match(TokenType.RPAREN):
                self.tokens.next()
            url = ''.join(url_parts).strip()
        return Link(text_nodes=text_nodes, url=url)

# -----------------------------------------------------------
# Quick convenience API
# -----------------------------------------------------------

# -------------------------------
# parse_markdown: текст -> Document
# -------------------------------
from mdparser.markdown_parser.lexer import Lexer

def parse_markdown(text: str) -> Document:
    tokens = Lexer(text).tokenize()
    parser = Parser(tokens)
    return parser.parse()

