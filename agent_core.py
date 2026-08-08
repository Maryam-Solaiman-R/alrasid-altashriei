import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from live_connectors import CONNECTORS
from live_fetcher import scan_root, fetch_candidate_text


def _article_number(question: str):
    m = re.search(r"(?:المادة|مادة)\s*[\(（]?\s*(\d{1,4})", question or "")
    return m.group(1) if m else ""


def _extract_change_metadata(text: str):
    """Conservative extraction: only fields explicitly present in the official page text."""
    decision = ""
    date = ""
    patterns = [
        r"(?:قرار\s+مجلس\s+الوزراء|قرار)\s+رقم\s*[\(（]?\s*([^\s\)）،,]+).*?وتاريخ\s*([0-9٠-٩/\-]+)",
        r"(?:مرسوم\s+ملكي|الأمر\s+الملكي|أمر\s+ملكي)\s+رقم\s*[\(（]?\s*([^\)）،,]+).*?وتاريخ\s*([0-9٠-٩/\-]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text or "", re.S)
        if m:
            decision = re.sub(r"\s+", " ", m.group(1)).strip()
            date = m.group(2).strip()
            break
    return decision, date


def _article_excerpt(text: str, article_number: str):
    if not text:
        return ""
    if article_number:
        patterns = [
            rf"(?:المادة|مادة)\s*[\(（]?\s*{re.escape(article_number)}\s*[\)）]?(.{{0,1800}})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.S)
            if m:
                return ("المادة " + article_number + " " + m.group(1))[:1800].strip()
    # Look for explicit amendment language before falling back to a short page excerpt.
    m = re.search(r"(.{0,450}(?:تعديل|تعدل|عدلت|إحلال|يلغى|تلغى|مادة معدلة).{0,1100})", text, re.S)
    return (m.group(1) if m else text[:1400]).strip()


def _inspect_candidate(candidate, authority, question, article_number):
    try:
        page = fetch_candidate_text(candidate["url"])
    except Exception:
        return None
    text = page.get("text", "")
    if not text:
        return None

    decision_number, decision_date = _extract_change_metadata(text)
    excerpt = _article_excerpt(text, article_number)
    has_change_language = any(k in text for k in ("مادة معدلة", "تعديل", "تعدل", "عدلت", "إحلال", "يلغى", "تلغى"))

    return {
        "authority": authority,
        "title": candidate.get("label") or page.get("title") or "وثيقة رسمية",
        "article_number": article_number,
        "change_status": "وجدت إشارة رسمية إلى تعديل" if has_change_language else "لم تثبت إشارة تعديل في النص المسترجع",
        "change_summary": excerpt,
        "decision_number": decision_number,
        "decision_date": decision_date,
        "source_url": page.get("url") or candidate["url"],
        "confidence": "موثق من صفحة رسمية" if has_change_language else "يتطلب مراجعة الصفحة الرسمية",
    }


def ask(question: str):
    question = " ".join((question or "").split()).strip()
    if not question:
        return {"status": "invalid_request", "message": "يرجى إدخال اسم النظام أو اللائحة، ويمكن إضافة رقم المادة."}

    article_number = _article_number(question)
    discovered = []
    errors = []

    # المصدران يعملان بالتوازي حتى لا يتسبب بطء أحدهما في تعليق الآخر مدة طويلة.
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {}
        for connector in CONNECTORS:
            for root in connector.roots:
                jobs[pool.submit(scan_root, root, question)] = connector
        for future in as_completed(jobs):
            connector = jobs[future]
            try:
                result = future.result()
                for item in result.get("candidates", [])[:6]:
                    discovered.append((item, connector.authority))
            except Exception as exc:
                errors.append({"authority": connector.authority, "error": f"{type(exc).__name__}: {str(exc)[:220]}"})

    # فحص أفضل النتائج فقط؛ الهدف السرعة والدقة لا الزحف الشامل.
    findings = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(_inspect_candidate, c, a, question, article_number) for c, a in discovered[:8]]
        for future in as_completed(jobs):
            try:
                item = future.result()
                if item:
                    findings.append(item)
            except Exception:
                pass

    # النتائج ذات إشارة التعديل أولاً.
    findings.sort(key=lambda x: (x["change_status"].startswith("وجدت"), bool(x["decision_number"])), reverse=True)

    if not findings:
        return {
            "status": "not_found",
            "query": question,
            "article_number": article_number or None,
            "message": "لم يتم العثور على نتيجة موثقة ضمن المصدرين الرسميين المحددين. لا يعرض الراصد استنتاجًا غير مثبت.",
            "sources_checked": [c.authority for c in CONNECTORS],
            "source_errors": errors,
            "findings": [],
        }

    return {
        "status": "ok",
        "query": question,
        "article_number": article_number or None,
        "message": "تم استرجاع نتائج من المصادر الرسمية. يرجى الاعتماد على رابط المصدر عند اتخاذ قرار مهني أو نظامي.",
        "sources_checked": [c.authority for c in CONNECTORS],
        "source_errors": errors,
        "findings": findings[:6],
    }
