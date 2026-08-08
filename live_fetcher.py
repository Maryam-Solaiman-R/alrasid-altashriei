import hashlib
import re
from html import unescape
from urllib.parse import urljoin, urlparse, urlencode, quote_plus

import requests

from live_connectors import connector_for_url

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36 AlRasid/2.2"
DEFAULT_TIMEOUT = (6, 18)
MAX_PAGE_BYTES = 3_000_000

AR_STOP = {"في","من","على","إلى","الى","عن","ما","هل","التي","الذي","هذه","هذا","مع","أو","او","ثم","تم","لدي","كان","كانت","نظام","لائحة","اللائحة","النظام"}


def _tokens(text: str):
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", (text or "").lower())
    return [x for x in text.split() if len(x) > 1 and x not in AR_STOP]


def fetch(url: str, timeout=DEFAULT_TIMEOUT):
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar-SA,ar;q=0.9,en-US;q=0.7,en;q=0.5",
        "Cache-Control": "no-cache",
    }
    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    body = r.content[:MAX_PAGE_BYTES]
    return {"url": r.url, "status": r.status_code, "content_type": r.headers.get("Content-Type", ""), "sha256": hashlib.sha256(body).hexdigest(), "body": body}


def _strip_html(value: str):
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value or "", flags=re.I|re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I|re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _links(html: str, base_url: str):
    out, seen = [], set()
    for href, label in re.findall(r'''href=["']([^"']+)["'][^>]*>(.*?)</a>''', html, re.I|re.S):
        url = urljoin(base_url, unescape(href))
        if url in seen or not connector_for_url(url):
            continue
        seen.add(url)
        out.append({"url": url, "label": _strip_html(label)})
    return out


def _score(query: str, label: str, url: str):
    q = set(_tokens(query)); hay = " ".join(_tokens((label or "") + " " + (url or "")))
    if not q: return 0
    return sum(1 for token in q if token in hay) / len(q)


def _direct_discovery_urls(root: str, query: str):
    host = (urlparse(root).hostname or "").lower()
    if host.endswith("laws.boe.gov.sa"):
        # صفحة البحث الرسمية لهيئة الخبراء؛ لا نبدأ من مجلد عام بطيء.
        return ["https://laws.boe.gov.sa/BoeLaws/Laws/SearchDetails/?Query=" + quote_plus(query)]
    # المركز الوطني: الصفحة الرئيسة نفسها تعرض الوثائق وروابط تفاصيلها.
    return ["https://ncar.gov.sa/"]


def scan_root(root: str, query: str):
    ranked, hashes, last_error = [], [], None
    for start_url in _direct_discovery_urls(root, query):
        try:
            got = fetch(start_url)
            hashes.append(got["sha256"])
            if "html" not in got["content_type"].lower():
                continue
            html = got["body"].decode("utf-8", "replace")
            for item in _links(html, got["url"]):
                s = _score(query, item["label"], item["url"])
                if s > 0:
                    item = dict(item); item["score"] = round(s, 3); ranked.append(item)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {str(exc)[:220]}"

    if not ranked and last_error:
        raise RuntimeError(last_error)

    dedup = {}
    for item in ranked:
        old = dedup.get(item["url"])
        if not old or item["score"] > old["score"]: dedup[item["url"]] = item
    return {"root": root, "candidates": sorted(dedup.values(), key=lambda x:x["score"], reverse=True)[:12], "sha256": hashes[-1] if hashes else ""}


def fetch_candidate_text(url: str):
    got = fetch(url)
    if "html" not in got["content_type"].lower(): return {"url": got["url"], "text": "", "title": ""}
    html = got["body"].decode("utf-8", "replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)
    return {"url": got["url"], "title": _strip_html(title_match.group(1)) if title_match else "", "text": _strip_html(html)}
