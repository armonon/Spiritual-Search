"""Ingest book data from multiple sources into a local JSON index."""
import json
import os
from personal_librarian import expand_topic, search_openlibrary
from google_books import search_google_books
from loc_connector import search_loc
from gutendex_connector import search_gutendex
from ia_connector import search_internet_archive
from wikidata_connector import search_wikidata
from hathitrust_connector import search_hathitrust
from worldcat_connector import search_worldcat

DATA_DIR = "data"
INDEX_FILE = os.path.join(DATA_DIR, "books_index.json")


def ingest_topic(topic: str, max_keywords: int = 10):
    """Ingest data for a topic and save to local index."""
    keywords = expand_topic(topic, max_keywords=max_keywords)
    ol = search_openlibrary(keywords)
    gb_raw = []
    for kw in keywords:
        items = search_google_books(kw, max_results=10)
        for it in items:
            gb_raw.append({
                "title": it.get("title"),
                "authors": it.get("authors") or [],
                "year": int(it.get("year")) if (it.get("year") and str(it.get("year")).isdigit()) else None,
                "source": "google_books",
                "subjects": [],
                "raw": it,
            })
    loc_raw = []
    for kw in keywords:
        items = search_loc([kw], per_keyword=10)
        loc_raw.extend(items)
    guten_raw = []
    ia_raw = []
    wikidata_raw = []
    ht_raw = []
    wc_raw = []
    for kw in keywords:
        guten_raw.extend(search_gutendex([kw], per_keyword=10))
        ia_raw.extend(search_internet_archive([kw], per_keyword=10))
        wikidata_raw.extend(search_wikidata([kw], per_keyword=10))
        ht_raw.extend(search_hathitrust([kw], per_keyword=10))
        wc_raw.extend(search_worldcat([kw], per_keyword=10))

    all_books = ol + gb_raw + loc_raw + guten_raw + ia_raw + wikidata_raw + ht_raw + wc_raw

    # Save to index
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_books, f, ensure_ascii=False, indent=2)
    print(f"Ingested {len(all_books)} books for topic '{topic}' into {INDEX_FILE}")


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "fasting"
    ingest_topic(topic)
