import requests


def search_internet_archive(query, max_results=10):
    """
    Fetch up to `max_results` docs from Internet Archive advancedsearch.
    The API supports `rows` and `page`/`start`-style parameters; we'll fetch in chunks
    until we reach `max_results` or the API returns fewer items than requested.
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
        url = (
            f"https://archive.org/advancedsearch.php?q={query}&fl[]=title,creator,year,mediatype"
            f"&rows={fetch_n}&offset={offset}&output=json"
        )
        res = requests.get(url).json()

        docs = res.get('response', {}).get('docs', [])
        if not docs:
            break

        for doc in docs:
            creators = doc.get('creator', [])
            if isinstance(creators, str):
                creators = [creators]
            elif creators is None:
                creators = []

            books.append({
                'title': doc.get('title', 'No Title'),
                'authors': creators,
                'year': doc.get('year', ''),
                'source': 'InternetArchive',
                'thumbnail': 'https://via.placeholder.com/60x90?text=No+Image'
            })

        count = len(docs)
        offset += count
        if remaining != float('inf'):
            remaining -= count

        if count < fetch_n:
            break

    return books
