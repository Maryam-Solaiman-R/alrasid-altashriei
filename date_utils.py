
from datetime import date
import re

AR_TO_EN = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹","01234567890123456789")

def normalize_date_text(value:str|None):
    if not value: return None
    s=value.translate(AR_TO_EN).strip()
    s=re.sub(r"\s+","",s)
    s=s.replace("هـ","").replace("م","")
    return s

def parse_gregorian(value:str|None):
    s=normalize_date_text(value)
    if not s: return None
    for sep in ("-","/"):
        parts=s.split(sep)
        if len(parts)==3:
            nums=list(map(int,parts))
            if nums[0] > 1900:
                y,m,d=nums
            else:
                d,m,y=nums
            try: return date(y,m,d)
            except: return None
    return None

def sortable_gregorian(value:str|None):
    d=parse_gregorian(value)
    return d.isoformat() if d else None

def date_record(hijri:str|None=None, gregorian:str|None=None, source_text:str|None=None):
    return {
        "hijri": normalize_date_text(hijri),
        "gregorian": sortable_gregorian(gregorian),
        "source_text": source_text,
        "conversion_status": "source_provided" if hijri and gregorian else ("single_calendar_only" if (hijri or gregorian) else "missing")
    }
