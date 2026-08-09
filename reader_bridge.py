from __future__ import annotations

import os
import re
from urllib.parse import quote
import requests

READER_BASE = "https://r.jina.ai/"
SEARCH_BASE = "https://s.jina.ai/"
UA = "Mozilla/5.0 (compatible; AlRasidAltashriei/2.7; +https://github.com/)"

def _headers():
    h = {
        "User-Agent": UA,
        "Accept": "text/plain, text/markdown;q=0.9, */*;q=0.1",
    }
    key = (os.getenv("JINA_API_KEY") or "").strip()
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h

def _get(url: str, timeout: int = 24) -> str:
    r = requests.get(url, headers=_headers(), timeout=timeout)
    r.raise_for_status()
    return (r.text or "")[:500000]

def _reader_get(target_url: str, timeout: int = 24) -> str:
    return _get(READER_BASE + target_url, timeout=timeout)

def _official_urls(text: str, domain: str) -> list[str]:
    urls, seen = [], set()
    pattern = r"https://" + re.escape(domain) + r"/[^\s\)\]\>\"']+"
    for u in re.findall(pattern, text or "", flags=re.I):
        u = u.replace("\\", "").rstrip(".,؛،)")
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls

def _query_variants(query: str) -> list[str]:
    q = " ".join((query or "").split()).strip()
    if not q:
        return []
    out = [q]
    # Common partial user wording: make discovery less brittle without changing the user's intent.
    if "المنافسات" in q and "المشتريات" not in q:
        out.append(q + " والمشتريات الحكومية")
    if "المشتريات" in q and "المنافسات" not in q:
        out.append("المنافسات و" + q)
    # Remove generic request words if user types a sentence instead of a title.
    cleaned = re.sub(r"\b(ابحث|تحقق|تأكد|عن|في|النظام|اللائحة|نظام|لائحة)\b", " ", q)
    cleaned = " ".join(cleaned.split())
    if cleaned and cleaned not in out:
        out.append(cleaned)
    return out[:3]

def discover_official(query: str, domain: str, limit: int = 6) -> tuple[list[str], list[str]]:
    """Use Jina Search only to DISCOVER URLs, then accept only official-domain URLs."""
    errors, found = [], []
    for q in _query_variants(query):
        search_q = f'{q} site:{domain}'
        try:
            text = _get(SEARCH_BASE + quote(search_q), timeout=24)
            for u in _official_urls(text, domain):
                if u not in found:
                    found.append(u)
                    if len(found) >= limit:
                        return found, errors
        except Exception as exc:
            errors.append(f"search:{type(exc).__name__}:{str(exc)[:180]}")
    return found[:limit], errors

def read_official_url(url: str) -> tuple[dict | None, str | None]:
    try:
        text = _reader_get(url)
        if not text.strip():
            return None, None
        title = "وثيقة رسمية"
        m = re.search(r"^Title:\s*(.+)$", text, re.M)
        if m:
            title = m.group(1).strip()[:240]
        return {"url": url, "text": text, "title": title}, None
    except Exception as exc:
        return None, f"reader:{type(exc).__name__}:{str(exc)[:180]}"

def search_and_read(query: str, domain: str, limit: int = 4) -> tuple[list[dict], list[str]]:
    urls, errors = discover_official(query, domain, limit=max(limit, 6))
    docs = []
    for u in urls:
        # Prefer real content/detail pages over generic home/search pages.
        if domain == "laws.boe.gov.sa":
            if not any(x in u for x in ("/Viewer/", "/SearchDetails/", "/LawDetails/")):
                continue
        if domain == "ncar.gov.sa":
            if "/document-details/" not in u:
                continue
        page, err = read_official_url(u)
        if err:
            errors.append(err)
        if page:
            docs.append(page)
        if len(docs) >= limit:
            break
    return docs, errors
