"""Wikidata connector for books."""
from typing import List, Dict, Any
import requests

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


def search_wikidata(keywords: List[str], per_keyword: int = 6) -> List[Dict[str, Any]]:
    # Basic SPARQL query searching book labels
    aggregated: Dict[str, Dict[str, Any]] = {}
    for kw in keywords:
        query = f"""
        SELECT ?book ?bookLabel ?authorLabel WHERE {{
          ?book wdt:P31 wd:Q571 .
          ?book rdfs:label ?bookLabel .
          OPTIONAL {{ ?book wdt:P50 ?author . ?author rdfs:label ?authorLabel . FILTER(LANG(?authorLabel) = "en") }}
          FILTER(CONTAINS(LCASE(?bookLabel), "{kw.lower()}"))
          FILTER(LANG(?bookLabel) = "en")
        }} LIMIT {per_keyword}
        """
        try:
            r = requests.get(WIKIDATA_SPARQL, params={"query": query, "format": "json"}, timeout=8)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", {}).get("bindings", [])
        except Exception:
            results = []
        for item in results:
            title = item.get("bookLabel", {}).get("value")
            author = item.get("authorLabel", {}).get("value")
            key = item.get("book", {}).get("value")
            if key in aggregated:
                if kw not in aggregated[key]["matched_keywords"]:
                    aggregated[key]["matched_keywords"].append(kw)
                continue
            aggregated[key] = {
                "id": key,
                "title": title,
                "authors": [author] if author else [],
                "year": None,
                "matched_keywords": [kw],
                "source": "wikidata",
                "raw": item,
            }
    results = list(aggregated.values())
    results.sort(key=lambda r: (-len(r.get("matched_keywords", [])), 0))
    return results
