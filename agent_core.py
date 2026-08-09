import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from live_connectors import CONNECTORS
from live_fetcher import scan_root, fetch_candidate_text


def _article_number(question: str):
    m = re.search(r"(?:المادة|مادة)\s*[\(（]?\s*(\d{1,4})", question or "")
    return m.group(1) if m else ""


def _extract_change_metadata(text: str):
    decision = ""
    date = ""
    patterns = [
        r"(?:قرار\s+مجلس\s+الوزراء|قرار\s+وزاري|قرار)\s+(?:برقم|رقم)\s*[\(（]?\s*([^\s\)）،,]+).*?(?:بتاريخ|وتاريخ)\s*([0-9٠-٩/\-]+)",
        r"(?:مرسوم\s+ملكي|الأمر\s+الملكي|أمر\s+ملكي)\s+(?:برقم|رقم)\s*[\(（]?\s*([^\)）،,]+).*?(?:بتاريخ|وتاريخ)\s*([0-9٠-٩/\-]+)",
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
        m = re.search(rf"(?:المادة|مادة)\s*[\(（]?\s*{re.escape(article_number)}\s*[\)）]?(.{{0,2200}})", text, re.S)
        if m:
            return ("المادة " + article_number + " " + m.group(1))[:2200].strip()
    m = re.search(r"(.{0,500}(?:وثائق التعديل|مادة معدلة|تعديل|تعدل|عدلت|إحلال|يلغى|تلغى).{0,1500})", text, re.S)
    return (m.group(1) if m else text[:1600]).strip()


def _inspect_candidate(candidate, authority, article_number):
    try:
        page = fetch_candidate_text(candidate["url"])
    except Exception as exc:
        return None, f"{authority}: {type(exc).__name__}: {str(exc)[:180]}"
    text = page.get("text", "")
    if not text:
        return None, None
    decision_number, decision_date = _extract_change_metadata(text)
    excerpt = _article_excerpt(text, article_number)
    has_change = any(k in text for k in ("وثائق التعديل", "مادة معدلة", "تعديل", "تعدل", "عدلت", "إحلال", "يلغى", "تلغى"))
    return {
        "authority": authority,
        "title": candidate.get("label") or page.get("title") or "وثيقة رسمية",
        "article_number": article_number or None,
        "change_status": "وجدت إشارة رسمية إلى تعديل" if has_change else "لم تثبت إشارة تعديل في النص المسترجع",
        "change_summary": excerpt,
        "decision_number": decision_number or None,
        "decision_date": decision_date or None,
        "source_url": page.get("url") or candidate["url"],
        "confidence": "موثق من صفحة رسمية" if has_change else "يتطلب مراجعة الصفحة الرسمية",
    }, None


def ask(question: str, ncar_documents=None):
    question = " ".join((question or "").split()).strip()
    if not question:
        return {"status": "invalid_request", "message": "يرجى إدخال اسم النظام أو اللائحة، ويمكن إضافة رقم المادة."}

    article_number = _article_number(question)
    discovered, errors = [], []

    # Browser-assisted NCAR fallback: the official NCAR API permits browser CORS,
    # while some cloud hosts cannot establish TCP/443 to ncar.gov.sa.  Accept only
    # document metadata returned by that official endpoint and keep it explicitly
    # labelled as metadata (not article text).
    browser_ncar_findings = []
    browser_docs_received = 0
    for doc in (ncar_documents or [])[:10]:
        if not isinstance(doc, dict):
            continue
        browser_docs_received += 1
        doc_id = str(doc.get("id") or "").strip()
        title = str(doc.get("title_ar") or doc.get("name") or doc.get("title_en") or "").strip()
        if not doc_id or not title:
            continue
        approvals = doc.get("Approves") if isinstance(doc.get("Approves"), list) else []
        approval = approvals[0] if approvals and isinstance(approvals[0], dict) else {}
        decision_number = str(approval.get("number") or approval.get("name_ar") or "").strip() or None
        decision_date = str(approval.get("approve_date") or approval.get("date") or "").strip() or None
        browser_ncar_findings.append({
            "authority": "المركز الوطني للوثائق والمحفوظات",
            "title": title,
            "article_number": article_number or None,
            "change_status": "تم العثور على الوثيقة في فهرس NCAR الرسمي",
            "change_summary": "تم التحقق من وجود الوثيقة وبياناتها عبر واجهة البحث الرسمية للمركز. لا يُنسب نص مادة أو تعديل ما لم يمكن استرجاع صفحة الوثيقة الرسمية.",
            "decision_number": decision_number,
            "decision_date": decision_date,
            "source_url": "https://ncar.gov.sa/document-details/" + doc_id,
            "confidence": "بيانات فهرسة رسمية من NCAR",
        })

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(scan_root, root, question): connector for connector in CONNECTORS for root in connector.roots}
        for future in as_completed(jobs):
            connector = jobs[future]
            try:
                result = future.result()
                for err in result.get("errors", []):
                    errors.append({"authority": connector.authority, "stage": "discovery", "error": err})
                for item in result.get("candidates", [])[:6]:
                    discovered.append((item, connector.authority))
            except Exception as exc:
                errors.append({"authority": connector.authority, "stage": "discovery", "error": f"{type(exc).__name__}: {str(exc)[:220]}"})

    findings = list(browser_ncar_findings)
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(_inspect_candidate, c, a, article_number) for c, a in discovered[:10]]
        for future in as_completed(jobs):
            try:
                item, err = future.result()
                if item:
                    findings.append(item)
                if err:
                    errors.append({"authority": err.split(":",1)[0], "stage": "document", "error": err})
            except Exception as exc:
                errors.append({"authority": "غير محدد", "stage": "document", "error": f"{type(exc).__name__}: {str(exc)[:180]}"})

    findings.sort(key=lambda x: (x["change_status"].startswith("وجدت"), bool(x["decision_number"])), reverse=True)
    # Avoid duplicate source URLs.
    unique = []
    seen = set()
    for x in findings:
        if x["source_url"] not in seen:
            seen.add(x["source_url"]); unique.append(x)

    if not unique:
        return {
            "status": "not_found",
            "query": question,
            "article_number": article_number or None,
            "message": "تعذر استرجاع وثيقة رسمية موثقة من المصدرين المحددين. لا يعرض الراصد استنتاجًا غير مثبت.",
            "sources_checked": [c.authority for c in CONNECTORS],
            "source_errors": errors[-8:],
            "browser_fallback": {"ncar_documents_received": browser_docs_received, "used": bool(browser_ncar_findings)},
            "findings": [],
        }

    return {
        "status": "ok",
        "query": question,
        "article_number": article_number or None,
        "message": "تم استرجاع نتائج من مصادر رسمية. يعرض الراصد ما أمكن إثباته فقط.",
        "sources_checked": [c.authority for c in CONNECTORS],
        "source_errors": errors[-8:],
        "browser_fallback": {"ncar_documents_received": browser_docs_received, "used": bool(browser_ncar_findings)},
        "findings": unique[:6],
    }
