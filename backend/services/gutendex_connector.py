"""Project Gutenberg (Gutendex) connector."""
from typing import List, Dict, Any
import requests

GUTENDEX_URL = "https://gutendex.com/books"


def search_gutendex(keywords: List[str], per_keyword: int = 6) -> List[Dict[str, Any]]:
    aggregated: Dict[str, Dict[str, Any]] = {}
    for kw in keywords:
        params = {"search": kw, "page_size": per_keyword}
        try:
            r = requests.get(GUTENDEX_URL, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
        except Exception:
            results = []
        for item in results:
            title = item.get("title")
            authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
            year = item.get("download_count")  # not the year but something
            key = f"gutendex|{item.get('id')}"
            if key in aggregated:
                if kw not in aggregated[key]["matched_keywords"]:
                    aggregated[key]["matched_keywords"].append(kw)
                continue
            aggregated[key] = {
                "id": key,
                "title": title,
                "authors": authors,
                "year": None,
                "matched_keywords": [kw],
                "source": "gutendex",
                "raw": item,
            }
    results = list(aggregated.values())
    results.sort(key=lambda r: (-len(r.get("matched_keywords", [])), 0))
    return results
