from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class LegalInstrument(BaseModel):
    id: str
    title: str
    source: str
    source_url: str
    status: Optional[str] = None
    issue_hijri: Optional[str] = None
    issue_gregorian: Optional[str] = None
    publication_hijri: Optional[str] = None
    publication_gregorian: Optional[str] = None
    issuing_tools: List[str] = []
    amendments: List[dict] = []
    articles: List[dict] = []
