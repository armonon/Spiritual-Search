# Spiritual Search

Spiritual Search blends Armon's original federated library-search prototype with Joey's Librarian book-atlas interface. The goal is a superb research engine for spiritual traditions, herbal medicine, philosophy, classics, archives, and serious book discovery.

The current app is a FastAPI backend plus a static, polished frontend. It searches across open catalogs and archives, organizes records into richer book cards, and keeps source provenance visible so every result can be checked.

## What it does now

- Federated search across Open Library, Google Books, Library of Congress, Project Gutenberg/Gutendex, Internet Archive, Wikidata, HathiTrust, WorldCat stub, and Open Web mode.
- Query expansion through Datamuse synonyms when enabled.
- Deduplication and ranking through `backend/services/run_multi_pilot.py`.
- A redesigned frontend with:
  - hero/search experience for spiritual + scholarly discovery
  - Library Atlas and Open Web modes
  - exact-match and synonym toggles
  - source, availability, year, and sort filters
  - metadata completeness scoring
  - cover fallbacks and source links
  - detail modal with identifiers/subjects/provenance
  - local browser research stack
  - source map and next-build architecture blueprint

## Architecture overview

- **FastAPI app**: `backend/main.py` serves the static UI and `/search` API.
- **Connectors**: individual modules under `backend/services/` return standardized book/source records.
- **Aggregator**: `backend/services/run_multi_pilot.py` collects, deduplicates, ranks, and groups results.
- **Local index**: `backend/services/ingest_data.py` can build `data/books_index.json` for offline/fast search.
- **Frontend**: `frontend/index.html`, `static/script.js`, and `static/styles.css` render the product experience with no build step.

## Run locally

Use Python 3.11.x, matching `runtime.txt` / `.python-version`.

```bash
python3.11 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn backend.main:app --reload
```

Then open `http://127.0.0.1:8000`.

## CLI searching

```bash
# simple search from live sources
PYTHONPATH=. ./venv/bin/python backend/services/run_multi_pilot.py "fasting" False False

# with academic mode
PYTHONPATH=. ./venv/bin/python backend/services/run_multi_pilot.py "fasting" False True

# using local index when present
PYTHONPATH=. ./venv/bin/python backend/services/run_multi_pilot.py "fasting" True False
```

## Ingestion

```bash
PYTHONPATH=. ./venv/bin/python backend/services/ingest_data.py "fasting"
```

## Extending

Add new connectors under `backend/services/` and import them in `run_multi_pilot.py`. Connectors should return standardized dicts with keys like `title`, `authors`, `year`, `subjects`, `isbn`, `source`, and optional `libraries`, `url`, `thumbnail`, or `raw`.

## Next build

- Set up a persistent indexed backend from Open Library dumps, Gutenberg, Internet Archive metadata, Wikidata IDs, and LOC enrichment.
- Resolve works/editions by ISBN, LCCN, OCLC, OLID, DOI, title-author fingerprints, and Wikidata QIDs.
- Add spiritual/herbal/philosophy collections, reading orders, author/tradition maps, semantic search, and public-domain full-text exploration.
- Add true WorldCat/OCLC only through official API access.

Spiritual Search should become a beautiful research atlas: wisdom-first discovery, serious source provenance, and practical paths to actually read the books it finds.
