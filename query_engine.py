
import re
from source_registry import public_sources

TOPICS={
 "المحتوى المحلي":["المحتوى المحلي","تفضيل المحتوى","القائمة الإلزامية","المنشآت الصغيرة والمتوسطة"],
 "المنافسات والمشتريات":["منافسات","مشتريات","عقد","توريد","مقاول","ترسية","مستخلص"],
 "الأمن السيبراني":["الأمن السيبراني","ضوابط الأمن","سيبراني"],
 "البيانات والذكاء الاصطناعي":["سدايا","البيانات","الذكاء الاصطناعي","الخصوصية"],
 "الحكومة الرقمية":["الحكومة الرقمية","التحول الرقمي","منصة رقمية"],
 "الموارد البشرية والعمل":["نظام العمل","الموارد البشرية","موظف","إجازة","عامل"],
}
INTENTS=[
 ("changed_articles",("المواد المحدثة","المواد المعدلة","ما المواد","جرى تعديل","تغيرت")),
 ("applicability",("تنطبق","ينطبق","حالتي","معاملتي","عقد")),
 ("historical_text",("كان نافذا","كان نافذ","وقت المعاملة","تاريخ المعاملة","نص سابق")),
 ("latest_changes",("آخر التعديلات","احدث التعديلات","أحدث التعديلات","ما الذي تغير")),
]
def analyze_question(q:str):
    q=" ".join(q.split())
    topics=[name for name,words in TOPICS.items() if any(w in q for w in words)]
    intents=[name for name,words in INTENTS if any(w in q for w in words)]
    article=re.search(r"(?:المادة|مادة)\s*[\(（]?\s*(\d{1,4})",q)
    year=re.findall(r"\b(20\d{2}|14\d{2})\b",q)
    return {"question":q,"topics":topics,"intents":intents or ["semantic_search"],
            "article_number":article.group(1) if article else None,"years":year,
            "requires_article_number":False}

def build_search_plan(q:str):
    a=analyze_question(q)
    plan=[
      {"step":1,"action":"semantic_legislation_search","description":"تحديد الأنظمة واللوائح والمواد الأكثر صلة بموضوع السؤال."},
      {"step":2,"action":"official_source_verification","description":"التحقق من النصوص والقرارات في المصادر الرسمية."},
      {"step":3,"action":"version_history","description":"فحص تاريخ تعديل المواد المرشحة وقرارات التعديل والنفاذ."},
    ]
    if "applicability" in a["intents"] or "historical_text" in a["intents"]:
        plan.append({"step":4,"action":"temporal_applicability","description":"مقارنة تاريخ الواقعة بفترات النفاذ والأحكام الانتقالية."})
    return {"analysis":a,"plan":plan,"source_registry_size":len(public_sources())}
