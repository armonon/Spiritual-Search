"""
Curated seed list for Open Web v1. Each seed is intentionally small and curated.
Do NOT expand this list automatically.
"""

# Minimal curated seeds. In a real deployment this would be larger and curated
# by humans. Keep domains and a representative page URL.
SEEDS = [
    {
        "url": "https://www.gutenberg.org/",
        "source_type": "independent_site",
        "reason": "Curated independent literature archive"
    },
    {
        "url": "https://scripting.com/",
        "source_type": "blog",
        "reason": "Curated personal/technical blog"
    },
    {
        "url": "https://web.archive.org/",
        "source_type": "archive",
        "reason": "Archive.org snapshots for archived public pages"
    }
]

# Small list of allowed domains (for quick membership checks)
ALLOWED_DOMAINS = ["gutenberg.org", "scripting.com", "web.archive.org"]
