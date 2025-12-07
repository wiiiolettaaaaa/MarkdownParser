from __future__ import annotations
from typing import List, Optional, Any
import html as html_module
import json
from mdparser.markdown_parser.ast_nodes import (
    Document, Paragraph, Heading, Text, Bold, Italic, Link,
    ListBlock, ListItem, CodeBlock, CodeSpan, BlockQuote, HorizontalRule,
    Visitor, Node
)


# -----------------------------------------------------------
# Helper: safe escape for HTML content
# -----------------------------------------------------------
def escape_html(s: str) -> str:
    return html_module.escape(s, quote=True)


# -----------------------------------------------------------
# Base Renderer (Visitor) - defines interface and helpers
# -----------------------------------------------------------
class BaseRenderer(Visitor):
    def render(self, node: Node) -> str:
        """Dispatch entrypoint"""
        node.accept(self)
        return self.get_output()

    def get_output(self) -> str:
        raise NotImplementedError


# -----------------------------------------------------------
# HTML Renderer
# -----------------------------------------------------------
class HTMLRenderer(BaseRenderer):
    def __init__(self, pretty: bool = True, indent_size: int = 2):
        self.pretty = pretty
        self.indent_size = indent_size
        self._parts: List[str] = []
        self._level = 0

    def _w(self, s: str):
        self._parts.append(s)

    def _w_indent(self, s: str):
        if self.pretty:
            self._parts.append(" " * (self.indent_size * self._level) + s)
        else:
            self._parts.append(s)

    def get_output(self) -> str:
        return ''.join(self._parts)

    # Document
    def visit_document(self, node: Document):
        for i, b in enumerate(node.blocks):
            b.accept(self)
            # extra newline between blocks for readability
            if self.pretty and i != len(node.blocks) - 1:
                self._w("\n")

    # Paragraph
    def visit_paragraph(self, node: Paragraph):
        self._w_indent("<p>")
        for child in node.inlines:
            child.accept(self)
        self._w("</p>")
        if self.pretty:
            self._w("\n")

    # Heading
    def visit_heading(self, node: Heading):
        level = max(1, min(6, node.level))
        self._w_indent(f"<h{level}>")
        for c in node.inlines:
            c.accept(self)
        self._w(f"</h{level}>")
        if self.pretty:
            self._w("\n")

    # Text
    def visit_text(self, node: Text):
        self._w(escape_html(node.text))

    # Bold
    def visit_bold(self, node: Bold):
        self._w("<strong>")
        for c in node.children:
            c.accept(self)
        self._w("</strong>")

    # Italic
    def visit_italic(self, node: Italic):
        self._w("<em>")
        for c in node.children:
            c.accept(self)
        self._w("</em>")

    # Link
    def visit_link(self, node: Link):
        href = escape_html(node.url or "")
        self._w(f'<a href="{href}">')
        for t in node.text_nodes:
            t.accept(self)
        self._w("</a>")

    # List
    def visit_list(self, node: ListBlock):
        tag = "ol" if node.ordered else "ul"
        self._w_indent(f"<{tag}>")
        if self.pretty:
            self._w("\n")
        self._level += 1
        for item in node.items:
            item.accept(self)
        self._level -= 1
        self._w_indent(f"</{tag}>")
        if self.pretty:
            self._w("\n")

    # List item
    def visit_list_item(self, node: ListItem):
        self._w_indent("<li>")
        # Render children — often a single Paragraph
        first = True
        for c in node.children:
            # If paragraph — render inline content only to avoid double <p> inside <li>
            if isinstance(c, Paragraph):
                for inl in c.inlines:
                    inl.accept(self)
            else:
                # nested block — new line + indentation
                if not first and self.pretty:
                    self._w("\n")
                c.accept(self)
            first = False
        self._w("</li>")
        if self.pretty:
            self._w("\n")

    # CodeBlock
    def visit_codeblock(self, node: CodeBlock):
        lang_attr = f' class="language-{escape_html(node.language)}"' if node.language else ""
        self._w_indent(f"<pre><code{lang_attr}>")
        # Preserve whitespace inside code block; escape html characters
        code_text = escape_html(node.code)
        # Avoid trimming user indentation
        self._w(code_text)
        self._w("</code></pre>")
        if self.pretty:
            self._w("\n")

    # CodeSpan
    def visit_codespan(self, node: CodeSpan):
        self._w("<code>")
        self._w(escape_html(node.code))
        self._w("</code>")

    # Blockquote
    def visit_blockquote(self, node: BlockQuote):
        self._w_indent("<blockquote>")
        if self.pretty:
            self._w("\n")
        self._level += 1
        for c in node.children:
            c.accept(self)
        self._level -= 1
        self._w_indent("</blockquote>")
        if self.pretty:
            self._w("\n")

    # Horizontal Rule
    def visit_hr(self, node: HorizontalRule):
        self._w_indent("<hr />")
        if self.pretty:
            self._w("\n")


# -----------------------------------------------------------
# Plain Text Renderer - useful for tests and snapshots
# -----------------------------------------------------------
class PlainTextRenderer(BaseRenderer):
    def __init__(self):
        self._parts: List[str] = []

    def get_output(self) -> str:
        return ''.join(self._parts)

    def visit_document(self, node: Document):
        for b in node.blocks:
            b.accept(self)
            self._parts.append("\n")

    def visit_paragraph(self, node: Paragraph):
        for inline in node.inlines:
            inline.accept(self)
        self._parts.append("\n\n")

    def visit_heading(self, node: Heading):
        hashes = "#" * node.level
        self._parts.append(hashes + " ")
        for inline in node.inlines:
            inline.accept(self)
        self._parts.append("\n\n")

    def visit_text(self, node: Text):
        self._parts.append(node.text)

    def visit_bold(self, node: Bold):
        self._parts.append("**")
        for c in node.children:
            c.accept(self)
        self._parts.append("**")

    def visit_italic(self, node: Italic):
        self._parts.append("*")
        for c in node.children:
            c.accept(self)
        self._parts.append("*")

    def visit_link(self, node: Link):
        text = []
        for i in node.text_nodes:
            if isinstance(i, Text):
                text.append(i.text)
            else:
                i.accept(self)
        text_str = ''.join(text)
        self._parts.append(f"[{text_str}]({node.url})")

    def visit_list(self, node: ListBlock):
        for i, it in enumerate(node.items, start=1):
            if node.ordered:
                prefix = f"{i}. "
            else:
                prefix = "- "
            self._parts.append(prefix)

            # items usually contain a Paragraph
            if it.children:
                first = it.children[0]
                if isinstance(first, Paragraph):
                    for inl in first.inlines:
                        inl.accept(self)
                else:
                    first.accept(self)

            self._parts.append("\n")

    def visit_list_item(self, node: ListItem):
        pass  # handled in visit_list

    def visit_codeblock(self, node: CodeBlock):
        lang = node.language or ""
        self._parts.append("```" + lang + "\n")
        self._parts.append(node.code)
        self._parts.append("\n```\n")

    def visit_codespan(self, node: CodeSpan):
        self._parts.append("`")
        self._parts.append(node.code)
        self._parts.append("`")

    def visit_blockquote(self, node: BlockQuote):
        for c in node.children:
            self._parts.append("> ")
            if isinstance(c, Paragraph):
                for inl in c.inlines:
                    inl.accept(self)
            else:
                c.accept(self)
            self._parts.append("\n")

    def visit_hr(self, node: HorizontalRule):
        self._parts.append("---\n")

    def _render_inlines(self, inlines: List[Any]) -> List[str]:
        collector: List[str] = []
        for i in inlines:
            if isinstance(i, Text):
                collector.append(i.text)
            elif isinstance(i, Bold):
                # flatten bold
                for c in i.children:
                    if isinstance(c, Text):
                        collector.append(c.text)
                    else:
                        collector.append(str(c))
            elif isinstance(i, Italic):
                for c in i.children:
                    if isinstance(c, Text):
                        collector.append(c.text)
                    else:
                        collector.append(str(c))
            elif isinstance(i, Link):
                collector.append(''.join(self._render_inlines(i.text_nodes)))
            else:
                collector.append(str(i))
        return collector


# -----------------------------------------------------------
# JSON Renderer (for golden master snapshots)
# -----------------------------------------------------------
class JSONRenderer(BaseRenderer):
    def __init__(self, indent: Optional[int] = 2):
        self.indent = indent
        self._json = None

    def get_output(self) -> str:
        return json.dumps(self._json, ensure_ascii=False, indent=self.indent)

    def visit_document(self, node: Document):
        self._json = node.to_dict()


# -----------------------------------------------------------
# Convenience factory functions
# -----------------------------------------------------------

def render_html(doc: Document, pretty: bool = True) -> str:
    r = HTMLRenderer(pretty=pretty)
    return r.render(doc)

def render_text(doc: Document) -> str:
    r = PlainTextRenderer()
    return r.render(doc)

def render_json(doc: Document, indent: Optional[int] = 2) -> str:
    r = JSONRenderer(indent=indent)
    return r.render(doc)


# -----------------------------------------------------------
# Quick manual test
# -----------------------------------------------------------
if __name__ == "__main__":
    # Minimal demonstration: build a small AST and render
    d = Document(blocks=[
        Heading(level=1, inlines=[Text("Hello")]),
        Paragraph(inlines=[Text("A "), Bold([Text("B")]), Text(" C")]),
        ListBlock(items=[ListItem(children=[Paragraph(inlines=[Text("one")])]),
                         ListItem(children=[Paragraph(inlines=[Text("two")])])], ordered=False),
        CodeBlock(code='print("x")', language='python'),
    ])
    print("=== HTML ===")
    print(render_html(d))
    print("=== TEXT ===")
    print(render_text(d))
    print("=== JSON ===")
    print(render_json(d))