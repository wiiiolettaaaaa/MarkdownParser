from  mdparser.markdown_parser.cache import CacheManager, LRUCache
from  mdparser.markdown_parser.parser import Parser
from  mdparser.markdown_parser.renderer import render_html


def parse_func(text):
    parser = Parser(text)
    return parser.parse()


def render_func(doc):
    return render_html(doc)


def test_cache_speedup():
    sample = "# Sample\n" + "Line " * 2000
    cache_manager = CacheManager(LRUCache(capacity=32))

    # Перший запуск без кешу
    doc1 = parse_func(sample)
    html1 = render_func(doc1)

    # Другий запуск через кеш
    cache_manager.set(sample, doc1)
    doc2 = cache_manager.get(sample)
    html2 = render_func(doc2)

    assert html1 == html2