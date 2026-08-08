from datetime import datetime, timezone

from live_connectors import CONNECTORS
from live_fetcher import scan_root, fetch
from legislation_index import upsert_document


def scan_all():
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sources": [],
        "indexed_documents": 0,
    }

    for c in CONNECTORS:
        item = {
            "key": c.key,
            "authority": c.authority,
            "roots": [],
        }

        for root in c.roots:
            try:
                r = scan_root(root)
                candidates = r.get("candidates", [])
                indexed = 0
                errors = []

                for candidate in candidates[:30]:
                    try:
                        url = candidate.get("url")
                        if not url:
                            continue

                        page = fetch(url)
                        body = page.get("body", b"")

                        if isinstance(body, bytes):
                            text = body.decode("utf-8", errors="replace")
                        else:
                            text = str(body or "")

                        if not text.strip():
                            continue

                        upsert_document({
                            "source_url": url,
                            "authority": c.authority,
                            "instrument": candidate.get("title", ""),
                            "document_type": "official_source",
                            "title": candidate.get("title", ""),
                            "article_number": "",
                            "text": text,
                            "decision_number": "",
                            "decision_date": "",
                            "publication_date": "",
                            "effective_from": "",
                            "effective_to": "",
                            "transitional_rule": "",
                            "confidence": 0.8,
                        })

                        indexed += 1
                        report["indexed_documents"] += 1

                    except Exception as doc_error:
                        errors.append(str(doc_error)[:200])

                item["roots"].append({
                    "url": root,
                    "status": "ok",
                    "candidate_count": len(candidates),
                    "indexed_count": indexed,
                    "errors": errors[:5],
                    "candidates": candidates[:30],
                    "sha256": r.get("sha256"),
                })

            except Exception as e:
                item["roots"].append({
                    "url": root,
                    "status": "error",
                    "error": str(e)[:300],
                })

        report["sources"].append(item)

    return report
