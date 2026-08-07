
import re, math
from collections import Counter

AR_STOP={"في","من","على","إلى","الى","عن","ما","هل","التي","الذي","هذه","هذا","مع","أو","او","ثم","تم","لدي","لها","له","كان","كانت"}

def tokens(text):
    text=re.sub(r"[^\w\u0600-\u06FF]+"," ",(text or "").lower())
    return [x for x in text.split() if len(x)>1 and x not in AR_STOP]

def score(query, document):
    q=Counter(tokens(query)); d=Counter(tokens(document))
    if not q or not d: return 0.0
    overlap=sum(min(q[k],d[k]) for k in q)
    coverage=overlap/max(1,sum(q.values()))
    phrase_bonus=0.0
    nq=" ".join(tokens(query)); nd=" ".join(tokens(document))
    for phrase in ("المحتوى المحلي","الأمن السيبراني","الحكومة الرقمية","نظام العمل","المنافسات والمشتريات"):
        if phrase in query and phrase in document: phrase_bonus+=0.18
    return round(min(1.0,coverage+phrase_bonus),3)

def rank_documents(query, docs, limit=8):
    ranked=[]
    for d in docs:
        body=" ".join(str(d.get(k,"")) for k in ("instrument","title","article_number","text","authority","document_type"))
        s=score(query,body)
        if s>0:
            x=dict(d); x["relevance"]=s; ranked.append(x)
    return sorted(ranked,key=lambda x:(x["relevance"],x.get("confidence",0)),reverse=True)[:limit]

def answer_shape(question, candidates):
    if not candidates:
        return {"status":"needs_live_search","summary":"لم يعثر الفهرس المحلي على نصوص كافية. يلزم البحث الحي في المصادر الرسمية.",
                "candidates":[]}
    return {"status":"candidates_found",
            "summary":f"عُثر على {len(candidates)} نتيجة محتملة الصلة. يجب التحقق من النسخة والنفاذ قبل الحكم النهائي.",
            "candidates":candidates}
