# backend/main.py
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

        if exact:
            term = query.lower()
            def matches(r):
                if term in (r.get("title") or "").lower():
                    return True
                for field in (r.get("authors") or []):
                    if term in field.lower():
                        return True
                for subj in (r.get("subjects") or []):
                    if term in subj.lower():
                        return True
                return False
            deduped = [r for r in deduped if matches(r)]
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
