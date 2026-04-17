import re
from urllib.parse import urlparse
from typing import Optional
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(\d{2,3}\)|\d{2,4})[\s-]?\d{3,4}[\s-]?\d{3,4}\b")


def is_login_required(resp) -> bool:
    # Status codes indicating restricted content
    if resp.status_code in (401, 403):
        return True

    # If page contains password inputs, treat as protected
    try:
        soup = BeautifulSoup(resp.text or '', 'html.parser')
        if soup.find('input', attrs={'type': 'password'}):
            return True
    except Exception:
        pass

    # Heuristic: presence of 'login' or 'sign in' in text near forms
    text = (resp.text or '').lower()
    if 'login' in text[:500] or 'sign in' in text[:500]:
        return True

    return False


def contains_pii(text: Optional[str]) -> bool:
    if not text:
        return False
    if EMAIL_RE.search(text):
        return True
    if PHONE_RE.search(text):
        return True
    return False


def allowed_by_robots(url: str, rp) -> bool:
    # rp is an instance of urllib.robotparser.RobotFileParser already set to the robots.txt URL
    try:
        return rp.can_fetch('*', url)
    except Exception:
        # If robots check fails, be conservative and disallow
        return False
 