from time import time
from threading import Lock

# Simple in-memory cache for Open Web results.
# Keyed by normalized query string.
_CACHE = {}
_LOCK = Lock()
TTL = 60 * 10  # 10 minutes


def _now():
    return int(time())


def get(query: str):
    k = query.strip().lower()
    with _LOCK:
        rec = _CACHE.get(k)
        if not rec:
            return None
        results, ts = rec
        if _now() - ts > TTL:
            del _CACHE[k]
            return None
        return results


def set_(query: str, results):
    k = query.strip().lower()
    with _LOCK:
        _CACHE[k] = (results, _now())


def clear():
    with _LOCK:
        _CACHE.clear()
