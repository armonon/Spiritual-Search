"""Minimal Personal Librarian prototype.

Features:
- Expand a user topic into related keywords (Datamuse API, with graceful fallback).
- Search Open Library for books matching those keywords.
- Aggregate and return structured results.

This module is intentionally small and dependency-light: it only uses `requests`.
"""
from typing import List, Dict, Any
import requests

DATAMUSE_URL = "https://api.datamuse.com/words"
OPENLIB_SEARCH_URL = "https://openlibrary.org/search.json"


def expand_topic(topic: str, max_keywords: int = 6, include_synonyms: bool = True) -> List[str]:
    """Return a list of keywords related to `topic`.

    If ``include_synonyms`` is False we simply return a list containing the
    original topic (plus a few trivial variants) so callers can perform an
    "exact" search. When True we query Datamuse as before and return up to
    ``max_keywords`` related words.
    """
    topic = topic.strip()
    keywords = [topic]
    # if we don't want synonyms bail out early with minimal variants
    if not include_synonyms:
        # add a couple obvious morphological relatives if space
        if " " not in topic and len(keywords) < max_keywords:
            keywords.append(topic + "s")
        return keywords

    try:
        resp = requests.get(DATAMUSE_URL, params={"ml": topic, "max": max_keywords - 1}, timeout=5)
        resp.raise_for_status()
        words = [w.get("word") for w in resp.json() if w.get("word")]
        for w in words:
            if w not in keywords:
                keywords.append(w)
            if len(keywords) >= max_keywords:
                break
    except Exception:
        # Fallback: add simple morphological variants and common related tokens
        if " " not in topic:
            keywords += [topic + "s", topic + "ing"]
        if len(keywords) < max_keywords:
            keywords += [topic + " book", "books about " + topic]
        keywords = keywords[:max_keywords]

    return keywords


def search_openlibrary(keywords: List[str], per_keyword: int = 8) -> List[Dict[str, Any]]:
    """Search Open Library for each keyword and aggregate unique results.

    Returns a list of result dicts with keys: `id`, `title`, `authors`, `year`, `matched_keyword`, `source`.
    """
    aggregated: Dict[str, Dict[str, Any]] = {}

    for kw in keywords:
        params = {"q": kw, "limit": per_keyword, "fields": "title,author_name,first_publish_year,key"}
        try:
            r = requests.get(OPENLIB_SEARCH_URL, params=params, timeout=8)
            r.raise_for_status()
            docs = r.json().get("docs", [])
        except Exception:
            docs = []

        for doc in docs:
            key = doc.get("key") or doc.get("cover_edition_key")
            if not key:
                title = doc.get("title") or ""
                authors = ",".join(doc.get("author_name") or [])
                key = f"/fallback/{title}/{authors}"

            if key in aggregated:
                if kw not in aggregated[key]["matched_keywords"]:
                    aggregated[key]["matched_keywords"].append(kw)
                continue

            aggregated[key] = {
                "id": key,
                "title": doc.get("title"),
                "authors": doc.get("author_name") or [],
                "year": doc.get("first_publish_year"),
                "matched_keywords": [kw],
                "source": "openlibrary",
                "raw": doc,
            }

    results = list(aggregated.values())
    results.sort(key=lambda r: (-len(r["matched_keywords"]), -(r.get("year") or 0)))
    return results


def search_topic(topic: str, max_keywords: int = 6, per_keyword: int = 8) -> Dict[str, Any]:
    """High-level search: expand `topic`, search Open Library, and return structured results."""
    keywords = expand_topic(topic, max_keywords=max_keywords)
    results = search_openlibrary(keywords, per_keyword=per_keyword)
    return {"topic": topic, "keywords": keywords, "results": results}


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Minimal Personal Librarian prototype CLI")
    parser.add_argument("topic", help="Topic to search for (e.g. 'fasting')")
    args = parser.parse_args()
    out = search_topic(args.topic)
    print(json.dumps(out, indent=2, ensure_ascii=False))
