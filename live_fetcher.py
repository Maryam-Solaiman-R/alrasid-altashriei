
import hashlib, time
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from live_connectors import connector_for_url, discover_candidates

UA="Saudi-Regulatory-Monitor/1.5 (+public regulatory research)"

def fetch(url, timeout=45):
    req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/pdf;q=0.9,*/*;q=0.8"})
    with urlopen(req,timeout=timeout) as r:
        body=r.read()
        return {"url":r.geturl(),"status":getattr(r,"status",200),
                "content_type":r.headers.get("Content-Type",""),
                "sha256":hashlib.sha256(body).hexdigest(),"body":body}

def scan_root(root):
    got=fetch(root)
    ct=got["content_type"].lower()
    if "html" not in ct:
        return {"root":root,"candidates":[],"sha256":got["sha256"]}
    html=got["body"].decode("utf-8","replace")
    candidates=discover_candidates(html,root)
    for c in candidates:
        c["url"]=urljoin(root,c["href"])
    return {"root":root,"candidates":candidates,"sha256":got["sha256"]}
