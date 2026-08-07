from live_connectors import connector_for_url, discover_candidates, public_connectors
from provenance import provenance_record, verification_state
def run():
    assert connector_for_url("https://www.uqn.gov.sa/decisions-and-regulations/4001123").key=="uqn"
    assert connector_for_url("https://nca.gov.sa/ar/regulatory-documents/controls-list/ecc/").key=="nca"
    html='<a href="/x">تعديل اللائحة التنفيذية</a><a href="/about">من نحن</a><a href="/a.pdf">ضوابط جديدة</a>'
    assert len(discover_candidates(html,"https://example.gov.sa"))==2
    r=provenance_record("https://www.uqn.gov.sa/x","جريدة أم القرى",decision_number="1097",decision_date="9/12/1447هـ",effective_rule="يعمل به من تاريخه")
    assert verification_state(r)["usable_for_applicability"] is True
    d=provenance_record("https://istitlaa.ncc.gov.sa/x","منصة استطلاع",document_status="draft")
    assert verification_state(d)["usable_for_applicability"] is False
    assert len(public_connectors())>=12
    print("OK: v1.4 connector registry, discovery, provenance and verification tests passed")
if __name__=="__main__": run()
