from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent_core import ask
from live_connectors import public_connectors

router = APIRouter(prefix="/api/v1", tags=["الرصد التشريعي"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="اسم النظام أو اللائحة، ويمكن إضافة رقم المادة")
    ncar_documents: list[dict] = Field(default_factory=list, description="نتائج بحث NCAR الرسمية التي جلبها متصفح المستخدم عند تعذر وصول الخادم للمصدر")


@router.post("/agent/ask")
def agent_ask(req: AskRequest):
    return ask(req.question, ncar_documents=req.ncar_documents)


@router.get("/agent/sources")
def agent_sources():
    return {"sources": public_connectors()}
