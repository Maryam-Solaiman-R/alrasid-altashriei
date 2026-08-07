
import json, time, argparse
from datetime import datetime, timezone
from urllib.request import Request, urlopen

def call(url, method="GET", body=None):
    data=None if body is None else json.dumps(body,ensure_ascii=False).encode("utf-8")
    req=Request(url,data=data,method=method,headers={"Content-Type":"application/json","User-Agent":"Saudi-Regulatory-Monitor/1.1"})
    with urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def run_once(api_base):
    sources=call(api_base.rstrip("/")+"/api/source-registry")
    summary={"checked_at":datetime.now(timezone.utc).isoformat(),"sources":len(sources),"status":"registry_ready"}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--api",default="http://127.0.0.1:8000")
    ap.add_argument("--interval-minutes",type=int,default=0)
    args=ap.parse_args()
    if args.interval_minutes<=0:
        run_once(args.api)
    else:
        while True:
            try: run_once(args.api)
            except Exception as e: print("monitor error:",e)
            time.sleep(args.interval_minutes*60)
