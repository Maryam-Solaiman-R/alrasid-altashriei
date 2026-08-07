from __future__ import annotations
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup

CHANGE_TERMS = (
    "تعديل", "تعديلات", "يعدل", "تُعدّل", "المعدلة", "المعدّل", "إلغاء", "يلغى",
    "إضافة مادة", "حذف مادة", "استبدال", "قرار", "مرسوم"
)

@dataclass
class CandidateLink:
    url: str
    title: str
    source: str
    score: float
    reason: str


def _score(title: str, href: str) -> tuple[float,str]:
    txt = f"{title} {href}"
    hits = [x for x in CHANGE_TERMS if x in txt]
    score = min(0.95, 0.20 + 0.15 * len(hits)) if hits else 0.08
    return score, "، ".join(hits[:4]) if hits else "رابط تشريعي محتمل"

class BaseAdapter:
    name = "عام"
    domains: tuple[str,...] = ()
    def accepts(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return not self.domains or any(d in host for d in self.domains)
    def discover(self, html: str, base_url: str) -> list[CandidateLink]:
        soup = BeautifulSoup(html, "html.parser")
        out=[]; seen=set()
        for a in soup.find_all("a", href=True):
            title=" ".join(a.stripped_strings).strip()
            href=urljoin(base_url,a["href"])
            if href in seen or href.startswith("javascript:"): continue
            seen.add(href)
            score,reason=_score(title,href)
            if score >= .20:
                out.append(CandidateLink(href,title,self.name,score,reason))
        return sorted(out,key=lambda x:x.score,reverse=True)

class UQNAdapter(BaseAdapter):
    name="جريدة أم القرى"
    domains=("uqn.gov.sa",)
    def discover(self, html:str, base_url:str):
        rows=super().discover(html,base_url)
        for r in rows:
            if "/decisions-and-regulations/" in r.url:
                r.score=min(.99,r.score+.25); r.reason += "؛ صفحة قرار/تنظيم"
        return sorted(rows,key=lambda x:x.score,reverse=True)

class BOEAdapter(BaseAdapter):
    name="هيئة الخبراء بمجلس الوزراء"
    domains=("laws.boe.gov.sa",)
    def discover(self, html:str, base_url:str):
        rows=super().discover(html,base_url)
        for r in rows:
            if "BoeLaws/Laws" in r.url:
                r.score=min(.95,r.score+.18); r.reason += "؛ وثيقة نظامية"
        return sorted(rows,key=lambda x:x.score,reverse=True)

class HRSDAdapter(BaseAdapter):
    name="وزارة الموارد البشرية والتنمية الاجتماعية"
    domains=("hrsd.gov.sa",)
    def discover(self, html:str, base_url:str):
        rows=super().discover(html,base_url)
        for r in rows:
            if "decisions-and-regulations" in r.url:
                r.score=min(.98,r.score+.20); r.reason += "؛ قرار/لائحة"
        return sorted(rows,key=lambda x:x.score,reverse=True)

class MOFAdapter(BaseAdapter):
    name="وزارة المالية"; domains=("mof.gov.sa",)
class GCAAdapter(BaseAdapter):
    name="الديوان العام للمحاسبة"; domains=("gca.gov.sa",)
class NCARAdapter(BaseAdapter):
    name="المركز الوطني للتنافسية"; domains=("ncar.gov.sa",)

ADAPTERS=[UQNAdapter(),BOEAdapter(),HRSDAdapter(),MOFAdapter(),GCAAdapter(),NCARAdapter()]

def adapter_for(url:str)->BaseAdapter:
    for a in ADAPTERS:
        if a.accepts(url): return a
    return BaseAdapter()
