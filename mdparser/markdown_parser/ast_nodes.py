from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Protocol, Any, Optional, Dict, Callable
import json


# -----------------------------------------------------------
# Visitor Protocol
# -----------------------------------------------------------

class Visitor(Protocol):
    def visit_document(self, node: "Document") -> Any: ...
    def visit_heading(self, node: "Heading") -> Any: ...
    def visit_paragraph(self, node: "Paragraph") -> Any: ...
    def visit_text(self, node: "Text") -> Any: ...
    def visit_bold(self, node: "Bold") -> Any: ...
    def visit_italic(self, node: "Italic") -> Any: ...
    def visit_link(self, node: "Link") -> Any: ...
    def visit_list(self, node: "ListBlock") -> Any: ...
    def visit_list_item(self, node: "ListItem") -> Any: ...
    def visit_codeblock(self, node: "CodeBlock") -> Any: ...
    def visit_codespan(self, node: "CodeSpan") -> Any: ...
    def visit_blockquote(self, node: "BlockQuote") -> Any: ...
    def visit_hr(self, node: "HorizontalRule") -> Any: ...


# -----------------------------------------------------------
# Base Node Classes
# -----------------------------------------------------------

@dataclass
class Node:
    def accept(self, visitor: Visitor) -> Any:
        raise NotImplementedError("accept not implemented")

    def to_dict(self) -> Dict[str, Any]:
        """
        Простий спосіб серіалізувати AST для кешу / golden tests.
        Override якщо треба складніші структури.
        """
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        raise NotImplementedError


# Inline and Block marker classes (for typing)
class Inline(Node):
    pass

class Block(Node):
    pass


# -----------------------------------------------------------
# Inline Nodes
# -----------------------------------------------------------

@dataclass
class Text(Inline):
    text: str

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_text(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Text", "text": self.text}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Text":
        return Text(data["text"])


@dataclass
class CodeSpan(Inline):
    code: str

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_codespan(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "CodeSpan", "code": self.code}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeSpan":
        return CodeSpan(data["code"])


@dataclass
class Bold(Inline):
    children: List[Inline] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_bold(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Bold", "children": [c.to_dict() for c in self.children]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bold":
        children = [_node_from_dict(c) for c in data.get("children", [])]
        return Bold(children)


@dataclass
class Italic(Inline):
    children: List[Inline] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_italic(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Italic", "children": [c.to_dict() for c in self.children]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Italic":
        children = [_node_from_dict(c) for c in data.get("children", [])]
        return Italic(children)


@dataclass
class Link(Inline):
    text_nodes: List[Inline] = field(default_factory=list)
    url: str = ""
    title: Optional[str] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_link(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Link",
            "text_nodes": [n.to_dict() for n in self.text_nodes],
            "url": self.url,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Link":
        nodes = [_node_from_dict(n) for n in data.get("text_nodes", [])]
        return Link(nodes, data.get("url", ""), data.get("title"))


# -----------------------------------------------------------
# Block Nodes
# -----------------------------------------------------------

@dataclass
class Paragraph(Block):
    inlines: List[Inline] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_paragraph(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Paragraph", "inlines": [i.to_dict() for i in self.inlines]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paragraph":
        inlines = [_node_from_dict(i) for i in data.get("inlines", [])]
        return Paragraph(inlines)


@dataclass
class Heading(Block):
    level: int
    inlines: List[Inline] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_heading(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Heading", "level": self.level, "inlines": [i.to_dict() for i in self.inlines]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Heading":
        inlines = [_node_from_dict(i) for i in data.get("inlines", [])]
        return Heading(level=data.get("level", 1), inlines=inlines)


@dataclass
class CodeBlock(Block):
    code: str
    language: Optional[str] = None

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_codeblock(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "CodeBlock", "code": self.code, "language": self.language}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeBlock":
        return CodeBlock(code=data.get("code", ""), language=data.get("language"))


@dataclass
class BlockQuote(Block):
    children: List[Block] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_blockquote(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "BlockQuote", "children": [c.to_dict() for c in self.children]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockQuote":
        children = [_node_from_dict(c) for c in data.get("children", [])]
        return BlockQuote(children)


@dataclass
class ListItem(Block):
    children: List[Block] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_list_item(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "ListItem", "children": [c.to_dict() for c in self.children]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListItem":
        children = [_node_from_dict(c) for c in data.get("children", [])]
        return ListItem(children)


@dataclass
class ListBlock(Block):
    items: List[ListItem] = field(default_factory=list)
    ordered: bool = False

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_list(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "ListBlock", "ordered": self.ordered, "items": [i.to_dict() for i in self.items]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListBlock":
        items = [_node_from_dict(i) for i in data.get("items", [])]
        # items should map to ListItem instances
        items = [it if isinstance(it, ListItem) else ListItem([it]) for it in items]
        return ListBlock(items=items, ordered=data.get("ordered", False))


@dataclass
class HorizontalRule(Block):
    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_hr(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "HorizontalRule"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HorizontalRule":
        return HorizontalRule()


@dataclass
class Document(Node):
    blocks: List[Block] = field(default_factory=list)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_document(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Document", "blocks": [b.to_dict() for b in self.blocks]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        blocks = [_node_from_dict(b) for b in data.get("blocks", [])]
        return Document(blocks)


# -----------------------------------------------------------
# Helper: deserialize node from dict
# -----------------------------------------------------------

_NODE_TYPE_MAP: Dict[str, Callable[[Dict[str, Any]], Node]] = {
    "Text": Text.from_dict,
    "CodeSpan": CodeSpan.from_dict,
    "Bold": Bold.from_dict,
    "Italic": Italic.from_dict,
    "Link": Link.from_dict,
    "Paragraph": Paragraph.from_dict,
    "Heading": Heading.from_dict,
    "CodeBlock": CodeBlock.from_dict,
    "BlockQuote": BlockQuote.from_dict,
    "ListItem": ListItem.from_dict,
    "ListBlock": ListBlock.from_dict,
    "HorizontalRule": HorizontalRule.from_dict,
    "Document": Document.from_dict,
}


def _node_from_dict(data: Dict[str, Any]) -> Node:
    t = data.get("type")
    if not t:
        raise ValueError("Node dict missing 'type'")
    if t not in _NODE_TYPE_MAP:
        raise ValueError(f"Unknown node type: {t}")
    return _NODE_TYPE_MAP[t](data)


# -----------------------------------------------------------
# Factory helpers (convenience functions)
# -----------------------------------------------------------

def mk_text(s: str) -> Text:
    return Text(s)

def mk_bold(*children: Inline) -> Bold:
    return Bold(list(children))

def mk_italic(*children: Inline) -> Italic:
    return Italic(list(children))

def mk_link(url: str, *text_nodes: Inline, title: Optional[str]=None) -> Link:
    return Link(list(text_nodes), url, title)

def mk_paragraph(*inlines: Inline) -> Paragraph:
    return Paragraph(list(inlines))

def mk_heading(level: int, *inlines: Inline) -> Heading:
    return Heading(level=level, inlines=list(inlines))

def mk_codeblock(code: str, language: Optional[str]=None) -> CodeBlock:
    return CodeBlock(code=code, language=language)

def mk_list(*items: ListItem, ordered: bool=False) -> ListBlock:
    return ListBlock(items=list(items), ordered=ordered)


# -----------------------------------------------------------
# Utility: pretty print AST as JSON (for golden tests / debugging)
# -----------------------------------------------------------

def ast_to_json(node: Node, indent: int=2) -> str:
    return json.dumps(node.to_dict(), ensure_ascii=False, indent=indent)


# -----------------------------------------------------------
# Small self-test (manual)
# -----------------------------------------------------------

if __name__ == "__main__":
    # Build a tiny AST and print JSON
    doc = Document(blocks=[
        Heading(level=1, inlines=[Text("Hello World")]),
        Paragraph(inlines=[Text("This is "), Bold([Text("bold")]), Text(" text.")]),
        ListBlock(items=[ListItem([Paragraph([Text("item1")])]), ListItem([Paragraph([Text("item2")])])]),
    ])
    print(ast_to_json(doc))