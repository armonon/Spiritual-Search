import requests


def search_open_library(query, max_results=10):
    """
    Fetch up to `max_results` docs from Open Library, paging via `offset` if needed.
    If `max_results` is None, fetch until exhausted.
    """
    books = []
    if max_results is None:
        remaining = float('inf')
    else:
        remaining = int(max_results)

    offset = 0
    CHUNK = 100

    while remaining > 0:
        fetch_n = CHUNK if remaining == float('inf') else min(CHUNK, remaining)
        url = f"https://openlibrary.org/search.json?q={query}&limit={fetch_n}&offset={offset}"
        res = requests.get(url).json()

        docs = res.get('docs', [])
        if not docs:
            break

        for doc in docs:
            cover_id = doc.get('cover_i')
            thumbnail = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
            books.append({
                'title': doc.get('title', 'No Title'),
                'authors': doc.get('author_name', []),
                'year': doc.get('first_publish_year', ''),
                'source': 'OpenLibrary',
                'thumbnail': thumbnail
            })

        count = len(docs)
        offset += count
        if remaining != float('inf'):
            remaining -= count

        if count < fetch_n:
            break

    return books
