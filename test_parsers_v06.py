
from backend_app import generic_parse, uqn_parse

def test_uqn_decision_1097():
    html="""<html><body>
    الموافقة على تعديل مواد من اللائحة التنفيذية لنظام المنافسات والمشتريات الحكومية
    قرار وزير المالية رقم (1097) بتاريخ 9/12/1447هـ
    تعديل المواد (88) و(111) و(114) و(132) من اللائحة التنفيذية لنظام المنافسات والمشتريات الحكومية.
    يعمل به ابتداء من تاريخه.
    </body></html>"""
    d=uqn_parse(html,"https://www.uqn.gov.sa/decisions-and-regulations/example")
    assert d["decision_number"]=="1097"
    assert d["article_numbers"]==["88","111","114","132"]

def test_generic_other_regulation():
    html="""<html><body>
    قرار رقم (77) بتاريخ 10/2/1448هـ بشأن تعديل المادة (25) من اللائحة التنفيذية لنظام افتراضي.
    يعمل به من اليوم التالي لتاريخ نشره.
    </body></html>"""
    d=generic_parse(html,"https://example.gov.sa/decision/77")
    assert d["decision_number"]=="77"
    assert "25" in d["article_numbers"]
    assert d["effective_rule"] is not None

if __name__=="__main__":
    test_uqn_decision_1097()
    test_generic_other_regulation()
    print("OK: v0.6 parser tests passed")
