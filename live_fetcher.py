import hashlib
import re
from html import unescape
from urllib.parse import urljoin, urlparse, urlencode
from urllib.request import Request, urlopen

from live_connectors import connector_for_url

UA = "Al-Rasid-Al-Tashriei/2.0 (official Saudi regulatory research)"
DEFAULT_TIMEOUT = 12
MAX_PAGE_BYTES = 3_000_000

AR_STOP = {
    "في", "من", "على", "إلى", "الى", "عن", "ما", "هل", "التي", "الذي", "هذه", "هذا",
    "مع", "أو", "او", "ثم", "تم", "لدي", "كان", "كانت", "نظام", "لائحة", "اللائحة", "النظام",
}


def _tokens(text: str):
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", (text or "").lower())
    return [x for x in text.split() if len(x) > 1 and x not in AR_STOP]


def fetch(url: str, timeout: int = DEFAULT_TIMEOUT):
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.8,en;q=0.7",
            "Connection": "close",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        body = response.read(MAX_PAGE_BYTES + 1)
        if len(body) > MAX_PAGE_BYTES:
            body = body[:MAX_PAGE_BYTES]
        return {
            "url": response.geturl(),
            "status": getattr(response, "status", 200),
            "content_type": response.headers.get("Content-Type", ""),
            "sha256": hashlib.sha256(body).hexdigest(),
            "body": body,
        }


def _strip_html(value: str):
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value or "", flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _links(html: str, base_url: str):
    out = []
    seen = set()
    for href, label in re.findall(r'''href=["']([^"']+)["'][^>]*>(.*?)</a>''', html, re.I | re.S):
        url = urljoin(base_url, unescape(href))
        if url in seen or not connector_for_url(url):
            continue
        seen.add(url)
        out.append({"url": url, "label": _strip_html(label)})
    return out


def _score(query: str, label: str, url: str):
    q = set(_tokens(query))
    hay = " ".join(_tokens((label or "") + " " + (url or "")))
    if not q:
        return 0
    matched = sum(1 for token in q if token in hay)
    return matched / len(q)


def _search_form_urls(html: str, base_url: str, query: str):
    """Build safe GET search URLs when an official page exposes a search form."""
    urls = []
    for form_attrs, form_body in re.findall(r"<form\b([^>]*)>(.*?)</form>", html, re.I | re.S):
        method_match = re.search(r'''method=["']?([^\s"'>]+)''', form_attrs, re.I)
        method = (method_match.group(1) if method_match else "get").lower()
        if method != "get":
            continue
        action_match = re.search(r'''action=["']([^"']*)["']''', form_attrs, re.I)
        action = urljoin(base_url, action_match.group(1) if action_match else base_url)
        if not connector_for_url(action):
            continue
        text_inputs = re.findall(r'''<input\b[^>]*name=["']([^"']+)["'][^>]*>''', form_body, re.I)
        for name in text_inputs[:2]:
            lname = name.lower()
            if any(k in lname for k in ("search", "query", "keyword", "text", "name", "q")):
                sep = "&" if "?" in action else "?"
                urls.append(action + sep + urlencode({name: query}))
    return urls[:2]


def scan_root(root: str, query: str):
    """Focused discovery inside one official source; never retries for minutes."""
    got = fetch(root)
    ctype = got["content_type"].lower()
    if "html" not in ctype:
        return {"root": root, "candidates": [], "sha256": got["sha256"]}

    html = got["body"].decode("utf-8", "replace")
    candidates = _links(html, got["url"])

    # Prefer links whose labels resemble the requested instrument/article.
    ranked = []
    for item in candidates:
        s = _score(query, item["label"], item["url"])
        if s > 0:
            item = dict(item)
            item["score"] = round(s, 3)
            ranked.append(item)

    # If the official site exposes a GET search form, query it and merge matching links.
    for search_url in _search_form_urls(html, got["url"], query):
        try:
            sg = fetch(search_url)
            if "html" not in sg["content_type"].lower():
                continue
            sh = sg["body"].decode("utf-8", "replace")
            for item in _links(sh, sg["url"]):
                s = _score(query, item["label"], item["url"])
                if s > 0:
                    item = dict(item)
                    item["score"] = round(s, 3)
                    ranked.append(item)
        except Exception:
            pass

    dedup = {}
    for item in ranked:
        old = dedup.get(item["url"])
        if not old or item["score"] > old["score"]:
            dedup[item["url"]] = item

    return {
        "root": root,
        "candidates": sorted(dedup.values(), key=lambda x: x["score"], reverse=True)[:12],
        "sha256": got["sha256"],
    }


def fetch_candidate_text(url: str):
    got = fetch(url)
    if "html" not in got["content_type"].lower():
        return {"url": got["url"], "text": "", "title": ""}
    html = got["body"].decode("utf-8", "replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return {
        "url": got["url"],
        "title": _strip_html(title_match.group(1)) if title_match else "",
        "text": _strip_html(html),
    }
