"""WorldCat connector for Personal Librarian."""
from typing import List, Dict, Any
import os
import requests

# optional API key from OCLC
WORLDCAT_API_KEY = os.getenv("WORLDCAT_KEY")
WORLDCAT_SEARCH_URL = "https://www.oclc.org/bib/search"


def search_worldcat(keywords: List[str], per_keyword: int = 6) -> List[Dict[str, Any]]:
    """Search WorldCat. If key present use their API, otherwise return empty."""
    results: List[Dict[str, Any]] = []
    if not WORLDCAT_API_KEY:
        return results

    for kw in keywords:
        params = {"q": kw, "wskey": WORLDCAT_API_KEY, "count": per_keyword}
        try:
            r = requests.get(WORLDCAT_SEARCH_URL, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            for item in data.get("entries", [])[:per_keyword]:
                results.append({
                    "title": item.get("title"),
                    "author": item.get("author"),
                    "year": item.get("publicationYear"),
                    "subjects": item.get("subjects", []),
                    "isbn": item.get("isbn"),
                    "source": "worldcat",
                    "libraries": item.get("holdingsCount"),
                })
        except Exception:
            pass
    return results
