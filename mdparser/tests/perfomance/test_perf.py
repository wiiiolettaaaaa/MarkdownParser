import pytest
from mdparser.markdown_parser.parser import Parser

def make_large_md(n_lines=2000):
    lines = ["# Large Document"]
    for i in range(n_lines):
        lines.append(f"Paragraph {i} with **bold** and *italic* and [link](http://example.com/{i})")
    return "\n".join(lines)

def test_parser_large_file(benchmark):
    md = make_large_md(1000)
    def run():
        parser = Parser(md)
        doc = parser.parse()
        return doc
    result = benchmark(run)
    assert result is not None