from __future__ import annotations
from io import BytesIO
from pypdf import PdfReader

def extract_pdf_text(raw:bytes)->str:
    reader=PdfReader(BytesIO(raw))
    parts=[]
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()
