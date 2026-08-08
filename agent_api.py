from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent_core import ask
from live_connectors import public_connectors

router = APIRouter(prefix="/api/v1", tags=["الرصد التشريعي"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="اسم النظام أو اللائحة، ويمكن إضافة رقم المادة")


@router.post("/agent/ask")
def agent_ask(req: AskRequest):
    return ask(req.question)


@router.get("/agent/sources")
def agent_sources():
    return {"sources": public_connectors()}
