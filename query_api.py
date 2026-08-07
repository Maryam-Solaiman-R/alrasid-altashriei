
from fastapi import APIRouter
from pydantic import BaseModel
from query_engine import build_search_plan
router=APIRouter(prefix="/api/v1",tags=["natural-language"])
class QueryRequest(BaseModel): question:str
@router.post("/query")
def query(req:QueryRequest):
    return {"status":"search_plan_ready",**build_search_plan(req.question),
            "note":"يُستكمل التنفيذ الحي عبر موصلات المصادر بعد النشر على خادم يسمح بالإنترنت."}
