
from source_registry import source_for_url, classify_document, evidence_gate, public_sources

def run():
    assert len(public_sources()) >= 12
    assert source_for_url("https://nca.gov.sa/ar/example").key=="nca"
    assert source_for_url("https://dga.gov.sa/ar/regulations").key=="dga"
    assert source_for_url("https://someagency.gov.sa/laws").key=="gov_dynamic"
    assert source_for_url("https://example.com/x") is None

    draft=classify_document("مشروع لائحة تنظيمية مطروح عبر منصة استطلاع")
    assert draft["class"]=="draft" and draft["can_be_effective"] is False

    reg=classify_document("لائحة تنفيذية معدلة بقرار")
    assert reg["can_be_effective"] is True

    parsed={"decision_number":"100","decision_date_hijri":"1/1/1448",
            "effective_rule":"يعمل به من تاريخ نشره","article_numbers":["5"]}
    gate=evidence_gate(parsed,source_for_url("https://www.uqn.gov.sa/x"),reg)
    assert gate["may_determine_applicability"] is True

    gate2=evidence_gate(parsed,source_for_url("https://istitlaa.ncc.gov.sa/x"),draft)
    assert gate2["may_determine_applicability"] is False
    print("OK: v0.9 source registry and evidence gate tests passed")

if __name__=="__main__": run()
