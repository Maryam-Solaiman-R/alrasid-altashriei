import os, html, io, re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

app=FastAPI(title="الراصد التشريعي")

SOURCES=[
("boe","هيئة الخبراء بمجلس الوزراء",["laws.boe.gov.sa","boe.gov.sa"]),
("ncar","المركز الوطني للوثائق والمحفوظات",["ncar.gov.sa"]),
("uqn","جريدة أم القرى",["uqn.gov.sa"]),
("mof","وزارة المالية",["mof.gov.sa"]),
("hrsd","وزارة الموارد البشرية والتنمية الاجتماعية",["hrsd.gov.sa"]),
("lcgpa","هيئة المحتوى المحلي والمشتريات الحكومية",["lcgpa.gov.sa"]),
("expro","هيئة كفاءة الإنفاق والمشروعات الحكومية",["expro.gov.sa"]),
("dga","هيئة الحكومة الرقمية",["dga.gov.sa"]),
("nca","الهيئة الوطنية للأمن السيبراني",["nca.gov.sa"]),
("sdaia","الهيئة السعودية للبيانات والذكاء الاصطناعي (سدايا)",["sdaia.gov.sa"]),
("gca","الديوان العام للمحاسبة",["gca.gov.sa"]),
]
class Ask(BaseModel):
    question:str
    sources:list[str]=["all"]

def selected(ids):
    if not ids or "all" in ids: return SOURCES
    wanted=set(ids); return [s for s in SOURCES if s[0] in wanted]

def citations(resp):
    out=[]
    try:
        d=resp.model_dump()
        for item in d.get("output",[]):
            if item.get("type")=="message":
                for c in item.get("content",[]):
                    for a in c.get("annotations",[]):
                        if a.get("type")=="url_citation":
                            u=a.get("url"); t=a.get("title") or "المصدر الرسمي"
                            if u and not any(x["url"]==u for x in out): out.append({"title":t,"url":u})
    except Exception: pass
    return out

def ask_ai(req):
    if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("يلزم إضافة OPENAI_API_KEY في Render.")
    ss=selected(req.sources)
    domains=[d for s in ss for d in s[2]]
    names="، ".join(s[1] for s in ss)
    prompt=f"""أنت الراصد التشريعي السعودي. أجب عن سؤال المستخدم بعد البحث الفعلي في الويب وقراءة المصادر الرسمية.
المصادر المختارة: {names}.
قواعد إلزامية:
- اعتمد على المصادر الحكومية الرسمية التي يسمح بها البحث فقط.
- لا تخمّن رقم مادة أو نصًا أو قرارًا أو تاريخًا.
- أجب مباشرة وبالعربية الفصحى.
- إذا كان السؤال عن تعديلات، استخرج المواد التي أمكن التحقق منها، وبيّن السابق والحالي والفرق وقرار/تاريخ التعديل متى توفر.
- إذا كان السؤال عن حالة عملية، رشّح المواد ذات الصلة واشرح سبب الصلة.
- استخدم جدولًا نصيًا واضحًا عندما تكون المقارنة أو تعدد المواد أفضل في جدول.
- إذا تعذر التحقق، قل تحديدًا ما الذي لم يمكن التحقق منه.
سؤال المستخدم: {req.question}"""
    tool={"type":"web_search","search_context_size":"high","filters":{"allowed_domains":domains}}
    client=OpenAI()
    resp=client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-5.6"),tools=[tool],input=prompt)
    return {"answer":resp.output_text,"citations":citations(resp),"sources":[s[1] for s in ss]}

@app.post("/analyze")
def analyze(req:Ask):
    try: return ask_ai(req)
    except Exception as e: raise HTTPException(500,str(e))

def _rtl_paragraph(p):
    p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    pPr=p._p.get_or_add_pPr(); bidi=OxmlElement('w:bidi'); bidi.set(qn('w:val'),'1'); pPr.append(bidi)
    for run in p.runs:
        run.font.name='Arial'; run.font.size=Pt(11)
        rPr=run._r.get_or_add_rPr(); rfonts=rPr.rFonts
        if rfonts is None:
            rfonts=OxmlElement('w:rFonts'); rPr.insert(0,rfonts)
        rfonts.set(qn('w:ascii'),'Arial'); rfonts.set(qn('w:hAnsi'),'Arial'); rfonts.set(qn('w:cs'),'Arial')

def _hyperlink(paragraph, text, url):
    part=paragraph.part; rid=part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    h=OxmlElement('w:hyperlink'); h.set(qn('r:id'),rid); r=OxmlElement('w:r'); rPr=OxmlElement('w:rPr')
    color=OxmlElement('w:color'); color.set(qn('w:val'),'3D7EB9'); rPr.append(color); u=OxmlElement('w:u'); u.set(qn('w:val'),'single'); rPr.append(u)
    r.append(rPr); t=OxmlElement('w:t'); t.text=text; r.append(t); h.append(r); paragraph._p.append(h)

def _clean_md(text):
    return re.sub(r'\*\*|__|^#{1,6}\s*','',text,flags=re.M).strip()

@app.post("/export/xlsx")
def export_xlsx(req:Ask):
    r=ask_ai(req); wb=Workbook(); ws=wb.active; ws.title="نتيجة الراصد"; ws.sheet_view.rightToLeft=True
    navy='15445A'; green='07A869'; blue='3D7EB9'; teal='0DA9A6'; gold='C1B489'; pale='F4FAF8'; white='FFFFFF'; line='DCE8E5'
    ws.merge_cells('A1:F1'); ws['A1']='الراصد التشريعي'; ws['A1'].font=Font(name='Arial',size=20,bold=True,color=navy); ws['A1'].alignment=Alignment(horizontal='right')
    ws.merge_cells('A2:F2'); ws['A2']='دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية'; ws['A2'].font=Font(name='Arial',size=11,bold=True,color=green); ws['A2'].alignment=Alignment(horizontal='right')
    row=4
    for label,value in [('السؤال',req.question),('المصادر المختارة','، '.join(r['sources']))]:
        ws.cell(row,1,label); ws.cell(row,1).font=Font(name='Arial',bold=True,color=white); ws.cell(row,1).fill=PatternFill('solid',fgColor=navy); ws.cell(row,1).alignment=Alignment(horizontal='right',vertical='top')
        ws.merge_cells(start_row=row,start_column=2,end_row=row,end_column=6); c=ws.cell(row,2,value); c.font=Font(name='Arial',color=navy); c.alignment=Alignment(horizontal='right',vertical='top',wrap_text=True); row+=1
    row+=1; ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=6); c=ws.cell(row,1,'نتيجة البحث والتحليل'); c.font=Font(name='Arial',size=13,bold=True,color=white); c.fill=PatternFill('solid',fgColor=green); c.alignment=Alignment(horizontal='right'); row+=1
    ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=6); c=ws.cell(row,1,_clean_md(r['answer'])); c.font=Font(name='Arial',size=11,color=navy); c.alignment=Alignment(horizontal='right',vertical='top',wrap_text=True); ws.row_dimensions[row].height=300; row+=2
    ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=6); c=ws.cell(row,1,'المصادر الرسمية المستخدمة'); c.font=Font(name='Arial',size=12,bold=True,color=white); c.fill=PatternFill('solid',fgColor=blue); c.alignment=Alignment(horizontal='right'); row+=1
    ws.append([])
    for i,cit in enumerate(r['citations'],1):
        ws.cell(row,1,i); ws.cell(row,2,cit['title']); ws.merge_cells(start_row=row,start_column=2,end_row=row,end_column=5); ws.cell(row,6,'فتح المصدر'); ws.cell(row,6).hyperlink=cit['url']; ws.cell(row,6).style='Hyperlink'
        for col in range(1,7): ws.cell(row,col).alignment=Alignment(horizontal='right',vertical='center',wrap_text=True); ws.cell(row,col).font=Font(name='Arial',color=navy); ws.cell(row,col).fill=PatternFill('solid',fgColor=pale)
        row+=1
    widths=[8,28,20,20,20,18]
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='A4'; ws.sheet_properties.pageSetUpPr.fitToPage=True; ws.page_setup.fitToWidth=1; ws.page_margins.right=.3; ws.page_margins.left=.3
    b=io.BytesIO(); wb.save(b); b.seek(0)
    return StreamingResponse(b,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=rasid.xlsx"})

@app.post("/export/docx")
def export_docx(req:Ask):
    r=ask_ai(req); d=Document(); sec=d.sections[0]; sec.right_margin=sec.left_margin
    styles=d.styles
    styles['Normal'].font.name='Arial'; styles['Normal'].font.size=Pt(11)
    p=d.add_paragraph(); run=p.add_run('الراصد التشريعي'); run.bold=True; run.font.size=Pt(22); run.font.color.rgb=RGBColor(21,68,90); _rtl_paragraph(p)
    p=d.add_paragraph(); run=p.add_run('دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية'); run.bold=True; run.font.color.rgb=RGBColor(7,168,105); _rtl_paragraph(p)
    for title,text in [('السؤال',req.question),('نتيجة البحث والتحليل',_clean_md(r['answer']))]:
        p=d.add_paragraph(); rr=p.add_run(title); rr.bold=True; rr.font.size=Pt(14); rr.font.color.rgb=RGBColor(21,68,90); _rtl_paragraph(p)
        p=d.add_paragraph(text); _rtl_paragraph(p)
    p=d.add_paragraph(); rr=p.add_run('المصادر الرسمية المستخدمة'); rr.bold=True; rr.font.size=Pt(14); rr.font.color.rgb=RGBColor(61,126,185); _rtl_paragraph(p)
    for i,cit in enumerate(r['citations'],1):
        p=d.add_paragraph(); p.add_run(f'{i}. {cit["title"]} — '); _hyperlink(p,'فتح المصدر الرسمي',cit['url']); _rtl_paragraph(p)
    b=io.BytesIO(); d.save(b); b.seek(0)
    return StreamingResponse(b,media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",headers={"Content-Disposition":"attachment; filename=rasid.docx"})

@app.get("/",response_class=HTMLResponse)
def home():
    opts="".join(f'<label><input type="checkbox" name="src" value="{i}"> {html.escape(n)}</label>' for i,n,_ in SOURCES)
    return """<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>الراصد التشريعي</title>
<style>:root{--g:#07A869;--b:#3D7EB9;--t:#0DA9A6;--n:#15445A;--gold:#C1B489;--line:#dce8e5}*{box-sizing:border-box}body{margin:0;font-family:Tahoma,Arial;color:var(--n);background:#fff}.hero{padding:42px 20px 70px;background:linear-gradient(135deg,#fff,#f3faf8);position:relative;overflow:hidden}.hero:before{content:"";position:absolute;width:520px;height:190px;border-radius:50%;background:linear-gradient(90deg,#07a86922,#3d7eb922);top:-130px;right:-70px}.inner,.shell{max-width:1100px;margin:auto}.brand{display:flex;gap:15px;align-items:center}.logo{width:58px;height:58px;border-radius:18px;background:linear-gradient(145deg,var(--g),var(--t));color:#fff;display:grid;place-items:center;font-size:28px;font-weight:bold}h1{margin:0;font-size:38px}.tag{color:var(--g);font-weight:bold;margin-top:6px;font-size:18px}.intro{margin-top:18px;color:#536c72;font-size:17px}.shell{margin-top:-35px;padding:0 18px 40px;position:relative}.card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:24px;box-shadow:0 14px 38px #15445a12;margin-bottom:18px}textarea{width:100%;min-height:115px;border:1px solid #cadbd6;border-radius:15px;padding:16px;font:inherit;line-height:1.8;outline:none}textarea:focus{border-color:var(--g);box-shadow:0 0 0 4px #07a86914}.grid{display:grid;grid-template-columns:1fr 240px;gap:14px;align-items:end;margin-top:15px}.drop{position:relative}.dropbtn{width:100%;background:#fff;border:1px solid #cadbd6;color:var(--n);border-radius:13px;padding:13px;font:inherit;text-align:right}.menu{display:none;position:absolute;right:0;left:0;top:52px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:8px;max-height:320px;overflow:auto;z-index:9;box-shadow:0 15px 35px #15445a25}.menu.open{display:block}.menu label{display:block;padding:9px;border-radius:8px;font-size:14px}.menu label:hover{background:#f0f8f5}.menu input{accent-color:var(--g)}button{cursor:pointer}.go{border:0;border-radius:13px;padding:14px;background:linear-gradient(135deg,var(--g),#079e75);color:#fff;font-weight:bold;font-size:16px}.go:disabled{opacity:.55}.result{line-height:2;white-space:pre-wrap}.citebox{margin-top:20px;padding:15px;background:#f5f8f9;border-right:4px solid var(--gold);border-radius:10px}.citebox a{color:var(--b);font-weight:bold;text-decoration:none;display:block;margin:5px 0}.actions{display:none;gap:8px;margin-top:16px}.actions button{border:1px solid #d6e5ef;background:#eef5fa;color:var(--b);border-radius:10px;padding:10px 14px;font-weight:bold}.status{margin-top:12px;color:#60777d}@media(max-width:700px){.grid{grid-template-columns:1fr}h1{font-size:30px}}</style></head>
<body><header class="hero"><div class="inner"><div class="brand"><div class="logo">ر</div><div><h1>الراصد التشريعي</h1><div class="tag">دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية</div></div></div><div class="intro">اسأل عن نظام أو لائحة أو مادة تنظيمية، واستعرض ما تغيّر، وتحقّق من المصدر الرسمي.</div></div></header>
<main class="shell"><section class="card"><b>ماذا تريد أن تعرف؟</b><textarea id="q" placeholder="مثال: ما المواد التي تم تعديلها في اللائحة التنفيذية لنظام المنافسات والمشتريات الحكومية؟"></textarea><div class="grid"><div class="drop"><b>مصادر البحث</b><button class="dropbtn" onclick="menu.classList.toggle('open')"><span id="lbl">جميع المصادر الرسمية</span> ▾</button><div id="menu" class="menu"><label><input id="all" type="checkbox" checked onchange="allchg()"> جميع المصادر الرسمية</label>"""+opts+"""</div></div><button id="go" class="go" onclick="run()">بحث وتحليل</button></div><div id="st" class="status"></div></section>
<section class="card"><b>نتائج الراصد</b><div id="out" class="result">اكتب سؤالك، وحدد المصادر التي تريد البحث فيها، ثم اضغط «بحث وتحليل».</div><div id="acts" class="actions"><button onclick="exp('xlsx')">تصدير Excel</button><button onclick="exp('docx')">تصدير Word</button></div></section></main>
<script>function renderMd(t){let e=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));let x=e(t);x=x.replace(/^### (.*)$/gm,'<h3>$1</h3>').replace(/^## (.*)$/gm,'<h2>$1</h2>').replace(/^# (.*)$/gm,'<h2>$1</h2>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>');let lines=x.split('\n'),o=[],tbl=[];function flush(){if(tbl.length){let rows=tbl.map(z=>z.split('|').filter(Boolean).map(v=>v.trim()));if(rows.length>1&&rows[1].every(v=>/^[-: ]+$/.test(v)))rows.splice(1,1);o.push('<div style=\"overflow:auto\"><table style=\"width:100%;border-collapse:collapse;margin:12px 0\">'+rows.map((r,i)=>'<tr>'+r.map(v=>'<'+(i?'td':'th')+' style=\"border:1px solid #dce8e5;padding:9px;text-align:right;vertical-align:top\">'+v+'</'+(i?'td':'th')+'>').join('')+'</tr>').join('')+'</table></div>');tbl=[]}}for(let l of lines){if(/^\s*\|.*\|\s*$/.test(l)){tbl.push(l);continue}flush();if(l.trim())o.push('<div>'+l+'</div>')}flush();return o.join('')}const menu=document.getElementById('menu');let last=null;document.addEventListener('click',e=>{if(!e.target.closest('.drop'))menu.classList.remove('open')});document.querySelectorAll('input[name=src]').forEach(x=>x.onchange=()=>{if(x.checked)all.checked=false;upd()});function allchg(){if(all.checked)document.querySelectorAll('input[name=src]').forEach(x=>x.checked=false);upd()}function upd(){let s=[...document.querySelectorAll('input[name=src]:checked')];if(!s.length){all.checked=true;lbl.textContent='جميع المصادر الرسمية'}else lbl.textContent=s.length==1?s[0].parentElement.innerText.trim():s.length+' مصادر محددة'}function payload(){let s=[...document.querySelectorAll('input[name=src]:checked')].map(x=>x.value);return {question:q.value.trim(),sources:all.checked||!s.length?['all']:s}}async function run(){let p=payload();if(!p.question)return;last=p;go.disabled=true;st.textContent='الذكاء الاصطناعي يبحث الآن في المصادر الرسمية ويحلل النتائج…';acts.style.display='none';try{let r=await fetch('/analyze',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(p)}),d=await r.json();if(!r.ok)throw Error(d.detail||'تعذر البحث');out.innerHTML=renderMd(d.answer);let box=document.createElement('div');box.className='citebox';box.innerHTML='<b>المصادر الرسمية المستخدمة:</b>';(d.citations||[]).forEach((c,i)=>{let a=document.createElement('a');a.href=c.url;a.target='_blank';a.rel='noopener';a.textContent=(i+1)+'. '+c.title;box.appendChild(a)});out.appendChild(box);acts.style.display='flex'}catch(e){out.textContent='تعذر تنفيذ البحث: '+e.message}finally{go.disabled=false;st.textContent=''}}async function exp(x){if(!last)return;let r=await fetch('/export/'+x,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(last)});if(!r.ok)return;let b=await r.blob(),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='نتائج_الراصد.'+x;a.click();URL.revokeObjectURL(u)}</script></body></html>"""
