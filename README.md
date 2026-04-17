# Personal Librarian Search Engine

This project is an incremental prototype of a federated academic library search system. It allows users to search topics and discover books across Open Library, Google Books, Library of Congress, Project Gutenberg, Internet Archive, Wikidata, HathiTrust (ISBN), WorldCat (stub), and more.

## Architecture Overview

- **Query Expansion**: Use Datamuse to expand topic into related keywords.
- **Connectors**: Individual modules for each data source (see `backend/services/*.py`).
- **Aggregator**: `run_multi_pilot.py` collects results, deduplicates, ranks, and groups by subject.
- **Local Index**: `ingest_data.py` builds a JSON index for fast offline search.
- **Knowledge Explorer**: `teach_me.py` provides curated book recommendations and related subjects.

## Searching

```bash
# simple search
./venv/bin/python backend/services/run_multi_pilot.py "fasting"

# academic mode (prioritizes HathiTrust/WorldCat)
./venv/bin/python backend/services/run_multi_pilot.py "fasting" False True
```

## Ingestion

```bash
./venv/bin/python backend/services/ingest_data.py "fasting"
```

## Extending

Add new connectors under `backend/services/` and import them in `run_multi_pilot.py`. Connectors should return standardized dicts with keys like `title`, `authors`, `year`, `subjects`, `isbn`, `source`, and optional `libraries`.

## Future Work

- Add true WorldCat API integration with key
- Support SRU/Z39.50 federated catalogs
- Implement caching and local search index with Elasticsearch/Meilisearch
- Expand academic filters and reading order algorithm

For now the system shows how to federate across multiple open library datasets and rank by keyword/subject/library popularity.