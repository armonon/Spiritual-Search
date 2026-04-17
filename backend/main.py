# backend/main.py
import re
from difflib import SequenceMatcher

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.services.google_books import search_google_books
from backend.services.open_library import search_open_library
from backend.services.internet_archive import search_internet_archive
from backend.services.dedupe import deduplicate_books
from backend.services.open_web import open_web_search
from backend.services.open_web import manager as open_web_manager
from backend.services.open_web import cache as open_web_cache
from pathlib import Path
import concurrent.futures

app = FastAPI()

# CORS so front-end can access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for JS/CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

RESULTS_PER_PAGE = 10
# No hard cap: services will page through their APIs as needed (supporting "unlimited").


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _word_tokens(value: str):
    return re.findall(r"[a-z0-9]+", _clean_text(value))


def _description_text(record: dict) -> str:
    raw = record.get("raw") if isinstance(record.get("raw"), dict) else {}
    volume_info = raw.get("volumeInfo") if isinstance(raw.get("volumeInfo"), dict) else {}
    candidates = [
        record.get("description"),
        record.get("summary"),
        record.get("excerpt"),
        volume_info.get("description"),
        volume_info.get("subtitle"),
    ]
    return " ".join([c for c in candidates if isinstance(c, str) and c.strip()])


def _query_matches_text(query: str, text: str) -> bool:
    q = _clean_text(query)
    t = _clean_text(text)
    if not q or not t:
        return False

    if q in t:
        return True

    q_tokens = [tok for tok in _word_tokens(q) if len(tok) >= 3]
    t_tokens = set(_word_tokens(t))
    if not q_tokens or not t_tokens:
        return False

    # Typo-tolerant token matching (e.g. "tsntra" -> "tantra")
    for q_tok in q_tokens:
        token_match = False
        for t_tok in t_tokens:
            if q_tok == t_tok or q_tok in t_tok or t_tok in q_tok:
                token_match = True
                break
            if abs(len(q_tok) - len(t_tok)) <= 2 and SequenceMatcher(None, q_tok, t_tok).ratio() >= 0.8:
                token_match = True
                break
        if not token_match:
            return False
    return True


def _record_matches_query(record: dict, query: str, exact: bool = False) -> bool:
    title = record.get("title") or ""
    description = _description_text(record)
    q = _clean_text(query)

    if exact:
        # strict containment in title or description
        return bool(q) and (q in _clean_text(title) or q in _clean_text(description))

    # normal mode: fuzzy/typo-tolerant over title or description text
    return _query_matches_text(query, title) or _query_matches_text(query, description)

@app.get("/", response_class=HTMLResponse)
async def root():
    # Serve your main HTML page
    # Resolve index path relative to the repository root (two levels up from this file)
    index_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    if not index_path.exists():
        # Fallback to static/index.html if frontend/index.html isn't present
        index_path = Path(__file__).resolve().parents[1] / "static" / "index.html"

    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/search")
def search(
    query: str,
    mode: str = "library",
    offset: int = 0,
    limit: int = RESULTS_PER_PAGE,
    exact: bool = False,
    synonyms: bool = False,
):
    """
    Search all sources, optionally filtering by exact term or expanding with
    synonyms. Results are paginated via offset/limit.  """

    if mode != "open_web":
        from backend.services.run_multi_pilot import run as multi_run

        try:
            full = multi_run(query, use_local=False, academic=False, include_synonyms=synonyms)
            deduped = full.get("results", [])
        except Exception as e:
            # log and fall back to empty list so endpoint stays alive
            print(f"Error running multi source search: {e}")
            deduped = []

        # Keep only books where query appears in title or description.
        # In normal mode this is typo-tolerant; in exact mode this is strict containment.
        deduped = [r for r in deduped if _record_matches_query(r, query, exact=exact)]
    else:
        cached = open_web_cache.get(query)
        if cached is not None:
            deduped = cached
        else:
            try:
                quick = open_web_search(query, max_results=50)
                open_web_cache.set_(query, quick)
                deduped = quick
            except Exception:
                open_web_manager.schedule_fetch(query)
                deduped = [
                    {
                        "title": "Open Web discovery in progress",
                        "url": "",
                        "excerpt": "Open Web discovery is running in the background. Refresh or try again shortly.",
                        "date": None,
                        "source_type": "archive",
                        "discovery_reason": "background_scheduled"
                    }
                ]

    paged_results = deduped[offset : offset + limit] if deduped is not None else []
    has_more = offset + limit < len(deduped) if deduped is not None else False

    return {
        "query": query,
        "results": paged_results,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "total": len(deduped) if deduped is not None else 0,
        "exact": exact,
        "synonyms": synonyms,
    }
