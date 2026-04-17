"""Internet Archive search connector."""
from typing import List, Dict, Any
import requests

IA_SEARCH_URL = "https://archive.org/advancedsearch.php"


def search_internet_archive(keywords: List[str], per_keyword: int = 6) -> List[Dict[str, Any]]:
    aggregated: Dict[str, Dict[str, Any]] = {}
    for kw in keywords:
        params = {"q": kw, "fl[]": "title,creator,date,identifier", "rows": per_keyword, "output": "json"}
        try:
            r = requests.get(IA_SEARCH_URL, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            results = data.get("response", {}).get("docs", [])
        except Exception:
            results = []
        for item in results:
            title = item.get("title")
            authors = item.get("creator") if isinstance(item.get("creator"), list) else [item.get("creator")] if item.get("creator") else []
            year = None
            key = item.get("identifier") or title
            if key in aggregated:
                if kw not in aggregated[key]["matched_keywords"]:
                    aggregated[key]["matched_keywords"].append(kw)
                continue
            aggregated[key] = {
                "id": key,
                "title": title,
                "authors": authors,
                "year": year,
                "matched_keywords": [kw],
                "source": "internet_archive",
                "raw": item,
            }
    results = list(aggregated.values())
    results.sort(key=lambda r: (-len(r.get("matched_keywords", [])), 0))
    return results
