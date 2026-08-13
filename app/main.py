from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from app.models import SearchRequest, SearchResponse, Evidence
from app.sources.registry import ADAPTERS, REGISTRY
from app.search_engine import discover
import io, html
from urllib.parse import urlparse

app = FastAPI(title="الراصد التشريعي", description="وكيل بحث وتحليل تشريعي عند الطلب من المصادر الحكومية الرسمية", version="0.3.0")

INTRO = """دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية. اسأل عن نظام أو لائحة أو مادة تنظيمية، وسيبحث الراصد في المصادر الحكومية الرسمية التي تحددها، ويقرأ النتائج ذات الصلة ويعرض لك خلاصة بحث موثقة بروابط المصادر الأصلية. يمكنك استخدامه لمعرفة المواد التي جرى تعديلها، ومقارنة ما يظهر في المصادر قبل التحديث وبعده، ومعرفة قرارات وتواريخ التعديل، والتحقق من النص النظامي المنشور في تاريخ معين، أو البحث عن المادة المرتبطة بحالة محددة. اسأل، واستعرض ما تغيّر، وتحقّق من المصدر الرسمي."""

@app.get("/", response_class=HTMLResponse)
def home():
    options = "".join(
        f'<label class="source-option"><input type="checkbox" name="src" value="{a.id}"><span>{html.escape(a.name)}</span></label>'
        for a in ADAPTERS
    )
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>الراصد التشريعي</title>
<style>
:root{{--green:#07A869;--blue:#3D7EB9;--teal:#0DA9A6;--navy:#15445A;--gold:#C1B489;--gray:#C2C1C1;--line:#DCE8E5;--shadow:0 14px 38px rgba(21,68,90,.09)}}*{{box-sizing:border-box}}body{{margin:0;font-family:Tahoma,Arial,sans-serif;color:var(--navy);background:#fff;min-height:100vh}}.hero{{position:relative;overflow:hidden;padding:48px 20px 72px;background:linear-gradient(135deg,#fff 0%,#f6fbfa 62%,#eef8f6 100%);border-bottom:1px solid #edf3f1}}.hero:before{{content:"";position:absolute;width:520px;height:220px;border-radius:50%;background:linear-gradient(90deg,rgba(7,168,105,.13),rgba(61,126,185,.10));top:-145px;right:-80px;transform:rotate(-8deg)}}.hero:after{{content:"";position:absolute;width:650px;height:170px;border-radius:50%;border:28px solid rgba(13,169,166,.06);bottom:-135px;left:-100px;transform:rotate(5deg)}}.hero-inner{{max-width:1120px;margin:auto;position:relative;z-index:1}}.brand{{display:flex;align-items:center;gap:15px;margin-bottom:18px}}.logo{{width:58px;height:58px;border-radius:18px;background:linear-gradient(145deg,var(--green),var(--teal));display:grid;place-items:center;color:#fff;font-size:28px;font-weight:bold;box-shadow:0 10px 25px rgba(7,168,105,.22)}}h1{{margin:0;font-size:38px;color:var(--navy)}}.tagline{{font-size:18px;color:var(--green);font-weight:bold;margin:6px 0 0}}.lead{{max-width:960px;line-height:2.05;font-size:16px;color:#4d676f;margin:20px 0 0}}.shell{{max-width:1120px;margin:-38px auto 42px;padding:0 20px;position:relative;z-index:2}}.card{{background:#fff;border:1px solid var(--line);border-radius:22px;padding:25px;margin-bottom:18px;box-shadow:var(--shadow)}}.section-title{{font-size:17px;font-weight:bold;margin:0 0 10px}}textarea{{width:100%;min-height:120px;border:1px solid #cadbd6;border-radius:15px;padding:16px 18px;font:inherit;line-height:1.8;resize:vertical;outline:none;background:#fcfefd}}textarea:focus{{border-color:var(--green);box-shadow:0 0 0 4px rgba(7,168,105,.08)}}.search-grid{{display:grid;grid-template-columns:1fr 255px;gap:14px;align-items:end;margin-top:16px}}.source-wrap{{position:relative}}.source-button{{width:100%;height:48px;background:#fff;color:var(--navy);border:1px solid #cadbd6;border-radius:13px;padding:0 14px;display:flex;align-items:center;justify-content:space-between;font:inherit;cursor:pointer}}.source-button:hover{{border-color:var(--green)}}.chev{{color:var(--green);font-size:17px}}.source-menu{{display:none;position:absolute;top:55px;right:0;left:0;background:#fff;border:1px solid var(--line);border-radius:15px;box-shadow:0 16px 38px rgba(21,68,90,.16);z-index:20;max-height:330px;overflow:auto;padding:8px}}.source-menu.open{{display:block}}.source-option{{display:flex;gap:9px;align-items:flex-start;padding:10px;border-radius:9px;cursor:pointer;line-height:1.45;font-size:14px}}.source-option:hover{{background:#f1f8f6}}.source-option input{{accent-color:var(--green);margin-top:3px}}.all-option{{font-weight:bold;border-bottom:1px solid #edf2f1;margin-bottom:4px}}button{{border:0;border-radius:13px;padding:13px 23px;font:inherit;font-weight:bold;cursor:pointer}}.primary{{background:linear-gradient(135deg,var(--green),#079e75);color:#fff;box-shadow:0 8px 20px rgba(7,168,105,.20)}}.primary:disabled{{opacity:.55}}.secondary{{background:#eef5fa;color:var(--blue);border:1px solid #d6e5ef}}#status{{margin-top:13px;color:#637b80;font-size:14px}}.result-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}}.actions{{display:none;gap:8px;flex-wrap:wrap}}.empty{{padding:22px;background:#fffaf0;border:1px solid #efe4c9;border-radius:14px;color:#715f39;line-height:1.9}}table{{width:100%;border-collapse:separate;border-spacing:0;margin-top:17px;border:1px solid var(--line);border-radius:14px;overflow:hidden}}th,td{{padding:13px 11px;text-align:right;vertical-align:top;line-height:1.75;border-bottom:1px solid #e8efed}}th{{background:linear-gradient(90deg,#edf8f4,#f3f8fb);font-size:14px}}tr:last-child td{{border-bottom:0}}td{{font-size:14px;color:#405b63}}a{{color:var(--blue);font-weight:bold;text-decoration:none}}.badge{{display:inline-block;background:#eaf7f1;color:#087a51;border-radius:999px;padding:4px 9px;font-size:12px;font-weight:bold}}.note{{margin-top:15px;padding:13px 15px;background:#f5f8f9;border-right:4px solid var(--gold);border-radius:9px;color:#63747a;font-size:13px;line-height:1.8}}.footer-wave{{height:55px;background:linear-gradient(175deg,#fff 49%,rgba(7,168,105,.07) 50%,rgba(61,126,185,.08) 100%)}}@media(max-width:760px){{h1{{font-size:31px}}.search-grid{{grid-template-columns:1fr}}.shell{{padding:0 12px}}.card{{padding:18px}}table{{display:block;overflow-x:auto}}}}
</style></head><body>
<header class="hero"><div class="hero-inner"><div class="brand"><div class="logo">ر</div><div><h1>الراصد التشريعي</h1><div class="tagline">دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية</div></div></div><p class="lead">{html.escape(INTRO)}</p></div></header>
<main class="shell"><section class="card"><div class="section-title">ماذا تريد أن تعرف؟</div><textarea id="q" placeholder="مثال: ما المواد التي تم تعديلها في اللائحة التنفيذية لنظام المنافسات والمشتريات الحكومية؟"></textarea><div class="search-grid"><div class="source-wrap"><div class="section-title">مصادر البحث</div><button type="button" class="source-button" onclick="toggleMenu(event)"><span id="sourceLabel">جميع المصادر الرسمية</span><span class="chev">⌄</span></button><div id="sourceMenu" class="source-menu"><label class="source-option all-option"><input id="all" type="checkbox" checked onchange="toggleAll()"><span>جميع المصادر الرسمية</span></label>{options}</div></div><button id="go" class="primary" onclick="run()">بحث وتحليل</button></div><div id="status"></div></section>
<section class="card"><div class="result-head"><div class="section-title" style="margin:0">نتائج الراصد</div><div class="actions" id="actions"><button class="secondary" onclick="downloadFile('xlsx')">تصدير Excel</button><button class="secondary" onclick="downloadFile('docx')">تصدير Word</button></div></div><div id="out" style="margin-top:14px">اكتب سؤالك، وحدد المصادر التي تريد البحث فيها، ثم اضغط «بحث وتحليل».</div></section></main><div class="footer-wave"></div>
<script>
let lastPayload=null;const menu=document.getElementById('sourceMenu');
function toggleMenu(e){{e.stopPropagation();menu.classList.toggle('open')}}
document.addEventListener('click',e=>{{if(!e.target.closest('.source-wrap'))menu.classList.remove('open')}});
function updateSourceLabel(){{const all=document.getElementById('all'),selected=[...document.querySelectorAll('input[name=src]:checked')],label=document.getElementById('sourceLabel');if(all.checked||!selected.length)label.textContent='جميع المصادر الرسمية';else if(selected.length===1)label.textContent=selected[0].parentElement.innerText.trim();else label.textContent=`${{selected.length}} مصادر محددة`;}}
function toggleAll(){{if(document.getElementById('all').checked)document.querySelectorAll('input[name=src]').forEach(x=>x.checked=false);updateSourceLabel();}}
document.querySelectorAll('input[name=src]').forEach(x=>x.addEventListener('change',()=>{{if(x.checked)document.getElementById('all').checked=false;if(!document.querySelector('input[name=src]:checked'))document.getElementById('all').checked=true;updateSourceLabel();}}));
function esc(s){{return (s||'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}
function payload(){{let s=[...document.querySelectorAll('input[name=src]:checked')].map(x=>x.value);if(document.getElementById('all').checked||!s.length)s=['all'];return {{question:document.getElementById('q').value.trim(),sources:s,mode:'search',urls:[]}}}}
async function run(){{let p=payload();if(p.question.length<2){{document.getElementById('status').textContent='اكتب سؤالًا أولًا.';return}}lastPayload=p;let b=document.getElementById('go');b.disabled=true;document.getElementById('status').textContent='جارٍ البحث في المصادر الرسمية وقراءة النتائج…';document.getElementById('actions').style.display='none';try{{let r=await fetch('/analyze',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify(p)}});let d=await r.json();if(!r.ok)throw new Error(d.detail||'تعذر تنفيذ البحث');render(d)}}catch(e){{document.getElementById('out').innerHTML='<div class="empty">'+esc(e.message)+'</div>'}}finally{{b.disabled=false;document.getElementById('status').textContent=''}}}}
function render(d){{if(!d.results.length){{document.getElementById('out').innerHTML='<div class="empty"><b>لم أعثر على نتيجة رسمية كافية من المصادر المحددة.</b><br>جرّب صياغة السؤال باسم النظام أو اللائحة بصورة أدق، أو اختر مصادر إضافية.</div>';return}}let rows=d.results.map((x,i)=>`<tr><td>${{i+1}}</td><td>${{esc(x.source_name)}}</td><td><b>${{esc(x.title)}}</b><br>${{esc(x.excerpt)}}</td><td><span class="badge">${{Math.round(x.score)}}%</span></td><td><a href="${{esc(x.url)}}" target="_blank" rel="noopener">فتح المصدر الرسمي</a></td></tr>`).join('');document.getElementById('out').innerHTML=`<h2 style="margin:5px 0 8px">نتيجة البحث والتحليل</h2><p><b>السؤال:</b> ${{esc(d.question)}}</p><p><b>المصادر التي تم البحث فيها:</b> ${{d.searched_sources.map(esc).join('، ')}}</p><table><thead><tr><th>#</th><th>المصدر</th><th>ما وجدناه</th><th>الصلة</th><th>التحقق</th></tr></thead><tbody>${{rows}}</tbody></table><div class="note">${{esc(d.notice)}}</div>`;document.getElementById('actions').style.display='flex'}}
async function downloadFile(ext){{if(!lastPayload)return;let r=await fetch('/export/'+ext,{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify(lastPayload)}});if(!r.ok){{alert('تعذر إنشاء الملف');return}}let blob=await r.blob(),u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='نتائج_الراصد_التشريعي.'+ext;a.click();URL.revokeObjectURL(u)}}
</script></body></html>"""

@app.get("/sources")
def sources(): return [{"id":a.id,"name":a.name,"domains":a.domains} for a in ADAPTERS]

async def _run(req: SearchRequest):
    ids=list(REGISTRY) if "all" in req.sources else req.sources
    bad=[x for x in ids if x not in REGISTRY]
    if bad: raise HTTPException(400,f"مصادر غير معروفة: {bad}")
    results=[]; seen=set()
    # Optional direct official URLs remain supported.
    candidates=[{"url":u,"title":u,"snippet":""} for u in req.urls]
    if not candidates:
        domains=[]
        for i in ids: domains.extend(REGISTRY[i].domains)
        candidates=await discover(req.question,domains,limit=10)
    for item in candidates:
        url=item["url"]
        if url in seen: continue
        seen.add(url)
        adapter=next((REGISTRY[i] for i in ids if REGISTRY[i].accepts(url)),None)
        if not adapter: continue
        try:
            page=await adapter.fetch_page(url)
            data=adapter.analyze(page,req.question)
            if (not data.get("excerpt") or data.get("excerpt","").startswith("لم يظهر")) and item.get("snippet"):
                data["excerpt"]=item["snippet"]
            results.append(Evidence(**data))
        except Exception:
            if item.get("snippet"):
                results.append(Evidence(source_id=adapter.id,source_name=adapter.name,title=item.get("title") or "نتيجة رسمية",url=url,excerpt=item["snippet"],matched_terms=[],score=35))
    results.sort(key=lambda x:x.score,reverse=True)
    return SearchResponse(question=req.question,mode=req.mode,searched_sources=[REGISTRY[i].name for i in ids],results=results[:10])

@app.post("/analyze",response_model=SearchResponse)
async def analyze(req: SearchRequest): return await _run(req)

@app.post('/export/xlsx')
async def export_xlsx(req: SearchRequest):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    res=await _run(req); wb=Workbook(); ws=wb.active; ws.title='نتائج الراصد'; ws.sheet_view.rightToLeft=True
    ws.append(['المصدر','العنوان','الخلاصة/المقتطف','درجة الصلة','الرابط الرسمي'])
    for c in ws[1]: c.font=Font(bold=True); c.fill=PatternFill('solid',fgColor='DDEFE8'); c.alignment=Alignment(horizontal='right')
    for r in res.results: ws.append([r.source_name,r.title,r.excerpt,r.score,r.url])
    for col,w in {'A':30,'B':45,'C':90,'D':15,'E':55}.items(): ws.column_dimensions[col].width=w
    for row in ws.iter_rows():
        for c in row: c.alignment=Alignment(horizontal='right',vertical='top',wrap_text=True)
    bio=io.BytesIO(); wb.save(bio); bio.seek(0)
    return StreamingResponse(bio,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename=legislative_observer.xlsx'})

@app.post('/export/docx')
async def export_docx(req: SearchRequest):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    res=await _run(req); d=Document(); p=d.add_heading('الراصد التشريعي - نتائج البحث',0); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    p=d.add_paragraph('السؤال: '+res.question); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    for i,r in enumerate(res.results,1):
        p=d.add_heading(f'{i}. {r.title}',level=2); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        for txt in [f'المصدر: {r.source_name}',r.excerpt,f'الرابط الرسمي: {r.url}']:
            p=d.add_paragraph(txt); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    p=d.add_paragraph(res.notice); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    bio=io.BytesIO(); d.save(bio); bio.seek(0)
    return StreamingResponse(bio,media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',headers={'Content-Disposition':'attachment; filename=legislative_observer.docx'})
