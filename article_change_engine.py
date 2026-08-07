
import re, difflib
from dataclasses import dataclass, asdict
from typing import Optional

def norm(s:str)->str:
    return re.sub(r"\s+"," ",s or "").strip()

def extract_articles(text:str):
    """Extract Arabic article blocks when headings use المادة (N), المادة N, or مادة (N)."""
    t=norm(text)
    pat=re.compile(r"(?:المادة|مادة)\s*(?:رقم\s*)?[\(（]?\s*(\d{1,4})\s*[\)）]?\s*[:：\-–]?\s*")
    hits=list(pat.finditer(t)); out=[]
    for i,m in enumerate(hits):
        start=m.end(); end=hits[i+1].start() if i+1<len(hits) else len(t)
        body=t[start:end].strip(" .،؛:")
        if body:
            out.append({"article_number":m.group(1),"text":body})
    return out

def diff_summary(old:str,new:str):
    a=norm(old).split(); b=norm(new).split()
    sm=difflib.SequenceMatcher(a=a,b=b)
    added=[]; removed=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag in ("insert","replace"): added.extend(b[j1:j2])
        if tag in ("delete","replace"): removed.extend(a[i1:i2])
    ratio=sm.ratio()
    level="محدود" if ratio>=.85 else ("جزئي" if ratio>=.55 else "جوهري")
    return {"similarity":round(ratio,3),"change_level":level,
            "added":" ".join(added),"removed":" ".join(removed)}

def derive_validity(previous:Optional[dict], current:dict):
    """Close previous version at current valid_from; never invent an effective date."""
    if not current.get("valid_from"):
        return {"previous":previous,"current":current,"status":"needs_effective_date"}
    if previous:
        previous=dict(previous)
        previous["valid_to"]=current["valid_from"]
    return {"previous":previous,"current":current,"status":"linked"}

def applicability(versions:list[dict], event_date:str):
    candidates=[]
    for v in versions:
        vf=v.get("valid_from"); vt=v.get("valid_to")
        if (not vf or vf<=event_date) and (not vt or event_date<vt):
            candidates.append(v)
    if not candidates:
        return {"status":"not_verified","message":"لا توجد نسخة موثقة تغطي تاريخ الواقعة."}
    v=sorted(candidates,key=lambda x:(x.get("confidence",0),x.get("valid_from") or ""),reverse=True)[0]
    if v.get("transitional_rule"):
        return {"status":"conditional","version":v,
                "message":"عُثر على النسخة الزمنية، لكن يوجد حكم انتقالي يجب فحصه قبل اعتماد الانطباق."}
    return {"status":"applicable_candidate","version":v,
            "message":"هذه النسخة هي المرشح الزمني للانطباق وفق فترة النفاذ الموثقة."}

def build_change_report(instrument:str,article_number:str,previous:dict,current:dict,event_date:Optional[str]=None):
    linked=derive_validity(previous,current)
    report={
      "instrument":instrument,"article_number":article_number,
      "before":linked["previous"],"after":linked["current"],
      "validity_status":linked["status"],
      "decision_number":current.get("decision_number"),
      "decision_date":current.get("decision_date"),
      "publication_date":current.get("publication_date"),
      "effective_from":current.get("valid_from"),
      "source_url":current.get("source_url"),
      "transitional_rule":current.get("transitional_rule"),
      "comparison":diff_summary((previous or {}).get("text",""),current.get("text",""))
    }
    if event_date:
        versions=[x for x in (linked["previous"],linked["current"]) if x]
        report["applicability"]=applicability(versions,event_date)
    return report
