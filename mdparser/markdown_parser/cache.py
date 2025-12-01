from __future__ import annotations
from typing import Dict, Any, Optional, Callable, List, Tuple
import time
import hashlib
import threading


# -----------------------------------------------------------
# Key generation для кешу
# -----------------------------------------------------------

def make_key(data: str) -> str:
    """Уніфікований ключ: SHA256 від даних."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# -----------------------------------------------------------
# Базова стратегія кешу
# -----------------------------------------------------------

class CacheStrategy:
    def get(self, key: str):
        raise NotImplementedError

    def set(self, key: str, value: Any):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def stats(self) -> dict:
        return {}


# -----------------------------------------------------------
# NoCache — використовується при тестах продуктивності без кешу
# -----------------------------------------------------------

class NoCache(CacheStrategy):
    def get(self, key: str):
        return None

    def set(self, key: str, value: Any):
        pass

    def clear(self):
        pass

    def stats(self):
        return {
            "enabled": False,
            "hits": 0,
            "misses": 0,
            "size": 0
        }


# -----------------------------------------------------------
# LRU Cache
# -----------------------------------------------------------

class LRUCache(CacheStrategy):
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.cache: Dict[str, Any] = {}
        self.order: List[str] = []
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()

    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                self.hits += 1
                # Move to end (most recently used)
                self.order.remove(key)
                self.order.append(key)
                return self.cache[key]
            self.misses += 1
            return None

    def set(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                # Update + move to end
                self.order.remove(key)
                self.order.append(key)
                self.cache[key] = value
                return

            # Insert new
            self.cache[key] = value
            self.order.append(key)

            # Remove LRU
            if len(self.cache) > self.capacity:
                oldest = self.order.pop(0)
                del self.cache[oldest]

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.order.clear()

    def stats(self):
        return {
            "enabled": True,
            "type": "LRU",
            "hits": self.hits,
            "misses": self.misses,
            "size": len(self.cache),
            "capacity": self.capacity
        }


# -----------------------------------------------------------
# LFU Cache — видаляє найменш часто використані елементи
# -----------------------------------------------------------

class LFUCache(CacheStrategy):
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.cache: Dict[str, Tuple[Any, int]] = {}  # key -> (value, freq)
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()

    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                self.hits += 1
                value, freq = self.cache[key]
                self.cache[key] = (value, freq + 1)
                return value
            self.misses += 1
            return None

    def set(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                _, freq = self.cache[key]
                self.cache[key] = (value, freq + 1)
                return

            if len(self.cache) >= self.capacity:
                # Remove least-frequent
                least_key = min(self.cache, key=lambda k: self.cache[k][1])
                del self.cache[least_key]

            self.cache[key] = (value, 1)

    def clear(self):
        with self.lock:
            self.cache.clear()

    def stats(self):
        return {
            "enabled": True,
            "type": "LFU",
            "hits": self.hits,
            "misses": self.misses,
            "size": len(self.cache),
            "capacity": self.capacity
        }


# -----------------------------------------------------------
# Головний Cache Manager
# -----------------------------------------------------------

class CacheManager:
    """
    Керує 3 видами кешу:
      - tokens
      - ast
      - html
    Має одну стратегію (LRU/LFU/NoCache)
    """

    def __init__(self, strategy: CacheStrategy):
        self.strategy = strategy
        self.enabled = not isinstance(strategy, NoCache)

    # -------------------------------
    # Tokens
    # -------------------------------
    def get_tokens(self, text: str):
        if not self.enabled:
            return None
        key = "tokens:" + make_key(text)
        return self.strategy.get(key)

    def set_tokens(self, text: str, tokens: Any):
        if self.enabled:
            key = "tokens:" + make_key(text)
            self.strategy.set(key, tokens)

    # -------------------------------
    # AST
    # -------------------------------
    def get_ast(self, text: str):
        if not self.enabled:
            return None
        key = "ast:" + make_key(text)
        return self.strategy.get(key)

    def set_ast(self, text: str, ast: Any):
        if self.enabled:
            key = "ast:" + make_key(text)
            self.strategy.set(key, ast)

    # -------------------------------
    # HTML
    # -------------------------------
    def get_html(self, text: str):
        if not self.enabled:
            return None
        key = "html:" + make_key(text)
        return self.strategy.get(key)

    def set_html(self, text: str, html: str):
        if self.enabled:
            key = "html:" + make_key(text)
            self.strategy.set(key, html)

    # -------------------------------
    # Stats
    # -------------------------------
    def stats(self) -> dict:
        return self.strategy.stats()

    def clear(self):
        self.strategy.clear()


# -----------------------------------------------------------
# Performance measurement tools
# -----------------------------------------------------------

class CacheEfficiencyMeter:
    """
    Вимірює ефективність кешування:

      - час без кешу
      - час з кешем
      - speedup
      - hit ratio
    """

    def __init__(self, parse_func: Callable[[str], Any], render_func: Callable[[Any], str],
                 cache_manager: CacheManager):
        self.parse_func = parse_func
        self.render_func = render_func
        self.cache = cache_manager

    def measure(self, text: str, repeat: int = 20) -> dict:
        # ---------------------------------------------
        # Measure WITHOUT cache
        # ---------------------------------------------
        no_cache_times = []
        old_strategy = self.cache.strategy
        self.cache.strategy = NoCache()

        for _ in range(repeat):
            start = time.perf_counter()
            ast = self.parse_func(text)
            self.render_func(ast)
            no_cache_times.append(time.perf_counter() - start)

        avg_no_cache = sum(no_cache_times) / repeat

        # ---------------------------------------------
        # Measure WITH cache
        # ---------------------------------------------
        with_cache_times = []
        self.cache.strategy = old_strategy  # restore

        for _ in range(repeat):
            start = time.perf_counter()
            ast = self.parse_func(text)
            self.render_func(ast)
            with_cache_times.append(time.perf_counter() - start)

        avg_with_cache = sum(with_cache_times) / repeat

        stats = self.cache.stats()
        hits = stats.get("hits", 0)
        misses = stats.get("misses", 0)

        # ---------------------------------------------
        # Result summary
        # ---------------------------------------------
        return {
            "avg_no_cache": avg_no_cache,
            "avg_with_cache": avg_with_cache,
            "speedup": avg_no_cache / avg_with_cache if avg_with_cache > 0 else None,
            "cache_stats": stats,
            "hit_ratio": hits / (hits + misses) if (hits + misses) > 0 else 0.0
        }


# -----------------------------------------------------------
# Quick local test
# -----------------------------------------------------------

if __name__ == "__main__":
    cm = CacheManager(LRUCache(4))
    cm.set_tokens("hello", ["t1", "t2"])
    print(cm.get_tokens("hello"))
    print(cm.stats())