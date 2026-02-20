import time
from typing import Any


class TTLCache:
    """Simple in-memory cache with per-key TTL."""

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int):
        self._store[key] = (time.time() + ttl, value)

    def invalidate(self, key: str):
        self._store.pop(key, None)

    def cleanup(self):
        now = time.time()
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]


cache = TTLCache()
