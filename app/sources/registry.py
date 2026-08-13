from .base import SourceAdapter

class BOE(SourceAdapter):
    id="boe"; name="هيئة الخبراء بمجلس الوزراء"; domains=["laws.boe.gov.sa","boe.gov.sa"]
class NCAR(SourceAdapter):
    id="ncar"; name="المركز الوطني للوثائق والمحفوظات"; domains=["ncar.gov.sa"]
class UQN(SourceAdapter):
    id="uqn"; name="جريدة أم القرى"; domains=["uqn.gov.sa"]
class DGA(SourceAdapter):
    id="dga"; name="هيئة الحكومة الرقمية"; domains=["dga.gov.sa"]
class NCA(SourceAdapter):
    id="nca"; name="الهيئة الوطنية للأمن السيبراني"; domains=["nca.gov.sa"]
class SDAIA(SourceAdapter):
    id="sdaia"; name="الهيئة السعودية للبيانات والذكاء الاصطناعي (سدايا)"; domains=["sdaia.gov.sa"]
class MOF(SourceAdapter):
    id="mof"; name="وزارة المالية"; domains=["mof.gov.sa"]
class HRSD(SourceAdapter):
    id="hrsd"; name="وزارة الموارد البشرية والتنمية الاجتماعية"; domains=["hrsd.gov.sa"]
class LCGPA(SourceAdapter):
    id="lcgpa"; name="هيئة المحتوى المحلي والمشتريات الحكومية"; domains=["lcgpa.gov.sa"]
class EXPRO(SourceAdapter):
    id="expro"; name="هيئة كفاءة الإنفاق والمشروعات الحكومية"; domains=["expro.gov.sa"]
class GCA(SourceAdapter):
    id="gca"; name="الديوان العام للمحاسبة"; domains=["gca.gov.sa"]

ADAPTERS = [BOE(), NCAR(), UQN(), MOF(), HRSD(), LCGPA(), EXPRO(), DGA(), NCA(), SDAIA(), GCA()]
REGISTRY = {a.id:a for a in ADAPTERS}
