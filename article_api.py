
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from article_change_engine import extract_articles, build_change_report
from report_renderer import render_change_report

router=APIRouter(prefix="/api/v1",tags=["article-change"])

class ExtractRequest(BaseModel):
    text:str

class ReportRequest(BaseModel):
    instrument:str
    article_number:str
    previous:dict
    current:dict
    event_date:Optional[str]=None

@router.post("/extract-articles")
def extract(req:ExtractRequest):
    return {"articles":extract_articles(req.text)}

@router.post("/change-report")
def report(req:ReportRequest):
    return build_change_report(req.instrument,req.article_number,req.previous,req.current,req.event_date)

from fastapi.responses import HTMLResponse

@router.post("/change-report/html", response_class=HTMLResponse)
def report_html(req:ReportRequest):
    data=build_change_report(req.instrument,req.article_number,req.previous,req.current,req.event_date)
    return render_change_report(data)
