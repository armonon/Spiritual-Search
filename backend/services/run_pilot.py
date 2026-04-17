"""Simple runner for the Personal Librarian prototype."""
from personal_librarian import search_topic
import json
import sys


def run(topic: str):
    out = search_topic(topic)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "fasting"
    run(topic)
