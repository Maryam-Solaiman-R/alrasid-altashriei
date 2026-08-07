
from pathlib import Path
import os
from legislation_index import DB, upsert_document, all_documents
from retrieval_engine import rank_documents
from agent_core import ask

def run():
    if DB.exists(): DB.unlink()
    upsert_document({"source_url":"fixture://1","authority":"هيئة المحتوى المحلي والمشتريات الحكومية",
      "instrument":"لائحة تفضيل المحتوى المحلي","document_type":"لائحة","title":"اختبار",
      "article_number":"20","text":"تطبق متطلبات المحتوى المحلي على العقود الحكومية وفق نطاق اللائحة.",
      "effective_from":"2026-01-01","confidence":.9})
    upsert_document({"source_url":"fixture://2","authority":"جهة أخرى","instrument":"لائحة أخرى",
      "document_type":"لائحة","title":"اختبار","article_number":"3","text":"أحكام مختلفة.","confidence":.8})
    r=ask("لدي عقد حكومي وأريد معرفة أحكام المحتوى المحلي التي تنطبق على حالتي")
    assert r["status"]=="candidates_found"
    assert r["candidates"][0]["article_number"]=="20"
    assert r["understanding"]["requires_article_number"] is False
    print("OK: v1.3 indexed retrieval and agent orchestration tests passed")
if __name__=="__main__": run()
