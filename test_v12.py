
from query_engine import analyze_question, build_search_plan
from pathlib import Path
def run():
    a=analyze_question("لدي عقد توريد وفيه اشتراطات المحتوى المحلي، ما المواد التي تنطبق على حالتي وهل تغيرت؟")
    assert "المحتوى المحلي" in a["topics"]
    assert a["requires_article_number"] is False
    assert "applicability" in a["intents"]
    b=analyze_question("ما المواد المحدثة من لائحة تفضيل المحتوى المحلي؟")
    assert "changed_articles" in b["intents"]
    html=Path("index.html").read_text(encoding="utf-8")
    assert 'dir="rtl"' in html and "اسأل الراصد" in html and "ما الذي تغير؟" in html
    assert "#07a869" in html.lower() and "@media(max-width:760px)" in html
    print("OK: v1.2 natural-language entry and self-contained responsive UI tests passed")
if __name__=="__main__":run()
