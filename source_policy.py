
from urllib.parse import urlparse
import re

PRIMARY_AUTHORITIES=[
 "هيئة الخبراء بمجلس الوزراء",
 "المركز الوطني للوثائق والمحفوظات",
 "الديوان العام للمحاسبة",
 "وزارة المالية",
 "وزارة الموارد البشرية والتنمية الاجتماعية",
 "هيئة المحتوى المحلي والمشتريات الحكومية",
 "هيئة كفاءة الإنفاق والمشروعات الحكومية",
 "هيئة الحكومة الرقمية",
 "الهيئة الوطنية للأمن السيبراني",
 "الهيئة السعودية للبيانات والذكاء الاصطناعي (سدايا)",
]
PRIMARY_PUBLICATION_SOURCES=["جريدة أم القرى"]

OFFICIAL_HINTS=(".gov.sa",".sa")

def is_probable_saudi_official(url:str)->bool:
    host=(urlparse(url).hostname or "").lower()
    # gov.sa is automatically a strong official-domain signal.
    if host=="gov.sa" or host.endswith(".gov.sa"): return True
    # Other .sa domains are not auto-trusted; they remain candidates pending verification.
    return False

def source_scope(authority_filter:str|None):
    if not authority_filter or authority_filter=="جميع الجهات":
        return {"mode":"all_official_saudi_government",
                "primary_authorities":PRIMARY_AUTHORITIES,
                "primary_publication_sources":PRIMARY_PUBLICATION_SOURCES,
                "allow_dynamic_discovery":True}
    return {"mode":"authority_filter","authority":authority_filter,
            "allow_dynamic_discovery":False}

def classify_discovered_source(url:str, declared_authority:str|None=None):
    if is_probable_saudi_official(url):
        return {"status":"official_domain_candidate","url":url,
                "authority":declared_authority,"eligible_for_discovery":True,
                "requires_content_verification":True}
    return {"status":"unverified_external","url":url,
            "authority":declared_authority,"eligible_for_discovery":False,
            "requires_content_verification":True}
