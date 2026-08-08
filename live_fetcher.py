import hashlib
import re
from html import unescape
from urllib.parse import urljoin, urlparse, quote_plus, parse_qs

import requests

from live_connectors import connector_for_url

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
DEFAULT_TIMEOUT = (4, 10)
MAX_PAGE_BYTES = 2_000_000

AR_STOP = {"في","من","على","إلى","الى","عن","ما","هل","التي","الذي","هذه","هذا","مع","أو","او","ثم","تم","لدي","كان","كانت"}


def _tokens(text: str):
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", (text or "").lower())
    return [x for x in text.split() if len(x) > 1 and x not in AR_STOP]


def fetch(url: str, timeout=DEFAULT_TIMEOUT):
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar-SA,ar;q=0.9,en-US;q=0.7,en;q=0.5",
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


def _score(query: str, label: str, url: str, snippet: str = ""):
    q = set(_tokens(query))
    hay = " ".join(_tokens((label or "") + " " + (snippet or "") + " " + (url or "")))
    if not q:
        return 0
    return sum(1 for token in q if token in hay) / len(q)


def _official_links(html: str, base_url: str):
    out, seen = [], set()
    for href, label in re.findall(r'''href=["']([^"']+)["'][^>]*>(.*?)</a>''', html, re.I|re.S):
        url = urljoin(base_url, unescape(href))
        # unwrap common search redirect URLs
        if "google." in (urlparse(url).hostname or "") and urlparse(url).path == "/url":
            url = parse_qs(urlparse(url).query).get("q", [url])[0]
        if not connector_for_url(url) or url in seen:
            continue
        seen.add(url)
        out.append({"url": url, "label": _strip_html(label), "snippet": ""})
    return out


def _search_engine_candidates(query: str, host: str):
    """Fallback discovery only. Results are accepted only when destination is one of our two official domains."""
    q = quote_plus(f'site:{host} "{query}"')
    urls = [
        "https://www.google.com/search?q=" + q + "&hl=ar",
        "https://www.bing.com/search?q=" + q + "&setlang=ar-SA",
    ]
    found, errors = [], []
    for u in urls:
        try:
            got = fetch(u, timeout=(4, 8))
            html = got["body"].decode("utf-8", "replace")
            # Generic official links
            found.extend(_official_links(html, got["url"]))
            # Also catch raw official URLs embedded in search markup
            for raw in re.findall(r'https?://[^"<>\s&]+', unescape(html)):
                raw = raw.rstrip(".,;')]")
                if connector_for_url(raw):
                    found.append({"url": raw, "label": "نتيجة من فهرس البحث", "snippet": ""})
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {str(exc)[:120]}")
    return found, errors




def _ncar_search_api(query: str):
    """Search NCAR using the same public JSON endpoint used by ncar.gov.sa.

    The endpoint was captured from the official site's own search page.  Keep the
    payload deliberately narrow: only the document name is supplied; all other
    filters remain unset, matching the website request.
    """
    endpoint = "https://ncar.gov.sa/api/index.php/api/documents/document-search/1/10/approveDate/DESC"
    payload = {
        "approveTool_id": None,
        "documentCategory_id": None,
        "name": query,
        "ApproveDate": None,
        "approveDate_from": None,
        "approveDate_to": None,
        "omAlQourah_version": None,
        "omAlQourah_date": None,
        "is_valid": None,
        "is_printed": None,
        "is_translated": None,
        "generalCategory_id": [],
        "particularCategory_id": [],
        "governmentalAgency_id": None,
        "governmentalAgency_childId": None,
        "alphabeticalTopic_id": None,
        "alphabeticalCategory_id": None,
        "alphabeticalSubCategory_id": [],
        "releaseOrgId": None,
        "identical": 1,
        "number": None,
        "PublishingStatus": None,
    }
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://ncar.gov.sa",
        "Referer": "https://ncar.gov.sa/",
        "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.6",
    }
    r = requests.post(endpoint, json=payload, headers=headers, timeout=(5, 15))
    r.raise_for_status()
    data = r.json()

    # NCAR has changed envelope names over time. Walk the JSON and collect
    # document-shaped objects instead of binding the connector to one envelope.
    docs = []
    seen_obj = set()
    def walk(value):
        if isinstance(value, dict):
            oid = id(value)
            if oid in seen_obj:
                return
            seen_obj.add(oid)
            if value.get("id") and (value.get("title_ar") or value.get("title_en") or value.get("name")):
                docs.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)

    out, seen = [], set()
    for doc in docs:
        doc_id = str(doc.get("id") or "").strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        title = str(doc.get("title_ar") or doc.get("name") or doc.get("title_en") or "وثيقة رسمية").strip()
        url = "https://ncar.gov.sa/document-details/" + doc_id
        out.append({
            "url": url,
            "label": title,
            "snippet": "",
            "score": round(max(_score(query, title, url), 0.55), 3),
            "discovery": "ncar_official_api",
            "ncar_id": doc_id,
        })
    return out


def _direct_discovery_urls(root: str, query: str):
    host = (urlparse(root).hostname or "").lower()
    if host.endswith("laws.boe.gov.sa"):
        return [
            "https://laws.boe.gov.sa/BoeLaws/Laws/SearchDetails/?Query=" + quote_plus(query),
            "https://laws.boe.gov.sa/boelaws/laws/lawupdated/1?IsDisplayWithUpdated=True&Name=" + quote_plus(query),
        ]
    return ["https://ncar.gov.sa/"]


def scan_root(root: str, query: str):
    host = (urlparse(root).hostname or "").lower()
    ranked, hashes, errors = [], [], []

    # NCAR is a JavaScript application. Use its official JSON search API first
    # instead of scraping the home page. This mirrors the request made by the
    # official website itself and is substantially more reliable.
    if host.endswith("ncar.gov.sa"):
        try:
            ranked.extend(_ncar_search_api(query))
        except Exception as exc:
            errors.append(f"ncar_api:{type(exc).__name__}: {str(exc)[:180]}")

    # For BOE, and as a secondary NCAR fallback, try the official site directly.
    for start_url in _direct_discovery_urls(root, query):
        try:
            got = fetch(start_url)
            hashes.append(got["sha256"])
            if "html" not in got["content_type"].lower():
                continue
            html = got["body"].decode("utf-8", "replace")
            for item in _official_links(html, got["url"]):
                s = _score(query, item["label"], item["url"])
                if s > 0:
                    item["score"] = round(s, 3)
                    item["discovery"] = "official_site"
                    ranked.append(item)
        except Exception as exc:
            errors.append(f"direct:{type(exc).__name__}: {str(exc)[:160]}")

    # If the government host is unreachable from Render, discover the exact official document URL
    # through a public search index. We still accept ONLY URLs on the two official domains.
    if not ranked:
        candidates, search_errors = _search_engine_candidates(query, host)
        errors.extend("index:" + x for x in search_errors)
        for item in candidates:
            s = _score(query, item.get("label", ""), item["url"], item.get("snippet", ""))
            item["score"] = round(max(s, 0.05), 3)
            item["discovery"] = "official_url_via_search_index"
            ranked.append(item)

    dedup = {}
    for item in ranked:
        old = dedup.get(item["url"])
        if not old or item["score"] > old["score"]:
            dedup[item["url"]] = item

    return {
        "root": root,
        "candidates": sorted(dedup.values(), key=lambda x: x["score"], reverse=True)[:10],
        "sha256": hashes[-1] if hashes else "",
        "errors": errors,
    }


def fetch_candidate_text(url: str):
    got = fetch(url)
    if "html" not in got["content_type"].lower():
        return {"url": got["url"], "text": "", "title": ""}
    html = got["body"].decode("utf-8", "replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)
    return {"url": got["url"], "title": _strip_html(title_match.group(1)) if title_match else "", "text": _strip_html(html)}
