# backend/services/test_search.py

import sys
import os

# Make sure imports work no matter where we run this from
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your services
from services.dedupe import deduplicate_books, safe_year
from services.google_books import search_google_books
from services.open_library import search_open_library
from services.internet_archive import search_internet_archive

def test_search():
    query = "Python programming"

    print(f"Testing search for: '{query}'\n")

    try:
        print("Google Books Results:")
        google_results = search_google_books(query)
        for book in google_results[:3]:  # show top 3
            print(f" - {book}")
    except Exception as e:
        print("Error fetching Google Books results:", e)

    try:
        print("\nOpen Library Results:")
        open_lib_results = search_open_library(query)
        for book in open_lib_results[:3]:
            print(f" - {book}")
    except Exception as e:
        print("Error fetching Open Library results:", e)

    try:
        print("\nInternet Archive Results:")
        ia_results = search_internet_archive(query)
        for book in ia_results[:3]:
            print(f" - {book}")
    except Exception as e:
        print("Error fetching Internet Archive results:", e)

    # Example dedupe test
    try:
        print("\nDeduplication Test:")
        combined_books = google_results + open_lib_results + ia_results
        deduped_books = deduplicate_books(combined_books)
        print(f"Total before dedupe: {len(combined_books)}")
        print(f"Total after dedupe: {len(deduped_books)}")
    except Exception as e:
        print("Error running deduplication:", e)

if __name__ == "__main__":
    test_search()
