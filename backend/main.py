# backend/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.services.google_books import search_google_books
from backend.services.open_library import search_open_library
from backend.services.internet_archive import search_internet_archive
from backend.services.dedupe import deduplicate_books
from pathlib import Path

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
def search(query: str, offset: int = 0, limit: int = RESULTS_PER_PAGE):
    """
    Search all sources, deduplicate, and return paginated results.
    """
    google_results = search_google_books(query)
    openlib_results = search_open_library(query)
    ia_results = search_internet_archive(query)

    all_results = google_results + openlib_results + ia_results
    deduped = deduplicate_books(all_results)

    # Pagination using offset & limit
    paged_results = deduped[offset:offset + limit]
    has_more = offset + limit < len(deduped)

    return {
        "query": query,
        "results": paged_results,
        "offset": offset,
        "limit": limit,
        "has_more": has_more
    }
