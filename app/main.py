from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from app.models import SearchRequest, SearchResponse
from app.sources.registry import ADAPTERS, REGISTRY
from urllib.parse import quote_plus
import io, csv, html

app = FastAPI(title="الراصد التشريعي", description="بحث وتحليل تشريعي عند الطلب من المصادر الرسمية", version="0.2.0")

@app.get("/", response_class=HTMLResponse)
def home():
    checks = "".join(f'<label><input type="checkbox" name="src" value="{a.id}"> {html.escape(a.name)}</label>' for a in ADAPTERS)
    return f'''<!doctype html><html dir="rtl" lang="ar"><meta charset="utf-8"><title>الراصد التشريعي</title>
<style>body{{font-family:Tahoma,Arial;background:#f7faf9;color:#15445A;margin:0}}main{{max-width:1050px;margin:35px auto;padding:25px}}h1{{color:#07A869}}.card{{background:white;border:1px solid #e4ece9;border-radius:18px;padding:22px;margin:16px 0;box-shadow:0 5px 18px #0000000d}}textarea{{width:100%;min-height:100px;border:1px solid #ccd8d4;border-radius:12px;padding:12px;box-sizing:border-box}}label{{display:inline-block;margin:8px 10px}}button{{background:#07A869;color:white;border:0;border-radius:10px;padding:12px 22px;cursor:pointer}}pre{{white-space:pre-wrap;direction:rtl}}</style>
<main><h1>الراصد التشريعي</h1><p>اسأل، اختر المصادر الرسمية، ثم تحقّق من الروابط الأصلية.</p><div class="card"><textarea id="q" placeholder="مثال: ما المواد المتعلقة بتأخر المقاول؟"></textarea><h3>مصادر البحث</h3><label><input id="all" type="checkbox" checked> جميع المصادر</label>{checks}<p><button onclick="run()">بحث وتحليل</button></p></div><div class="card"><pre id="out">النتيجة ستظهر هنا.</pre></div></main>
<script>async function run(){{let s=[...document.querySelectorAll('input[name=src]:checked')].map(x=>x.value);if(document.getElementById('all').checked||!s.length)s=['all'];let r=await fetch('/analyze',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify({{question:document.getElementById('q').value,sources:s,mode:'search',urls:[]}})}});document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2)}}</script></html>'''

@app.get("/sources")
def sources():
    return [{"id":a.id,"name":a.name,"domains":a.domains} for a in ADAPTERS]

@app.get("/search-links")
def search_links(q: str, sources: str = "all"):
    ids = list(REGISTRY) if sources == "all" else [x.strip() for x in sources.split(",") if x.strip() in REGISTRY]
    return [{"source_id":i,"source_name":REGISTRY[i].name,"search_url":f"https://www.google.com/search?q={quote_plus('site:'+REGISTRY[i].domains[0]+' '+q)}"} for i in ids]

@app.post("/analyze", response_model=SearchResponse)
async def analyze(req: SearchRequest):
    ids = list(REGISTRY) if "all" in req.sources else req.sources
    bad = [x for x in ids if x not in REGISTRY]
    if bad: raise HTTPException(400, f"مصادر غير معروفة: {bad}")
    results=[]
    # النسخة الحالية تحلل الروابط الرسمية التي يحددها المستخدم/واجهة البحث.
    # اكتشاف الروابط آليًا سيضاف في مرحلة موصل البحث لكل جهة.
    for url in req.urls:
        adapter = next((REGISTRY[i] for i in ids if REGISTRY[i].accepts(url)), None)
        if not adapter: continue
        try:
            page = await adapter.fetch_page(url)
            results.append(adapter.analyze(page, req.question))
        except Exception as e:
            results.append({"source_id":adapter.id,"source_name":adapter.name,"title":"تعذر قراءة المصدر","url":url,"excerpt":str(e),"matched_terms":[],"score":0})
    return SearchResponse(question=req.question, mode=req.mode, searched_sources=[REGISTRY[i].name for i in ids], results=results)

@app.post("/export/csv")
async def export_csv(req: SearchRequest):
    res = await analyze(req)
    out=io.StringIO(); w=csv.writer(out); w.writerow(["المصدر","العنوان","الرابط","درجة المطابقة","المقتطف"])
    for r in res.results: w.writerow([r.source_name,r.title,r.url,r.score,r.excerpt])
    data='\ufeff'+out.getvalue()
    return StreamingResponse(io.BytesIO(data.encode('utf-8')), media_type='text/csv; charset=utf-8', headers={'Content-Disposition':'attachment; filename=legislative_observer_results.csv'})
