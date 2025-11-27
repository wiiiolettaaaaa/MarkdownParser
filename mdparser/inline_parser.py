from .ast_nodes import Text, Bold, Italic, Link
from typing import List

def parse_inline_from_text(s: str) -> List:
    nodes = []
    i = 0
    n = len(s)
    while i < n:
        if s.startswith('**', i):
            j = s.find('**', i+2)
            if j != -1:
                inner = parse_inline_from_text(s[i+2:j])
                nodes.append(Bold(inner))
                i = j + 2
                continue
        if s.startswith('*', i):
            j = s.find('*', i+1)
            if j != -1:
                inner = parse_inline_from_text(s[i+1:j])
                nodes.append(Italic(inner))
                i = j + 1
                continue
        if s.startswith('[', i):
            rb = s.find(']', i+1)
            if rb != -1 and rb+1 < n and s[rb+1] == '(':
                rp = s.find(')', rb+2)
                if rp != -1:
                    text_part = s[i+1:rb]
                    href = s[rb+2:rp]
                    nodes.append(Link(parse_inline_from_text(text_part), href))
                    i = rp + 1
                    continue
        # accumulate text
        start = i
        while i < n and not s.startswith('**', i) and not s.startswith('*', i) and s[i] != '[':
            i += 1
        if start < i:
            nodes.append(Text(s[start:i]))
    # merge adjacent Text
    merged = []
    for node in nodes:
        if isinstance(node, Text) and merged and isinstance(merged[-1], Text):
            merged[-1] = Text(merged[-1].value + node.value)
        else:
            merged.append(node)
    return merged