import re
import httpx
from bs4 import BeautifulSoup
from .base import SourceAdapter

class NCARAdapter(SourceAdapter):
    """
    محول المركز الوطني للوثائق والمحفوظات.
    مهمته الأساسية: بيانات الوثيقة + وثائق التعديل + المرفقات/المصادر الرسمية.
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

        amendments = []
        # نمط أولي لكتل "وثائق التعديل"
        if "وثائق التعديل" in text:
            tail = text.split("وثائق التعديل", 1)[1]
            tail = tail.split("الوثائق ذات صلة", 1)[0]
            chunks = [x.strip() for x in tail.split("\n") if x.strip()]
            for i, line in enumerate(chunks):
                if "قرار" in line or "مرسوم" in line or "المعدلة" in line:
                    amendments.append({"text": line})

        return {
            "title": soup.title.get_text(strip=True) if soup.title else "وثيقة",
            "source": "المركز الوطني للوثائق والمحفوظات",
            "source_url": str(r.url),
            "amendments": amendments,
            "raw_has_amendments_section": "وثائق التعديل" in text,
        }
