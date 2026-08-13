from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SourceInfo(BaseModel):
    id: str
    name: str
    domain: str
    enabled: bool = True

class SearchRequest(BaseModel):
    question: str = Field(min_length=2)
    sources: List[str] = Field(default_factory=lambda: ["all"])
    mode: Literal["search", "compare", "applicable", "effective_date", "updates"] = "search"
    urls: List[str] = Field(default_factory=list, description="روابط رسمية اختيارية يحددها المستخدم لتحليلها مباشرة")
    effective_date: Optional[str] = None

class Evidence(BaseModel):
    source_id: str
    source_name: str
    title: str
    url: str
    excerpt: str
    matched_terms: List[str] = []
    score: float = 0

class SearchResponse(BaseModel):
    question: str
    mode: str
    searched_sources: List[str]
    results: List[Evidence]
    notice: str = "النتائج مساعدة للبحث، ويظل النص المنشور في المصدر الرسمي هو المرجع للتحقق."
