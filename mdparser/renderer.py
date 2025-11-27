from .ast_nodes import (
    Document, Heading, Paragraph, Text, Bold, Italic, Link,
    UnorderedList, OrderedList, ListItem, CodeBlock, BlockQuote
)

def escape_html(s: str) -> str:
    return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            .replace('"','&quot;').replace("'",'&#39;'))

def render_node(node) -> str:
    if isinstance(node, Document):
        return '\n'.join(render_node(ch) for ch in node.children)
    if isinstance(node, Heading):
        inner = ''.join(render_node(ch) for ch in node.inline)
        return f'<h{node.level}>{inner}</h{node.level}>'
    if isinstance(node, Paragraph):
        inner = ''.join(render_node(ch) for ch in node.inline)
        return f'<p>{inner}</p>'
    if isinstance(node, Text):
        return escape_html(node.value)
    if isinstance(node, Bold):
        inner = ''.join(render_node(ch) for ch in node.inline)
        return f'<strong>{inner}</strong>'
    if isinstance(node, Italic):
        inner = ''.join(render_node(ch) for ch in node.inline)
        return f'<em>{inner}</em>'
    if isinstance(node, Link):
        text = ''.join(render_node(ch) for ch in node.inline)
        href = escape_html(node.href)
        return f'<a href="{href}">{text}</a>'
    if isinstance(node, UnorderedList):
        items_html = ''.join(f'<li>{"".join(render_node(ch) for ch in item.inline)}</li>' for item in node.items)
        return f'<ul>{items_html}</ul>'
    if isinstance(node, OrderedList):
        items_html = ''.join(f'<li>{"".join(render_node(ch) for ch in item.inline)}</li>' for item in node.items)
        return f'<ol>{items_html}</ol>'
    if isinstance(node, ListItem):
        return ''.join(render_node(ch) for ch in node.inline)
    if isinstance(node, CodeBlock):
        lang_attr = f' class="language-{escape_html(node.language)}"' if node.language else ''
        code = escape_html(node.code)
        return f'<pre><code{lang_attr}>{code}</code></pre>'
    if isinstance(node, BlockQuote):
        inner = '\n'.join(render_node(ch) for ch in node.children)
        return f'<blockquote>{inner}</blockquote>'
    raise ValueError(f'Unknown node type: {type(node)}')

def render(document: Document) -> str:
    return render_node(document)