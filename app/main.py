from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.sources.boe import BOEAdapter
from app.sources.ncar import NCARAdapter
import json
from pathlib import Path

app = FastAPI(
    title="الراصد التشريعي",
    description="MVP: هيئة الخبراء + المركز الوطني للوثائق والمحفوظات",
    version="0.1.0",
)

SEED = Path(__file__).resolve().parent.parent / "data" / "seed.json"

class FetchRequest(BaseModel):
    source: str
    url: str

@app.get("/")
def home():
    return {
        "name": "الراصد التشريعي",
        "sources": ["boe", "ncar"],
        "status": "MVP source adapters ready",
    }

@app.get("/seed")
def seed():
    return json.loads(SEED.read_text(encoding="utf-8"))

@app.post("/fetch")
async def fetch(req: FetchRequest):
    adapters = {"boe": BOEAdapter(), "ncar": NCARAdapter()}
    adapter = adapters.get(req.source.lower())
    if not adapter:
        raise HTTPException(400, "source must be boe or ncar")
    try:
        return await adapter.fetch_document(req.url)
    except Exception as e:
        raise HTTPException(502, f"تعذر الجلب من المصدر الرسمي: {e}")

@app.get("/search")
def search(q: str):
    rows = json.loads(SEED.read_text(encoding="utf-8"))
    qn = q.strip().lower()
    return [r for r in rows if qn in r["title"].lower()]
