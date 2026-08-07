
from pathlib import Path
from source_policy import source_scope, classify_discovered_source, PRIMARY_AUTHORITIES

def run():
    html=Path("index.html").read_text(encoding="utf-8")
    required=[
      "هيئة الخبراء بمجلس الوزراء","المركز الوطني للوثائق والمحفوظات",
      "الديوان العام للمحاسبة","وزارة المالية","وزارة الموارد البشرية والتنمية الاجتماعية",
      "هيئة المحتوى المحلي والمشتريات الحكومية","هيئة كفاءة الإنفاق والمشروعات الحكومية",
      "هيئة الحكومة الرقمية","الهيئة الوطنية للأمن السيبراني",
      "الهيئة السعودية للبيانات والذكاء الاصطناعي (سدايا)"
    ]
    for x in required: assert x in html
    assert len(PRIMARY_AUTHORITIES)==10
    scope=source_scope("جميع الجهات")
    assert scope["allow_dynamic_discovery"] is True
    assert scope["mode"]=="all_official_saudi_government"
    assert classify_discovered_source("https://example.gov.sa/regulations")["eligible_for_discovery"] is True
    assert classify_discovered_source("https://example.com/regulations")["eligible_for_discovery"] is False
    assert Path("backend_app.py").exists() and Path("config.js").exists()
    assert "دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية" in html
    print("OK: v1.6 deployment candidate, authority scope, dynamic gov.sa discovery and UI tests passed")
if __name__=="__main__": run()
