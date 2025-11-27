from .ast_nodes import (
    Document, Heading, Paragraph, Text, Bold, Italic, Link,
    ListItem, UnorderedList, OrderedList, CodeBlock, BlockQuote
)

class NodeFactory:
    def document(self, children):
        return Document(children=children)
    def heading(self, level, inline):
        return Heading(level=level, inline=inline)
    def paragraph(self, inline):
        return Paragraph(inline=inline)
    def text(self, value):
        return Text(value=value)
    def bold(self, inline):
        return Bold(inline=inline)
    def italic(self, inline):
        return Italic(inline=inline)
    def link(self, inline, href):
        return Link(inline=inline, href=href)
    def list_item(self, inline):
        return ListItem(inline=inline)
    def unordered_list(self, items):
        return UnorderedList(items=items)
    def ordered_list(self, items):
        return OrderedList(items=items)
    def code_block(self, language, code):
        return CodeBlock(language=language, code=code)
    def block_quote(self, children):
        return BlockQuote(children=children)