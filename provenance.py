from urllib.parse import urlparse
def provenance_record(source_url, authority, retrieved_at=None, sha256=None,
                      decision_number=None, decision_date=None, publication_date=None,
                      effective_rule=None, document_status="candidate"):
    return {"source_url":source_url,"source_host":(urlparse(source_url).hostname or ""),
      "authority":authority,"retrieved_at":retrieved_at,"sha256":sha256,
      "decision_number":decision_number,"decision_date":decision_date,
      "publication_date":publication_date,"effective_rule":effective_rule,
      "document_status":document_status}
def verification_state(record):
    missing=[]
    for k,label in (("source_url","المصدر الرسمي"),("authority","الجهة"),
                    ("decision_number","رقم أداة التعديل"),("decision_date","تاريخ أداة التعديل")):
        if not record.get(k): missing.append(label)
    if not record.get("effective_rule"): missing.append("قاعدة النفاذ")
    if record.get("document_status")=="draft":
        return {"status":"draft","usable_for_applicability":False,"missing":missing}
    return {"status":"verified" if not missing else "partial",
            "usable_for_applicability":not missing,"missing":missing}
