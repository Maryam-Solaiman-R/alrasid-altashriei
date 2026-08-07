
from pathlib import Path
def run():
    html=Path("index.html").read_text(encoding="utf-8")
    assert "دليلك إلى تحديثات الأنظمة واللوائح الحكومية السعودية" in html
    assert "اسأل، واستعرض ما تغيّر، وتحقّق من النص النظامي الذي كان ساريًا وقت معاملتك." in html
    assert "وكيل ذكي" not in html
    assert Path("live_fetcher.py").exists()
    assert Path("source_monitor.py").exists()
    assert Path(".github/workflows/regulatory-monitor.yml").exists()
    print("OK: v1.5 approved wording, live fetcher and scheduled monitor scaffolding passed")
if __name__=="__main__": run()
