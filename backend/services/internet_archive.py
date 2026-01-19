import requests

def search_internet_archive(query, max_results=10):
    url = f"https://archive.org/advancedsearch.php?q={query}&fl[]=title,creator,year,mediatype&rows={max_results}&output=json"
    res = requests.get(url).json()
    books = []

    for doc in res.get("response", {}).get("docs", []):
        # Normalize creators/authors to always be a list
        creators = doc.get("creator", [])
        if isinstance(creators, str):
            creators = [creators]
        elif creators is None:
            creators = []

        # Use a placeholder image since IA covers vary widely
        books.append({
            "title": doc.get("title", "No Title"),
            "authors": creators,
            "year": doc.get("year", ""),
            "source": "InternetArchive",
            "thumbnail": "https://via.placeholder.com/60x90?text=No+Image"
        })
    return books
