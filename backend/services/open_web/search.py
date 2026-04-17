from .discover import discover_sites
from .forums.discover import discover_forums


def open_web_search(query: str, max_results=None):
    """
    Entry point for Open Web v1 search pipeline.
    Returns a list of dicts matching the Open Web data model.
    This implementation is intentionally conservative and seed-based.
    """
    pages = []
    # discover independent sites and blogs / archive-linked pages
    pages += discover_sites(query, max_results=max_results)
    # discover curated forum seeds (first post only)
    pages += discover_forums(query, max_results=max_results)

    # apply simple grouping and light randomization for diversity
    # but preserve determinism for now — we simply return as-found
    return pages[:max_results] if max_results else pages
