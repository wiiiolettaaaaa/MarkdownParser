import hashlib
import pickle
from typing import Optional

class InMemoryCacheBackend:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

class RedisCacheBackend:
    def __init__(self, host="localhost", port=6379, db=0):
        import redis
        self.r = redis.Redis(host=host, port=port, db=db)

    def get(self, key):
        val = self.r.get(key)
        return val

    def set(self, key, value):
        # store raw bytes (pickle)
        self.r.set(key, value)

class CacheService:
    def __init__(self, backend=None):
        self.backend = backend or InMemoryCacheBackend()

    def _key(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def get_ast(self, text: str):
        k = self._key(text)
        data = self.backend.get(k)
        if data is None:
            return None
        # data may be bytes (redis) or pickled object (inmemory)
        try:
            return pickle.loads(data)
        except Exception:
            # maybe in-memory stored object directly
            return data

    def set_ast(self, text: str, ast):
        k = self._key(text)
        data = pickle.dumps(ast)
        self.backend.set(k, data)