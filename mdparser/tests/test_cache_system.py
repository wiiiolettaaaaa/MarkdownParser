import hashlib
import time
import types

from mdparser.markdown_parser.cache import (
    make_key, NoCache, LRUCache, LFUCache,
    CacheManager, CacheEfficiencyMeter
)


# -----------------------------------------------------------
# make_key
# -----------------------------------------------------------

def test_make_key():
    key = make_key("hello")
    assert key == hashlib.sha256(b"hello").hexdigest()
    assert len(key) == 64
    assert make_key("hello") == make_key("hello")
    assert make_key("hello") != make_key("world")


# -----------------------------------------------------------
# NoCache
# -----------------------------------------------------------

def test_no_cache_basic():
    nc = NoCache()
    assert nc.get("a") is None
    nc.set("a", 123)
    assert nc.get("a") is None


def test_no_cache_stats():
    nc = NoCache()
    stats = nc.stats()

    assert stats["enabled"] is False
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["size"] == 0


def test_no_cache_clear():
    nc = NoCache()
    nc.clear()  # нічого не робить, але не повинно падати


# -----------------------------------------------------------
# LRUCache
# -----------------------------------------------------------

def test_lru_set_get_hit_miss():
    cache = LRUCache(capacity=2)

    assert cache.get("x") is None
    assert cache.misses == 1

    cache.set("x", 10)
    assert cache.get("x") == 10
    assert cache.hits == 1


def test_lru_eviction():
    cache = LRUCache(capacity=2)

    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # витіснить "a"

    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_lru_update_moves_to_recent():
    cache = LRUCache(capacity=2)

    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")      # тепер b буде LRU
    cache.set("c", 3)   # витісняє b

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_lru_stats():
    cache = LRUCache(capacity=3)

    cache.set("x", 1)
    cache.get("x")
    cache.get("y")

    stats = cache.stats()

    assert stats["enabled"] is True
    assert stats["type"] == "LRU"
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["capacity"] == 3


# -----------------------------------------------------------
# LFUCache
# -----------------------------------------------------------

def test_lfu_set_get_hit_miss():
    cache = LFUCache(capacity=2)

    assert cache.get("a") is None
    assert cache.misses == 1

    cache.set("a", 5)
    assert cache.get("a") == 5
    assert cache.hits == 1


def test_lfu_eviction():
    cache = LFUCache(capacity=2)

    cache.set("a", 1)
    cache.set("b", 2)

    cache.get("a")  # freq(a)=2
    # b freq=1 → буде видалено

    cache.set("c", 3)

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_lfu_frequency_increment():
    cache = LFUCache(capacity=2)

    cache.set("a", 10)
    cache.get("a")
    cache.get("a")

    _, freq = cache.cache["a"]
    assert freq == 3


def test_lfu_stats():
    cache = LFUCache(capacity=5)
    cache.set("x", 1)
    cache.get("x")
    cache.get("y")  # miss

    stats = cache.stats()
    assert stats["type"] == "LFU"
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["capacity"] == 5


# -----------------------------------------------------------
# CacheManager
# -----------------------------------------------------------

def test_cache_manager_basic():
    cm = CacheManager(LRUCache(10))

    cm.set_tokens("hello", ["T"])
    assert cm.get_tokens("hello") == ["T"]

    cm.set_ast("hello", {"a": 1})
    assert cm.get_ast("hello") == {"a": 1}

    cm.set_html("hello", "<p>x</p>")
    assert cm.get_html("hello") == "<p>x</p>"


def test_cache_manager_disabled():
    cm = CacheManager(NoCache())

    cm.set_tokens("x", [1])
    assert cm.get_tokens("x") is None

    cm.set_ast("x", 2)
    assert cm.get_ast("x") is None

    cm.set_html("x", "zzz")
    assert cm.get_html("x") is None


def test_cache_manager_clear():
    cm = CacheManager(LRUCache(10))
    cm.set_tokens("hello", [1])
    assert cm.get_tokens("hello") == [1]

    cm.clear()
    assert cm.get_tokens("hello") is None


# -----------------------------------------------------------
# CacheEfficiencyMeter
# -----------------------------------------------------------

def fake_parse(text):
    return {"ast": text}


def fake_render(ast):
    return "<p>" + ast["ast"] + "</p>"


def test_efficiency_meter_fixed2():
    cm = CacheManager(LRUCache(10))

    # parse_func використовує кеш
    def parse_with_cache(text):
        ast = cm.get_ast(text)
        if ast is None:
            ast = {"ast": text}
            cm.set_ast(text, ast)
        return ast

    def render_func(ast):
        return "<p>" + ast["ast"] + "</p>"

    meter = CacheEfficiencyMeter(parse_with_cache, render_func, cm)
    result = meter.measure("hello", repeat=5)

    stats = result["cache_stats"]

    assert stats["hits"] >= 1  # тепер хіти реально будуть
    assert stats["misses"] >= 1
    assert result["hit_ratio"] > 0
    assert "avg_no_cache" in result
    assert "avg_with_cache" in result
    assert "speedup" in result