from __future__ import annotations
from difflib import SequenceMatcher
import re

def normalize_arabic(text:str)->str:
    text=re.sub(r"[\u064B-\u065F\u0670]","",text or "")
    text=text.replace("ـ","")
    return re.sub(r"\s+"," ",text).strip()

def word_diff(before:str, after:str):
    a=normalize_arabic(before).split(); b=normalize_arabic(after).split()
    sm=SequenceMatcher(a=a,b=b)
    changes=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=="equal": continue
        changes.append({"type":tag,"before":" ".join(a[i1:i2]),"after":" ".join(b[j1:j2])})
    ratio=sm.ratio()
    if not before: kind="إضافة نص جديد"
    elif not after: kind="إلغاء النص"
    elif ratio > .92: kind="تعديل محدود"
    elif ratio > .65: kind="تعديل جزئي"
    else: kind="إعادة صياغة جوهرية"
    return {"similarity":round(ratio,4),"change_kind":kind,"changes":changes}
