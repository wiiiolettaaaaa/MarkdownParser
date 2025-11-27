from .tokens import TokenType
from .factory import NodeFactory
from .inline_parser import parse_inline_from_text

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens, factory: NodeFactory = None):
        self.tokens = tokens
        self.i = 0
        self.n = len(tokens)
        self.factory = factory or NodeFactory()

    def peek(self, k=0):
        idx = self.i + k
        if idx < self.n:
            return self.tokens[idx]
        return self.tokens[-1]

    def advance(self, k=1):
        self.i = min(self.i + k, self.n-1)
        return self.peek()

    def accept(self, ttype):
        if self.peek().type == ttype:
            tok = self.peek()
            self.advance(1)
            return tok
        return None

    def expect(self, ttype):
        tok = self.accept(ttype)
        if not tok:
            raise ParserError(f'Expected {ttype} at pos {self.peek().pos}, got {self.peek().type}')
        return tok

    def parse(self):
        children = []
        while self.peek().type != TokenType.EOF:
            if self.peek().type == TokenType.NEWLINE:
                self.advance(1); continue
            node = self.parse_block()
            if node:
                children.append(node)
        return self.factory.document(children)

    def parse_block(self):
        tok = self.peek()
        if tok.type == TokenType.HASH:
            return self.parse_heading()
        if tok.type == TokenType.DASH:
            return self.parse_unordered_list()
        if tok.type == TokenType.NUMBER:
            return self.parse_ordered_list()
        if tok.type == TokenType.CODE_FENCE:
            return self.parse_code_fence()
        if tok.type == TokenType.GT:
            return self.parse_blockquote()
        # else paragraph
        return self.parse_paragraph()

    def parse_heading(self):
        tok = self.accept(TokenType.HASH)
        level = len(tok.value)
        inline_text = self.collect_line_text()
        inline_nodes = parse_inline_from_text(inline_text)
        if self.peek().type == TokenType.NEWLINE:
            self.advance(1)
        return self.factory.heading(level=level, inline=inline_nodes)

    def parse_unordered_list(self):
        items = []
        while self.peek().type == TokenType.DASH:
            self.advance(1)
            content = self.collect_line_text()
            inline_nodes = parse_inline_from_text(content)
            items.append(self.factory.list_item(inline_nodes))
            if self.peek().type == TokenType.NEWLINE:
                self.advance(1)
            else:
                break
        return self.factory.unordered_list(items)

    def parse_ordered_list(self):
        items = []
        while self.peek().type == TokenType.NUMBER:
            self.advance(1)  # consume number token like '1.'
            content = self.collect_line_text()
            inline_nodes = parse_inline_from_text(content)
            items.append(self.factory.list_item(inline_nodes))
            if self.peek().type == TokenType.NEWLINE:
                self.advance(1)
            else:
                break
        return self.factory.ordered_list(items)

    def parse_code_fence(self):
        # CODE_FENCE token stores optional language
        tok = self.accept(TokenType.CODE_FENCE)
        lang = tok.value or ''
        # collect until next CODE_FENCE token
        code_lines = []
        while self.peek().type != TokenType.CODE_FENCE and self.peek().type != TokenType.EOF:
            # include raw token values with newlines
            if self.peek().type == TokenType.NEWLINE:
                code_lines.append('\n')
                self.advance(1)
                continue
            code_lines.append(self.peek().value)
            self.advance(1)
        # consume closing fence if present
        if self.peek().type == TokenType.CODE_FENCE:
            self.advance(1)
        code = ''.join(code_lines)
        # consume trailing newline
        if self.peek().type == TokenType.NEWLINE:
            self.advance(1)
        return self.factory.code_block(language=lang, code=code)

    def parse_blockquote(self):
        # consecutive lines starting with GT are treated as quote body
        children = []
        while self.peek().type == TokenType.GT:
            self.advance(1)  # consume '>'
            # collect line text for this quote line and parse as blocks recursively
            line = self.collect_line_text()
            # parse the line as markdown fragment (reuse Parser on tokens from line)
            # Simple approach: treat line as paragraph inline
            inline_nodes = parse_inline_from_text(line)
            children.append(self.factory.paragraph(inline_nodes))
            if self.peek().type == TokenType.NEWLINE:
                self.advance(1)
            else:
                break
        return self.factory.block_quote(children)

    def parse_paragraph(self):
        parts = []
        while self.peek().type not in (TokenType.EOF, TokenType.NEWLINE, TokenType.HASH, TokenType.DASH,
                                      TokenType.NUMBER, TokenType.CODE_FENCE, TokenType.GT):
            if self.peek().type == TokenType.TEXT:
                parts.append(self.peek().value)
                self.advance(1)
            else:
                t = self.peek()
                # translate punctuation tokens back to literal
                if t.type == TokenType.LBRACKET:
                    parts.append('[')
                elif t.type == TokenType.RBRACKET:
                    parts.append(']')
                elif t.type == TokenType.LPAREN:
                    parts.append('(')
                elif t.type == TokenType.RPAREN:
                    parts.append(')')
                elif t.type == TokenType.STAR:
                    parts.append('*')
                elif t.type == TokenType.DOUBLE_STAR:
                    parts.append('**')
                else:
                    parts.append(t.value)
                self.advance(1)
        if self.peek().type == TokenType.NEWLINE:
            self.advance(1)
        joined = ''.join(parts).strip()
        inline_nodes = parse_inline_from_text(joined)
        return self.factory.paragraph(inline_nodes)

    def collect_line_text(self):
        parts = []
        while self.peek().type not in (TokenType.NEWLINE, TokenType.EOF):
            parts.append(self.peek().value)
            self.advance(1)
        return ''.join(parts).strip()