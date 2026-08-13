import re
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

AR_STOP = {"في","من","على","إلى","عن","ما","هل","او","أو","التي","الذي","هذه","هذا","مع","بعد","قبل","بين","لدى","عند","تم","ثم"}

def terms(text: str):
    xs = re.findall(r"[\u0600-\u06FFA-Za-z0-9]+", text.lower())
    return [x for x in xs if len(x) > 2 and x not in AR_STOP]

class SourceAdapter:
    id = "generic"
    name = "مصدر رسمي"
    domains = []

    def accepts(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return any(d in host for d in self.domains)

    async def fetch_page(self, url: str) -> dict:
        if not self.accepts(url):
            raise ValueError(f"الرابط لا يتبع المصدر المحدد: {self.name}")
        headers = {"User-Agent":"Mozilla/5.0 LegislativeObserver/0.2","Accept-Language":"ar,en;q=0.8"}
        async with httpx.AsyncClient(timeout=35, follow_redirects=True, headers=headers) as client:
            r = await client.get(url)
            r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "pdf" in ctype.lower() or str(r.url).lower().endswith(".pdf"):
            return {"title": str(r.url).split("/")[-1], "url": str(r.url), "text": "", "content_type": "pdf", "note":"PDF detected; use official URL as evidence. PDF text extraction is a next adapter enhancement."}
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript","svg"]): tag.decompose()
        text = "\n".join(s.strip() for s in soup.stripped_strings if s.strip())
        title = soup.title.get_text(" ", strip=True) if soup.title else str(r.url)
        return {"title": title, "url": str(r.url), "text": text, "content_type": ctype}

    def analyze(self, page: dict, question: str) -> dict:
        qterms = terms(question)
        text = page.get("text", "")
        low = text.lower()
        matched = [t for t in qterms if t in low]
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        hits = [ln for ln in lines if any(t in ln.lower() for t in matched)]
        excerpt = " | ".join(hits[:8])[:3500]
        score = round((len(matched) / max(len(set(qterms)), 1)) * 100, 1)
        return {"source_id":self.id,"source_name":self.name,"title":page.get("title","وثيقة"),"url":page.get("url",""),"excerpt":excerpt or page.get("note", "لم يظهر نص مطابق كافٍ في الصفحة."),"matched_terms":matched,"score":score}
