"""HathiTrust connector for Personal Librarian."""
from typing import List, Dict, Any
import requests

HATHITRUST_API = "https://catalog.hathitrust.org/api/volumes/brief/json/"


def search_hathitrust(keywords: List[str], per_keyword: int = 6) -> List[Dict[str, Any]]:
    """Search HathiTrust by ISBN or keyword.

    HathiTrust's public bibliographic API is ISBN-based. For a federated search
    we'll attempt to treat each keyword as an ISBN, and otherwise return an empty
    list or placeholder. In a full implementation you'd need an API key and/or
    scrape search results pages.
    """
    results_list: List[Dict[str, Any]] = []
    for kw in keywords:
        # if kw looks like ISBN, try API
        clean = kw.replace('-', '').strip()
        if clean.isdigit() and len(clean) in (10, 13):
            try:
                r = requests.get(HATHITRUST_API + clean, timeout=8)
                r.raise_for_status()
                data = r.json()
                # API returns {isbn: {...}} structure
                entry = data.get(clean)
                if entry:
                    title = entry.get('title')
                    authors = entry.get('author')
                    year = None
                    subjects = entry.get('subjects', [])
                    isbn = clean
                    results_list.append({
                        'title': title,
                        'author': authors,
                        'year': year,
                        'subjects': subjects,
                        'isbn': isbn,
                        'source': 'hathitrust',
                        'link': f'https://catalog.hathitrust.org/Search/Home?lookfor={isbn}'
                    })
            except Exception:
                pass
        # otherwise skip; real system would scrape search pages
    # limit to per_keyword * len(keywords)
    return results_list[: per_keyword * len(keywords)]
