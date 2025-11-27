from dataclasses import dataclass
from typing import List

class Node:
    pass

@dataclass
class Document(Node):
    children: List[Node]

@dataclass
class Heading(Node):
    level: int
    inline: List[Node]

@dataclass
class Paragraph(Node):
    inline: List[Node]

@dataclass
class Text(Node):
    value: str

@dataclass
class Bold(Node):
    inline: List[Node]

@dataclass
class Italic(Node):
    inline: List[Node]

@dataclass
class Link(Node):
    inline: List[Node]
    href: str

@dataclass
class ListItem(Node):
    inline: List[Node]

@dataclass
class UnorderedList(Node):
    items: List[ListItem]

@dataclass
class OrderedList(Node):
    items: List[ListItem]

@dataclass
class CodeBlock(Node):
    language: str
    code: str

@dataclass
class BlockQuote(Node):
    children: List[Node]