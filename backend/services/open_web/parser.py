from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional


def extract_text_snippet(html: str, length: int = 300) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/styles
    for s in soup(['script', 'style', 'noscript']):
        s.extract()
    text = soup.get_text(separator=' ', strip=True)
    return text[:length]


def parse_page(url: str, html: str, source_type: str, discovery_reason: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find('title')
    title = title_tag.get_text().strip() if title_tag else url

    # Try to find common meta date fields
    date = None
    for name in ('article:published_time', 'og:published_time', 'date', 'pubdate'):
        meta = soup.find('meta', attrs={'property': name}) or soup.find('meta', attrs={'name': name})
        if meta and meta.get('content'):
            date = meta.get('content')
            break

    # fallback: look for time element
    if not date:
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            date = time_tag.get('datetime')
        elif time_tag:
            date = time_tag.get_text().strip()

    # Normalize date if possible
    if date:
        try:
            # try ISO parse
            parsed = datetime.fromisoformat(date)
            date = parsed.isoformat()
        except Exception:
            # leave as-is; short strings ok
            pass

    excerpt = extract_text_snippet(html, length=400)

    return {
        "title": title,
        "url": url,
        "excerpt": excerpt,
        "date": date,
        "source_type": source_type,
        "discovery_reason": discovery_reason
    }
