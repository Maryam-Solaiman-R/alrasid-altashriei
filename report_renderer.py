
from html import escape
from article_change_engine import build_change_report

COLORS={"green":"#07A869","blue":"#3D7EB9","teal":"#0DA9A6","navy":"#15445A","gold":"#C1B489","gray":"#C2C1C1"}

def _v(x,default="—"):
    return escape(str(x)) if x not in (None,"") else default

def render_change_report(data:dict)->str:
    before=data.get("before") or {}
    after=data.get("after") or {}
    app=data.get("applicability") or {}
    comp=data.get("comparison") or {}
    status=app.get("status","غير محدد")
    status_text={
      "applicable_candidate":"النسخة المرشحة للانطباق",
      "conditional":"انطباق مشروط بحكم انتقالي",
      "not_verified":"تعذر تحديد النص النافذ"
    }.get(status,status)
    return f"""<!doctype html>
<html dir="rtl" lang="ar">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>تقرير التغيير التشريعي</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:Tahoma,Arial,sans-serif;background:#f7faf9;color:#15445A}}
.page{{width:210mm;min-height:297mm;margin:auto;background:#fff;padding:18mm;position:relative;overflow:hidden}}
.wave{{position:absolute;top:-35mm;right:-25mm;width:120mm;height:70mm;border-radius:50%;background:linear-gradient(135deg,#0da9a61a,#3d7eb91f)}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:#55727f;margin-bottom:18px}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}} .card{{border:1px solid #e4ece9;border-radius:18px;padding:14px;background:#fff;box-shadow:0 6px 18px #15445a0b}}
.kpi{{border-right:5px solid #07A869}} .label{{font-size:12px;color:#6a7f87}} .value{{font-size:18px;font-weight:700;margin-top:4px}}
.section{{margin-top:18px}} .section h2{{font-size:18px;border-bottom:2px solid #0DA9A6;padding-bottom:7px}}
.compare{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .text{{line-height:1.9;color:#233f4a}}
.badge{{display:inline-block;padding:7px 12px;border-radius:999px;background:#07A86915;color:#067b4d;font-weight:700}}
.warn{{background:#c1b48926;color:#806f3d}}
.source{{font-size:12px;word-break:break-all;color:#3D7EB9}}
.footer{{position:absolute;bottom:10mm;right:18mm;left:18mm;font-size:10px;color:#7f9096;border-top:1px solid #edf2f0;padding-top:6px}}
@media print{{body{{background:white}} .page{{margin:0;box-shadow:none}}}}
</style></head>
<body><main class="page"><div class="wave"></div>
<h1>تقرير التغيير التشريعي</h1>
<div class="sub">{_v(data.get("instrument"))} — المادة ({_v(data.get("article_number"))})</div>
<div class="grid">
<div class="card kpi"><div class="label">قرار التعديل</div><div class="value">{_v(data.get("decision_number"))}</div></div>
<div class="card kpi"><div class="label">تاريخ القرار</div><div class="value">{_v(data.get("decision_date"))}</div></div>
<div class="card"><div class="label">تاريخ بدء النفاذ</div><div class="value">{_v(data.get("effective_from"))}</div></div>
<div class="card"><div class="label">حالة الانطباق</div><div class="value"><span class="badge {'warn' if status!='applicable_candidate' else ''}">{_v(status_text)}</span></div></div>
</div>
<section class="section"><h2>المقارنة قبل وبعد</h2><div class="compare">
<div class="card"><div class="label">قبل التعديل</div><div class="text">{_v(before.get("text"))}</div><div class="label">نهاية العمل: {_v(before.get("valid_to"))}</div></div>
<div class="card"><div class="label">بعد التعديل</div><div class="text">{_v(after.get("text"))}</div><div class="label">بداية العمل: {_v(after.get("valid_from"))}</div></div>
</div></section>
<section class="section"><h2>ملخص التغيير</h2>
<div class="grid"><div class="card"><div class="label">مستوى التغيير</div><div class="value">{_v(comp.get("change_level"))}</div></div>
<div class="card"><div class="label">نسبة التشابه</div><div class="value">{_v(comp.get("similarity"))}</div></div></div>
<div class="card" style="margin-top:12px"><div class="label">المحذوف</div><div class="text">{_v(comp.get("removed"))}</div><div class="label" style="margin-top:8px">المضاف</div><div class="text">{_v(comp.get("added"))}</div></div>
</section>
<section class="section"><h2>الحكم الانتقالي والمصدر</h2>
<div class="card"><div class="text">{_v(data.get("transitional_rule"),"لا يوجد حكم انتقالي مسجل.")}</div>
<div class="source" style="margin-top:8px">{_v(data.get("source_url"))}</div></div></section>
<div class="footer">الراصد التشريعي — مخرجات آلية مساندة للتحقق النظامي، ويجب الرجوع إلى المصدر الرسمي عند الاعتماد النهائي.</div>
</main></body></html>"""
