from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import re

@dataclass(frozen=True)
class Connector:
    key:str
    authority:str
    roots:tuple[str,...]
    modes:tuple[str,...]
    priority:int=2
    notes:str=""

CONNECTORS=[
 Connector("uqn","جريدة أم القرى",("https://www.uqn.gov.sa/decisions-and-regulations/",),("listing","decision_page","html"),1),
 Connector("ncar","المركز الوطني للوثائق والمحفوظات",("https://ncar.gov.sa/",),("site_search","systems","regulations","documents","pdf"),1),   
 Connector("boe","هيئة الخبراء بمجلس الوزراء",("https://laws.boe.gov.sa/BoeLaws/Laws/Folders/1",),("catalog","consolidated_law"),1),
 Connector("ncar","المركز الوطني للوثائق والمحفوظات",("https://ncar.gov.sa/",),("catalog","archive"),1),
 Connector("mof","وزارة المالية",("https://www.mof.gov.sa/",),("site_search","decisions","pdf"),2),
 Connector("gca","الديوان العام للمحاسبة",("https://www.gca.gov.sa/",),("site_search","regulations","pdf"),2),
 Connector("hrsd","وزارة الموارد البشرية والتنمية الاجتماعية",("https://www.hrsd.gov.sa/",),("site_search","decisions","regulations","pdf"),2),
 Connector("lcgpa","هيئة المحتوى المحلي والمشتريات الحكومية",("https://lcgpa.gov.sa/",),("site_search","regulations","pdf"),2),
 Connector("expro","هيئة كفاءة الإنفاق والمشروعات الحكومية",("https://www.expro.gov.sa/",),("site_search","regulations","standards","pdf"),2),
 Connector("dga","هيئة الحكومة الرقمية",("https://dga.gov.sa/",),("site_search","regulations","policies","standards","pdf"),2),
 Connector("nca","الهيئة الوطنية للأمن السيبراني",("https://nca.gov.sa/ar/regulatory-documents/",),("catalog","controls","frameworks","pdf"),2),
 Connector("sdaia","الهيئة السعودية للبيانات والذكاء الاصطناعي (سدايا)",("https://sdaia.gov.sa/",),("site_search","regulations","policies","pdf"),2),
 Connector("istitlaa","منصة استطلاع",("https://istitlaa.ncc.gov.sa/",),("consultations","drafts"),3),
]

def connector_for_url(url):
    host=(urlparse(url).hostname or "").lower().removeprefix("www.")
    for c in CONNECTORS:
        for root in c.roots:
            rh=(urlparse(root).hostname or "").lower().removeprefix("www.")
            if host==rh or host.endswith("."+rh): return c
    return None

def discover_candidates(html, base_url):
    links=[]
    pattern=r'''href=["']([^"']+)["'][^>]*>(.*?)</a>'''
    for href,label in re.findall(pattern,html,re.I|re.S):
        text=re.sub(r"<[^>]+>"," ",label)
        text=re.sub(r"\s+"," ",text).strip()
        hay=(text+" "+href).lower()
        if any(k in hay for k in ("تعديل","قرار","لائحة","نظام","قواعد","ضوابط","regulation","decision","law","pdf")):
            links.append({"href":href,"label":text})
    return links[:500]

def public_connectors(): return [asdict(x) for x in CONNECTORS]
