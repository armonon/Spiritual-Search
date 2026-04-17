import requests
from .seeds import FORUM_SEEDS
from ..parser import parse_page
from ..filter import is_login_required, contains_pii


def discover_forums(query: str, max_results=None):
    results = []
    for url in FORUM_SEEDS:
        try:
            resp = requests.get(url, timeout=8, headers={'User-Agent': 'OpenWebDiscoveryBot/1.0'})
        except Exception:
            continue

        if is_login_required(resp):
            continue

        # Parse first post only: find first <article> or first <p>
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text or '', 'html.parser')
            first_post = None
            # common forum structures
            article = soup.find('article')
            if article:
                first_post = article
            else:
                # fallback: first post container
                post = soup.find(class_='post') or soup.find(class_='thread')
                if post:
                    first_post = post
                else:
                    p = soup.find('p')
                    first_post = p

            excerpt_html = first_post.decode_contents() if first_post else (resp.text or '')

            if query.lower() in (excerpt_html or '').lower():
                parsed = parse_page(url, excerpt_html, 'public_forum', 'Curated forum seed (first post only)')
                if contains_pii(parsed.get('excerpt')):
                    continue
                results.append(parsed)
        except Exception:
            continue

        if max_results and len(results) >= max_results:
            break

    return results
