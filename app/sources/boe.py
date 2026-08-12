import re
import httpx
from bs4 import BeautifulSoup
from .base import SourceAdapter

class BOEAdapter(SourceAdapter):
    """
    محول هيئة الخبراء.
    الهدف: استخراج بيانات الوثيقة والمواد من الصفحة الرسمية.
    """
    async def fetch_document(self, url: str) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0 LegislativeObserver/0.1",
            "Accept-Language": "ar,en;q=0.8",
        }
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client:
            r = await client.get(url)
            r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        text = "\n".join(x.strip() for x in soup.stripped_strings)

        title = self._first(text, [
            r"(نظام المنافسات\s*و?\s*المشتريات الحكومية)",
            r"الاسم\s+(.+)"
        ])

        return {
            "title": title or (soup.title.get_text(strip=True) if soup.title else "وثيقة"),
            "source": "هيئة الخبراء بمجلس الوزراء",
            "source_url": str(r.url),
            "status": self._first(text, [r"الحالة\s+([^\n]+)"]),
            "issue_hijri": self._first(text, [r"تاريخ الإصدار\s+([0-9/٠-٩]+)\s*هـ"]),
            "issue_gregorian": self._first(text, [r"الموافق\s*:\s*([0-9/٠-٩]+)\s*م"]),
            "publication_hijri": self._first(text, [r"تاريخ النشر\s+([0-9/٠-٩]+)\s*هـ"]),
            "issuing_tools": self._issuing_tools(text),
            "articles": self._articles(text),
        }

    def _first(self, text, patterns):
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return None

    def _issuing_tools(self, text):
        out = []
        for m in re.finditer(r"(مرسوم ملكي|قرار مجلس الوزراء)\s+رقم\s*\(([^)]+)\)\s+وتاريخ\s+([0-9/٠-٩]+)", text):
            out.append(f"{m.group(1)} رقم ({m.group(2)}) بتاريخ {m.group(3)}")
        return out

    def _articles(self, text):
        # استخراج مبدئي؛ يُحسّن بعد اختبار HTML الحي على Render.
        pat = re.compile(r"(المادة\s+[^\n]+)\n(.*?)(?=\nالمادة\s+|\Z)", re.S)
        return [{"heading": m.group(1).strip(), "text": m.group(2).strip()} for m in pat.finditer(text)]
