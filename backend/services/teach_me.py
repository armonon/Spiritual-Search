"""Knowledge exploration module for Personal Librarian."""
import json
from run_multi_pilot import run  # to reuse search

def teach_me(topic: str):
    """Teach me about a topic: return recommended books and related subjects."""
    # For simplicity, use the search results and extract subjects as related
    import json
    from io import StringIO
    import sys

    # Capture output of run
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    run(topic, use_local=True)
    sys.stdout = old_stdout

    data = json.loads(captured_output.getvalue())
    results = data["results"]
    related_subjects = set()
    recommended_books = []
    for r in results[:10]:  # top 10
        recommended_books.append({"title": r["title"], "authors": r["authors"], "year": r["year"]})
        subjects = r.get("subjects", [])
        related_subjects.update(subjects)

    return {
        "topic": topic,
        "recommended_books": recommended_books,
        "related_subjects": list(related_subjects)[:5],  # top 5
        "reading_order": "Read foundational books first, then modern applications."
    }

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "fasting"
    out = teach_me(topic)
    print(json.dumps(out, indent=2, ensure_ascii=False))
