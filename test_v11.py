
from date_utils import parse_gregorian, sortable_gregorian
from report_renderer import render_change_report
from article_change_engine import build_change_report

def run():
    assert sortable_gregorian("5/6/2026")=="2026-06-05"
    assert sortable_gregorian("2026-06-05")=="2026-06-05"
    old={"text":"النص السابق","valid_from":"2025-01-01","confidence":.9}
    new={"text":"النص الجديد","valid_from":"2026-06-01","decision_number":"1097","decision_date":"9/12/1447هـ",
         "source_url":"https://www.uqn.gov.sa/example","confidence":.95}
    r=build_change_report("لائحة اختبار","88",old,new,"2026-06-20")
    html=render_change_report(r)
    assert 'dir="rtl"' in html
    assert "قبل التعديل" in html and "بعد التعديل" in html and "#07A869" in html
    print("OK: v1.1 date normalization and printable RTL report tests passed")

if __name__=="__main__": run()
