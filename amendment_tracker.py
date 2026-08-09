from __future__ import annotations

import re
from article_change_engine import extract_articles, diff_summary
from reader_bridge import read_ncar_document_and_resources

CHANGE_WORDS = ("تعديل","المعدلة","تعديلات","إلغاء","استبدال","إحلال","تحديث")
AR_NUM = str.maketrans("٠١٢٣٤٥٦٧٨٩","0123456789")

def _norm(s):
    return re.sub(r"\s+"," ",(s or "").translate(AR_NUM)).strip()

def _approval(doc):
    arr = doc.get("Approves") if isinstance(doc.get("Approves"), list) else []
    a = arr[0] if arr and isinstance(arr[0], dict) else {}
    return {
        "decision_number": _norm(str(a.get("number") or a.get("name_ar") or "")) or None,
        "decision_date": _norm(str(a.get("approve_date") or a.get("date") or "")) or None,
        "decision_type": _norm(str(a.get("name_ar") or a.get("name") or "")) or None,
    }

def _title(doc):
    return _norm(str(doc.get("title_ar") or doc.get("name") or doc.get("title_en") or ""))

def _is_change_doc(doc):
    t=_title(doc)
    return any(w in t for w in CHANGE_WORDS)

def _article_nums(text):
    t=_norm(text)
    nums=[]
    # المادة 88 / المواد (88، 111، 114)
    for m in re.finditer(r"(?:المادة|المواد|مادة)\s*(?:رقم\s*)?[\(（]?\s*([0-9][0-9\s،,و\-–]{0,80})", t):
        chunk=m.group(1)
        for n in re.findall(r"\d{1,4}",chunk):
            if n not in nums: nums.append(n)
    return nums[:30]

def _metadata_from_text(text):
    t=_norm(text)
    number=date=None
    pats=[
      r"(?:قرار\s+وزاري|قرار\s+مجلس\s+الوزراء|قرار)\s+(?:برقم|رقم)\s*[\(（]?\s*([A-Za-zأ-ي/0-9\-]+).*?(?:بتاريخ|وتاريخ)\s*([0-9/\-]+)",
      r"(?:مرسوم\s+ملكي|أمر\s+ملكي)\s+(?:برقم|رقم)\s*[\(（]?\s*([A-Za-zأ-ي/0-9\-]+).*?(?:بتاريخ|وتاريخ)\s*([0-9/\-]+)",
    ]
    for p in pats:
        m=re.search(p,t,re.S)
        if m:
            number,date=m.group(1),m.group(2); break
    return number,date

def _after_text(text, article):
    t=_norm(text)
    if article:
        # A decision often says: تعديل المادة (...) لتكون بالنص الآتي: ...
        p=rf"(?:المادة|مادة)\s*[\(（]?\s*{re.escape(str(article))}\s*[\)）]?.{{0,350}}?(?:لتكون|ليكون|يصبح|يكون)\s*(?:نصها|بالنص)?\s*(?:الآتي|التالي)?\s*[:：\-–]?\s*(.{{80,2600}})"
        m=re.search(p,t,re.S)
        if m:
            body=m.group(1)
            stop=re.search(r"(?:المادة|مادة)\s*[\(（]?\s*\d{1,4}",body)
            if stop: body=body[:stop.start()]
            return body[:2400].strip()
    return None

def _article_map(text):
    return {x["article_number"]:x["text"] for x in extract_articles(text or "")}

def build_amendment_timeline(instrument: str, ncar_documents: list[dict], requested_article: str | None=None):
    docs=[d for d in (ncar_documents or []) if isinstance(d,dict) and d.get("id")]
    if not docs:
        return {"status":"no_ncar_documents","events":[],"documents_received":0}

    # De-duplicate API objects by encrypted NCAR document id.
    uniq=[]; seen=set()
    for d in docs:
        k=str(d.get("id"))
        if k not in seen:
            seen.add(k); uniq.append(d)
    docs=uniq[:30]

    base_docs=[d for d in docs if not _is_change_doc(d)]
    change_docs=[d for d in docs if _is_change_doc(d)]
    # If NCAR returns an amended consolidated regulation without the word "تعديل",
    # preserve it as a potential version.
    for d in base_docs:
        if "المعدلة" in _title(d) and d not in change_docs:
            change_docs.append(d)

    pages_by_id={}
    reader_errors=[]
    # Read base docs first so we have a candidate previous text.
    for d in (base_docs[:3]+change_docs[:10]):
        did=str(d.get("id"))
        if did in pages_by_id: continue
        pages,errs=read_ncar_document_and_resources(did,max_resources=3)
        pages_by_id[did]=pages
        reader_errors.extend(errs[-2:])

    # Pick the richest original/base text as a baseline.
    baseline_map={}
    baseline_source=None
    baseline_title=None
    for d in base_docs[:3]:
        did=str(d.get("id"))
        all_text="\n".join(p.get("text","") for p in pages_by_id.get(did,[]))
        amap=_article_map(all_text)
        if len(amap)>len(baseline_map):
            baseline_map=amap; baseline_source="https://ncar.gov.sa/document-details/"+did; baseline_title=_title(d)

    events=[]
    for d in change_docs[:12]:
        did=str(d.get("id")); title=_title(d)
        text="\n".join(p.get("text","") for p in pages_by_id.get(did,[]))
        ap=_approval(d)
        tnum,tdate=_metadata_from_text(text)
        if not ap["decision_number"] and tnum: ap["decision_number"]=tnum
        if not ap["decision_date"] and tdate: ap["decision_date"]=tdate
        nums=_article_nums(title+"\n"+text)
        if requested_article and requested_article not in nums:
            # If we can extract the requested article's new text, keep it even if title omitted number.
            if not _after_text(text, requested_article):
                continue
            nums=[requested_article]
        if not nums and requested_article:
            nums=[requested_article]

        event={
          "title":title,
          "decision_number":ap["decision_number"],
          "decision_date":ap["decision_date"],
          "decision_type":ap["decision_type"],
          "source_url":"https://ncar.gov.sa/document-details/"+did,
          "affected_articles":nums,
          "changes":[]
        }

        for n in (nums or [None])[:20]:
            after=_after_text(text,n) if n else None
            before=baseline_map.get(str(n)) if n else None
            comparison=None
            if before and after:
                comparison=diff_summary(before,after)
                # Advance baseline so later amendments compare to the most recently reconstructed text.
                baseline_map[str(n)]=after
            event["changes"].append({
              "article_number":n,
              "before_text":before,
              "after_text":after,
              "comparison":comparison,
              "evidence_excerpt": (_norm(text)[:1800] if text else None),
            })
        events.append(event)

    # sort by decision date where the string is comparable enough; otherwise stable order
    events.sort(key=lambda e:(e.get("decision_date") or "",e.get("decision_number") or ""))
    return {
      "status":"ok" if events else "no_amendment_events",
      "instrument":instrument,
      "requested_article":requested_article,
      "documents_received":len(docs),
      "change_documents":len(change_docs),
      "baseline_title":baseline_title,
      "baseline_source":baseline_source,
      "reader_errors":reader_errors[-6:],
      "events":events,
    }
