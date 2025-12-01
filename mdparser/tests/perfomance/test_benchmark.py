# tests/test_benchmark.py
# skeleton for pytest-benchmark usage
from  mdparser.markdown_parser.parser import Parser
import os

def test_small_file_benchmark(benchmark):
    sample = "# hello\n" + "line\n" * 100
    def run():
        p = Parser(sample)
        doc = p.parse()
        return doc
    result = benchmark(run)
    assert result is not None