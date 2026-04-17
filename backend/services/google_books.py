import requests


def search_google_books(query, max_results=10):
    """
    Fetch up to `max_results` items from Google Books, handling the API's per-request
    `maxResults` limit by paging in chunks (Google caps at 40).
    """
    books = []
    if max_results is None:
        # treat None as 'fetch as many as available' -> we'll loop until no more
        remaining = float('inf')
    else:
        remaining = int(max_results)

    start_index = 0
    CHUNK = 40

    while remaining > 0:
        fetch_n = CHUNK if remaining == float('inf') else min(CHUNK, remaining)
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&startIndex={start_index}&maxResults={fetch_n}"
        res = requests.get(url).json()

        items = res.get('items', [])
        if not items:
            break

        for item in items:
            volume_info = item.get('volumeInfo', {})
            books.append({
                'title': volume_info.get('title', 'No Title'),
                'authors': volume_info.get('authors', []),
                'year': (volume_info.get('publishedDate', '') or '')[:4],
                'source': 'GoogleBooks',
                'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail')
            })

        count = len(items)
        start_index += count
        if remaining != float('inf'):
            remaining -= count

        # safety: if API sent fewer items than requested chunk, it's exhausted
        if count < fetch_n:
            break

    return books
