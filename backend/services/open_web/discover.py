import requests
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from .sources import SEEDS
from .parser import parse_page
from .filter import is_login_required, contains_pii


def _get_robots_for_domain(domain: str) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = f"https://{domain}/robots.txt"
    try:
        # Use requests with timeout to avoid blocking on slow robots.txt
        import requests
        resp = requests.get(robots_url, timeout=2, headers={'User-Agent': 'OpenWebDiscoveryBot/1.0'})
        if resp.status_code == 200 and resp.text:
            rp.parse(resp.text.splitlines())
        else:
            # empty rules -> conservative allow nothing
            rp.parse([])
    except Exception:
        # If robots.txt not reachable, conservative: allow nothing
        try:
            rp.parse([])
        except Exception:
            pass
    return rp


def discover_sites(query: str, max_results=None):
    """
    For each curated seed, fetch its URL and include the page if it contains the query text.
    This is intentionally seed-based and one-level only.
    """
    pages = []
    for seed in SEEDS:
        url = seed.get('url')
        domain = urlparse(url).netloc
        rp = _get_robots_for_domain(domain)
        try:
            if not rp.can_fetch('*', url):
                continue
        except Exception:
            continue

        try:
            resp = requests.get(url, timeout=6, headers={'User-Agent': 'OpenWebDiscoveryBot/1.0'})
        except Exception:
            continue

        if is_login_required(resp):
            continue

        text = (resp.text or '').lower()
        if query.lower() in text:
            parsed = parse_page(url, resp.text, seed.get('source_type', 'independent_site'), seed.get('reason', 'seed match'))
            # redact excerpts containing PII
            if contains_pii(parsed.get('excerpt')):
                continue
            pages.append(parsed)

        # follow outbound links one level deep only (from seed page) but only if they stay on allowed domains
        # to respect the discovery policy, we do not follow extensively
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text or '', 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                child = urljoin(url, href)
                child_domain = urlparse(child).netloc
                # only follow if same domain or archive.org
                if child_domain.endswith(domain) or 'archive.org' in child_domain:
                    try:
                        if not rp.can_fetch('*', child):
                            continue
                    except Exception:
                        continue
                    try:
                        cresp = requests.get(child, timeout=3, headers={'User-Agent': 'OpenWebDiscoveryBot/1.0'})
                    except Exception:
                        continue
                    if is_login_required(cresp):
                        continue
                    if query.lower() in (cresp.text or '').lower():
                        parsed = parse_page(child, cresp.text, seed.get('source_type', 'independent_site'), f"linked from {url}")
                        if contains_pii(parsed.get('excerpt')):
                            continue
                        pages.append(parsed)
        except Exception:
            pass

        # early stop if we have enough
        if max_results and len(pages) >= max_results:
            break

    return pages[:max_results] if max_results else pages