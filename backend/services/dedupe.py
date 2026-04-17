from typing import List, Dict

def safe_year(year):
    """Ensure year is an integer if possible, else None."""
    try:
        return int(year)
    except (TypeError, ValueError):
        return None

def deduplicate_books(books: List[Dict]) -> List[Dict]:
    """
    Deduplicate a list of books.
    Uses title + author as unique key.
    """
    seen = set()
    unique_books = []

    for book in books:
        title = book.get("title", "").strip().lower()
        authors = ", ".join(book.get("authors", [])).strip().lower()
        key = f"{title}|{authors}"

        if key not in seen:
            seen.add(key)
            book["year"] = safe_year(book.get("year"))
            unique_books.append(book)

    return unique_books
