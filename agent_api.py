
from fastapi import APIRouter
from pydantic import BaseModel
from agent_core import ask, changed
router=APIRouter(prefix="/api/v1",tags=["agent"])
class AskRequest(BaseModel): question:str
@router.post("/agent/ask")
def agent_ask(req:AskRequest): return ask(req.question)
@router.get("/agent/changes")
def agent_changes(q:str="",limit:int=50): return changed(q,limit)
