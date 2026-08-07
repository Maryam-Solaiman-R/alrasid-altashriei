
from article_change_engine import extract_articles, build_change_report, applicability

def run():
    doc="المادة (10): المدة ثلاثون يوماً. المادة (11): يقدم الطلب إلى الجهة المختصة."
    a=extract_articles(doc)
    assert [x["article_number"] for x in a]==["10","11"]

    old={"text":"يجب تقديم الطلب خلال ثلاثين يوماً.","valid_from":"2024-01-01","valid_to":None,
         "decision_number":"1","confidence":0.95}
    new={"text":"يجب تقديم الطلب خلال ستين يوماً.","valid_from":"2026-06-01","valid_to":None,
         "decision_number":"99","decision_date":"1447-12-09","publication_date":"2026-06-05",
         "source_url":"https://www.uqn.gov.sa/example","confidence":0.98}
    r=build_change_report("لائحة اختبار","10",old,new,"2026-05-20")
    assert r["before"]["valid_to"]=="2026-06-01"
    assert r["applicability"]["version"]["decision_number"]=="1"
    r2=build_change_report("لائحة اختبار","10",old,new,"2026-06-20")
    assert r2["applicability"]["version"]["decision_number"]=="99"
    assert "ثلاثين" in r2["comparison"]["removed"]
    assert "ستين" in r2["comparison"]["added"]

    trans=dict(new); trans["transitional_rule"]="يستمر العمل بالحكم السابق على الحالات القائمة."
    r3=build_change_report("لائحة اختبار","10",old,trans,"2026-06-20")
    assert r3["applicability"]["status"]=="conditional"
    print("OK: v1.0 article extraction, version linking, diff, and applicability tests passed")
if __name__=="__main__": run()
