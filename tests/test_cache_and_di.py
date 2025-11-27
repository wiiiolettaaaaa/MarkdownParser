from mdparser.cache_service import CacheService, InMemoryCacheBackend
from mdparser.parser_service import ParserService
from mdparser.factory import NodeFactory
from mdparser.perf_monitor import PerfMonitor

def test_parser_service_di_and_cache():
    cache = CacheService(InMemoryCacheBackend())
    perf = PerfMonitor()
    factory = NodeFactory()
    service = ParserService(factory=factory, cache=cache, perf=perf)

    text = "# Title"
    first = service.parse(text)
    second = service.parse(text)

    assert first["cached"] is False
    assert second["cached"] is True
    assert first["metrics"] is not None