
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

@dataclass(frozen=True)
class Source:
    key: str
    name: str
    base_url: str
    tier: int
    roles: tuple[str, ...]
    notes: str = ""

SOURCES = [
    Source("uqn","جريدة أم القرى","https://www.uqn.gov.sa/",1,("official_gazette","publication","effective_date")),
    Source("boe","هيئة الخبراء بمجلس الوزراء","https://laws.boe.gov.sa/",1,("legislation_portal","consolidated_text","history")),
    Source("ncar_archive","المركز الوطني للوثائق والمحفوظات","https://ncar.gov.sa/",1,("archive","regulations","historical_reference")),
    Source("mof","وزارة المالية","https://www.mof.gov.sa/",2,("regulator","finance","procurement")),
    Source("gca","الديوان العام للمحاسبة","https://www.gca.gov.sa/",2,("regulator","audit","financial_control")),
    Source("hrsd","وزارة الموارد البشرية والتنمية الاجتماعية","https://www.hrsd.gov.sa/",2,("regulator","labor","civil_service")),
    Source("expro","هيئة كفاءة الإنفاق والمشروعات الحكومية","https://www.expro.gov.sa/",2,("regulator","spending_efficiency","government_projects")),
    Source("dga","هيئة الحكومة الرقمية","https://dga.gov.sa/",2,("regulator","digital_government","policies_standards")),
    Source("nca","الهيئة الوطنية للأمن السيبراني","https://nca.gov.sa/",2,("regulator","cybersecurity","controls")),
    Source("sdaia","الهيئة السعودية للبيانات والذكاء الاصطناعي (سدايا)","https://sdaia.gov.sa/",2,("regulator","data","ai")),
    Source("lcgpa","هيئة المحتوى المحلي والمشتريات الحكومية","https://lcgpa.gov.sa/",2,("regulator","local_content","procurement")),
    Source("istitlaa","منصة استطلاع - المركز الوطني للتنافسية","https://istitlaa.ncc.gov.sa/",3,("consultation","draft_legislation","early_warning")),
]

LEGISLATIVE_TYPES = (
    "نظام","لائحة","تنظيم","قواعد","ضوابط","سياسة","قرار تنظيمي",
    "تعميم","دليل","مشروع نظام","مشروع لائحة","مشروع قواعد","مشروع ضوابط"
)

def source_for_url(url:str):
    host=(urlparse(url).hostname or "").lower().removeprefix("www.")
    for s in SOURCES:
        shost=(urlparse(s.base_url).hostname or "").lower().removeprefix("www.")
        if host==shost or host.endswith("."+shost):
            return s
    if host.endswith(".gov.sa") or host=="gov.sa":
        return Source("gov_dynamic",f"جهة حكومية سعودية: {host}",f"https://{host}/",2,("government_dynamic","candidate_legislation"),
                      "مصدر حكومي مكتشف ديناميكيًا؛ يلزم التحقق من طبيعة الوثيقة وأداة إصدارها.")
    return None

def classify_document(text:str):
    t=" ".join(text.split())
    # drafts first so they are never confused with effective legislation
    if any(x in t for x in ("مشروع نظام","مشروع لائحة","مشروع قواعد","مشروع ضوابط","استطلاع")):
        return {"class":"draft","label":"مشروع تشريع/استطلاع","can_be_effective":False}
    for typ in ("نظام","لائحة","تنظيم","قواعد","ضوابط","سياسة","قرار تنظيمي","تعميم","دليل"):
        if typ in t:
            return {"class":"legislative" if typ not in ("تعميم","دليل") else "guidance",
                    "label":typ,"can_be_effective":typ not in ("تعميم","دليل")}
    return {"class":"unknown","label":"غير مصنف","can_be_effective":False}

def evidence_gate(parsed:dict, source:Source|None, classification:dict):
    reasons=[]
    score=0
    if source:
        score += {1:35,2:25,3:10}.get(source.tier,5)
    else: reasons.append("المصدر غير موجود في سجل المصادر الحكومية.")
    if parsed.get("decision_number"): score+=15
    else: reasons.append("لم يُستخرج رقم أداة الإصدار.")
    if parsed.get("decision_date_hijri"): score+=10
    else: reasons.append("لم يُستخرج تاريخ أداة الإصدار.")
    if parsed.get("effective_rule"): score+=20
    else: reasons.append("لم تُثبت قاعدة النفاذ.")
    if parsed.get("article_numbers"): score+=10
    if classification.get("class")=="draft":
        return {"status":"draft_only","score":min(score,60),"may_determine_applicability":False,
                "reasons":["الوثيقة مشروع/استطلاع وليست نصًا نافذًا."]+reasons}
    if not classification.get("can_be_effective"):
        return {"status":"needs_review","score":min(score,65),"may_determine_applicability":False,"reasons":reasons}
    ok=score>=70 and bool(parsed.get("effective_rule"))
    return {"status":"verified_candidate" if ok else "needs_review","score":min(score,100),
            "may_determine_applicability":ok,"reasons":reasons}

def public_sources():
    return [asdict(x) for x in SOURCES]
