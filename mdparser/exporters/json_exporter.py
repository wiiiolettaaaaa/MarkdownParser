from ..visitor import BaseVisitor
from ..ast_nodes import (
    Document, Heading, Paragraph, Text, Bold, Italic, Link,
    UnorderedList, OrderedList, ListItem, CodeBlock, BlockQuote
)

class JsonExporter(BaseVisitor):
    def visit_Document(self, node: Document):
        return {"type": "Document", "children": [self.visit(ch) for ch in node.children]}

    def visit_Heading(self, node: Heading):
        return {"type": "Heading", "level": node.level, "inline": [self.visit(ch) for ch in node.inline]}

    def visit_Paragraph(self, node: Paragraph):
        return {"type": "Paragraph", "inline": [self.visit(ch) for ch in node.inline]}

    def visit_Text(self, node: Text):
        return {"type": "Text", "value": node.value}

    def visit_Bold(self, node: Bold):
        return {"type": "Bold", "inline": [self.visit(ch) for ch in node.inline]}

    def visit_Italic(self, node: Italic):
        return {"type": "Italic", "inline": [self.visit(ch) for ch in node.inline]}

    def visit_Link(self, node: Link):
        return {"type": "Link", "href": node.href, "inline": [self.visit(ch) for ch in node.inline]}

    def visit_UnorderedList(self, node: UnorderedList):
        return {"type": "UnorderedList", "items": [self.visit(it) for it in node.items]}

    def visit_OrderedList(self, node: OrderedList):
        return {"type": "OrderedList", "items": [self.visit(it) for it in node.items]}

    def visit_ListItem(self, node: ListItem):
        return {"type": "ListItem", "inline": [self.visit(ch) for ch in node.inline]}

    def visit_CodeBlock(self, node: CodeBlock):
        return {"type": "CodeBlock", "language": node.language, "code": node.code}

    def visit_BlockQuote(self, node: BlockQuote):
        return {"type": "BlockQuote", "children": [self.visit(ch) for ch in node.children]}

    def generic_visit(self, node):
        # fallback
        return {"type": node.__class__.__name__}