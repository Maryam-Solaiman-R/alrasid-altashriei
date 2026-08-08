import hashlib
import time
from urllib.request import Request, urlopen
from urllib.parse import urljoin

from live_connectors import connector_for_url, discover_candidates


UA = "Saudi-Regulatory-Monitor/1.6 (+public regulatory research)"


def fetch(url, timeout=45):
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Connection": "close",
        },
    )

    last_error = None

    for attempt in range(2):
        try:
            current_timeout = timeout if attempt == 0 else 90

            with urlopen(req, timeout=current_timeout) as r:
                body = r.read()

                return {
                    "url": r.geturl(),
                    "status": getattr(r, "status", 200),
                    "content_type": r.headers.get("Content-Type", ""),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "body": body,
                }

        except Exception as e:
            last_error = e

            if attempt == 0:
                time.sleep(2)

    raise last_error


def scan_root(root, query=None):
    """
    Scan an official source root and discover candidate
    regulatory pages.

    query is optional and is kept for compatibility with
    question-aware live search.
    """
    got = fetch(root)

    content_type = got["content_type"].lower()

    if "html" not in content_type:
        return {
            "root": root,
            "candidates": [],
            "sha256": got["sha256"],
        }

    html = got["body"].decode("utf-8", "replace")

    candidates = discover_candidates(html, root)

    normalized = []

    for candidate in candidates:
        href = candidate.get("href") or candidate.get("url")

        if not href:
            continue

        url = urljoin(root, href)

        item = dict(candidate)
        item["url"] = url

        if query:
            item["query"] = query

        normalized.append(item)

    return {
        "root": root,
        "candidates": normalized,
        "sha256": got["sha256"],
    }
