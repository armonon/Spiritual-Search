"""Runner that merges Open Library + Google Books + Library of Congress results, with local index support."""
import json
import sys
import os
from backend.services.personal_librarian import expand_topic, search_openlibrary
from backend.services.google_books import search_google_books
from backend.services.loc_connector import search_loc
from backend.services.gutendex_connector import search_gutendex
from backend.services.ia_connector import search_internet_archive
from backend.services.wikidata_connector import search_wikidata
from backend.services.hathitrust_connector import search_hathitrust
from backend.services.worldcat_connector import search_worldcat

DATA_DIR = "data"
INDEX_FILE = os.path.join(DATA_DIR, "books_index.json")


def normalize_key(r):
    t = (r.get("title") or "").strip().lower()
    a = (r.get("authors") or [])
    a0 = a[0].strip().lower() if a else ""
    return f"{t}|{a0}"


def merge_results(list_a, list_b):
    # dedupe by ISBN if available, otherwise fallback to title+author
    seen = {}
    merged = []
    for r in list_a + list_b:
        isbn = r.get("isbn")
        if isbn:
            k = f"isbn:{isbn}"
        else:
            k = normalize_key(r)
        if k in seen:
            existing = seen[k]
            # merge matched keywords
            for kw in r.get("matched_keywords", []):
                if kw not in existing.setdefault("matched_keywords", []):
                    existing["matched_keywords"].append(kw)
            # prefer non-null values
            for field in ("year", "subjects", "libraries"):
                if not existing.get(field) and r.get(field):
                    existing[field] = r.get(field)
            continue
        seen[k] = dict(r)
        merged.append(seen[k])
    return merged


def score_result(r, keywords, academic=False):
    # compute keywordMatch and subjectMatch
    km = len([kw for kw in keywords if kw.lower() in (r.get("title") or "").lower()])
    sm = 0
    for subj in r.get("subjects", []):
        for kw in keywords:
            if kw.lower() in subj.lower():
                sm += 1
    lib = r.get("libraries") or 0
    rec = r.get("year") or 0
    # normalize components (simple, could be improved)
    return km * 0.4 + sm * 0.3 + (lib * 0.2) + (rec * 0.1)


def rank_results(results, keywords, academic=False):
    for r in results:
        r["_score"] = score_result(r, keywords, academic)
    results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return results
def group_by_subjects(results):
    """Group results by subjects."""
    groups = {}
    for r in results:
        subjects = r.get("subjects", [])
        if not subjects:
            subjects = ["Uncategorized"]
        for subj in subjects:
            if subj not in groups:
                groups[subj] = []
            groups[subj].append(r)
    return groups


def run(
    topic: str = "fasting",
    use_local: bool = True,
    academic: bool = False,
    include_synonyms: bool = True,
):
    # expand topic based on flag
    keywords = [k.strip() for k in expand_topic(topic, include_synonyms=include_synonyms) if isinstance(k, str) and k.strip()]
    if not keywords:
        out = {
            "topic": topic,
            "expandedQueries": [],
            "subjects": {},
            "totalBooksFound": 0,
            "results": [],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return out
    if use_local and os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            all_books = json.load(f)
        merged = all_books
    else:
        ol = search_openlibrary(keywords)
        gb_raw = []
        for kw in keywords:
            items = search_google_books(kw, max_results=8)
            for it in items:
                gb_raw.append({
                    "id": None,
                    "title": it.get("title"),
                    "authors": it.get("authors") or [],
                    "year": int(it.get("year")) if (it.get("year") and str(it.get("year")).isdigit()) else None,
                    "matched_keywords": [kw],
                    "source": "google_books",
                    "raw": it,
                })
        loc_raw = []
        guten_raw = []
        ia_raw = []
        wikidata_raw = []
        ht_raw = []
        wc_raw = []
        for kw in keywords:
            try:
                items = search_loc([kw], per_keyword=8)
                loc_raw.extend(items)
            except Exception as e:
                print(f"Warning: LOC search failed for '{kw}': {e}")
            try:
                guten_raw.extend(search_gutendex([kw], per_keyword=8))
            except Exception as e:
                print(f"Warning: Gutendex search failed for '{kw}': {e}")
            try:
                ia_raw.extend(search_internet_archive([kw], per_keyword=8))
            except Exception as e:
                print(f"Warning: Internet Archive search failed for '{kw}': {e}")
            try:
                wikidata_raw.extend(search_wikidata([kw], per_keyword=8))
            except Exception as e:
                print(f"Warning: Wikidata search failed for '{kw}': {e}")
            try:
                ht_raw.extend(search_hathitrust([kw], per_keyword=8))
            except Exception as e:
                print(f"Warning: HathiTrust search failed for '{kw}': {e}")
            try:
                wc_raw.extend(search_worldcat([kw], per_keyword=8))
            except Exception as e:
                print(f"Warning: WorldCat search failed for '{kw}': {e}")
        merged = merge_results(ol, gb_raw + loc_raw + guten_raw + ia_raw + wikidata_raw + ht_raw + wc_raw)

    # ranking
    ranked = rank_results(merged, keywords, academic=academic)
    subjects_map = group_by_subjects(ranked)
    out = {
        "topic": topic,
        "expandedQueries": keywords,
        "subjects": subjects_map,
        "totalBooksFound": len(ranked),
        "results": ranked,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return out


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "fasting"
    # allow optional flags after topic
    use_local = True
    academic = False
    include_synonyms = True
    if len(sys.argv) >= 3:
        use_local = sys.argv[2].lower() in ("true", "1")
    if len(sys.argv) >= 4:
        academic = sys.argv[3].lower() in ("true", "1")
    if len(sys.argv) >= 5:
        include_synonyms = sys.argv[4].lower() in ("true", "1")
    run(topic, use_local, academic, include_synonyms)