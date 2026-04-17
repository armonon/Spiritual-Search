"""Library of Congress connector for Personal Librarian."""
from typing import List, Dict, Any
import requests

LOC_SEARCH_URL = "https://www.loc.gov/search/"


def search_loc(keywords: List[str], per_keyword: int = 6) -> List[Dict[str, Any]]:
    """Search Library of Congress for each keyword and return structured results."""
    aggregated: Dict[str, Dict[str, Any]] = {}

    for kw in keywords:
        params = {"q": kw, "fo": "json", "c": per_keyword}
        try:
            r = requests.get(LOC_SEARCH_URL, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
        except Exception:
            results = []

        for item in results:
            title = item.get("title")
            if not title:
                continue
            authors = item.get("contributors", [])
            year = item.get("date")
            if year:
                try:
                    year = int(year[:4])
                except:
                    year = None
            subjects = item.get("subjects", [])

            # Use title + first author as key
            key = f"{title.lower()}|{authors[0].lower() if authors else ''}"
            if key in aggregated:
                if kw not in aggregated[key]["matched_keywords"]:
                    aggregated[key]["matched_keywords"].append(kw)
                continue

            aggregated[key] = {
                "id": item.get("id"),
                "title": title,
                "authors": authors,
                "year": year,
                "subjects": subjects,
                "matched_keywords": [kw],
                "source": "library_of_congress",
                "raw": item,
            }

    results = list(aggregated.values())
    results.sort(key=lambda r: (-len(r["matched_keywords"]), -(r.get("year") or 0)))
    return results
