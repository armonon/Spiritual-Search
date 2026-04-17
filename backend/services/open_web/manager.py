from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Optional
from .search import open_web_search
from .cache import set_, get

_EXEC = ThreadPoolExecutor(max_workers=2)
_FUTURES = {}
_LOCK = Lock()


def schedule_fetch(query: str):
    k = query.strip().lower()
    with _LOCK:
        if k in _FUTURES:
            f = _FUTURES[k]
            if not f.done():
                return
        # submit background fetch
        fut = _EXEC.submit(_run_and_cache, query)
        _FUTURES[k] = fut


def _run_and_cache(query: str):
    try:
        results = open_web_search(query, max_results=None)
        set_(query, results)
        return results
    except Exception:
        return []


def fetch_now(query: str, timeout: Optional[float] = None):
    """Run a blocking fetch using the executor but with a timeout."""
    k = query.strip().lower()
    with _LOCK:
        fut = _EXEC.submit(open_web_search, query, None)
        _FUTURES[k] = fut
    try:
        results = fut.result(timeout=timeout)
        set_(query, results)
        return results
    except Exception:
        return None
