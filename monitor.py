from __future__ import annotations
import json, sqlite3, time
from datetime import datetime, timezone
from backend_app import DB, fetch_resource, save_snapshot, parser_for, persist_discovery
from source_adapters import adapter_for

SEED_URLS = [
    'https://www.uqn.gov.sa/decisions-and-regulations',
    'https://laws.boe.gov.sa/BoeLaws/Laws/Folders/1',
    'https://www.hrsd.gov.sa/knowledge-centre/decisions-and-regulations',
    'https://www.mof.gov.sa/Pages/default.aspx',
    'https://www.gca.gov.sa/Pages/homePage.aspx',
    'https://ncar.gov.sa/',
]

def con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def store_candidates(source_url, rows):
    c=con(); now=datetime.now(timezone.utc).isoformat()
    for r in rows:
        c.execute('''INSERT OR IGNORE INTO candidate_links
          (source_url,candidate_url,title,source_name,score,reason,discovered_at)
          VALUES(?,?,?,?,?,?,?)''',(source_url,r.url,r.title,r.source,r.score,r.reason,now))
    c.commit(); c.close()

def scan_seed(url:str, ingest_top:int=10):
    body,sha,kind=fetch_resource(url)
    if kind!='html': return {'url':url,'status':'skip_non_html'}
    is_new=save_snapshot(url,body,sha)
    rows=adapter_for(url).discover(body,url)
    store_candidates(url,rows)
    ingested=[]
    for r in rows[:ingest_top]:
        try:
            body2,sha2,kind2=fetch_resource(r.url)
            save_snapshot(r.url,body2,sha2)
            parsed=parser_for(r.url)(body2,r.url)
            if parsed.get('decision_number') or parsed.get('article_numbers') or parsed.get('instrument_name'):
                persist_discovery(parsed); ingested.append(r.url)
        except Exception as e:
            ingested.append({'url':r.url,'error':str(e)[:180]})
    return {'url':url,'snapshot_new':is_new,'candidates':len(rows),'ingested':ingested}

def run_all():
    report=[]
    for u in SEED_URLS:
        try: report.append(scan_seed(u))
        except Exception as e: report.append({'url':u,'error':str(e)[:250]})
    return {'run_at':datetime.now(timezone.utc).isoformat(),'report':report}

if __name__=='__main__':
    print(json.dumps(run_all(),ensure_ascii=False,indent=2))
