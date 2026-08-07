
from datetime import datetime, timezone
from live_connectors import CONNECTORS
from live_fetcher import scan_root

def scan_all():
    report={"checked_at":datetime.now(timezone.utc).isoformat(),"sources":[]}
    for c in CONNECTORS:
        item={"key":c.key,"authority":c.authority,"roots":[]}
        for root in c.roots:
            try:
                r=scan_root(root)
                item["roots"].append({"url":root,"status":"ok","candidate_count":len(r["candidates"]),
                                      "candidates":r["candidates"][:30],"sha256":r["sha256"]})
            except Exception as e:
                item["roots"].append({"url":root,"status":"error","error":str(e)[:300]})
        report["sources"].append(item)
    return report
