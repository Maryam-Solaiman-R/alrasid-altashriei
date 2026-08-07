
from legislation_index import upsert_document
def seed():
    docs=[
      {"source_url":"fixture://local-content","authority":"هيئة المحتوى المحلي والمشتريات الحكومية",
       "instrument":"لائحة اختبار لتفضيل المحتوى المحلي","document_type":"لائحة","title":"بيانات اختبار غير رسمية",
       "article_number":"10","text":"يلتزم المتعاقد بمتطلبات المحتوى المحلي وفق الأحكام المحددة في اللائحة.",
       "decision_number":"TEST","effective_from":"2026-01-01","confidence":0.2},
      {"source_url":"fixture://cyber","authority":"الهيئة الوطنية للأمن السيبراني",
       "instrument":"ضوابط اختبار للأمن السيبراني","document_type":"ضوابط","title":"بيانات اختبار غير رسمية",
       "article_number":"5","text":"تطبق متطلبات الأمن السيبراني على النطاق المحدد في الضوابط.",
       "decision_number":"TEST","effective_from":"2025-01-01","confidence":0.2},
    ]
    for d in docs: upsert_document(d)
if __name__=="__main__": seed()
