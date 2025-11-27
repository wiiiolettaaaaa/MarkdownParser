from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    HASH = auto()         # '#', '##', ...
    DASH = auto()         # '-'
    STAR = auto()         # '*'
    DOUBLE_STAR = auto()  # '**'
    LBRACKET = auto()     # '['
    RBRACKET = auto()     # ']'
    LPAREN = auto()       # '('
    RPAREN = auto()       # ')'
    NEWLINE = auto()      # '\n'
    TEXT = auto()         # plain text
    EOF = auto()
    CODE_FENCE = auto()   # ```
    NUMBER = auto()       # ordered list marker like '1.'
    GT = auto()           # '>' blockquote

@dataclass
class Token:
    type: TokenType
    value: str
    pos: int = 0

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, pos={self.pos})"