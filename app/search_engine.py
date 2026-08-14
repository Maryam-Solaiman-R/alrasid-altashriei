import re, io, asyncio
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36'
HEADERS={'User-Agent':UA,'Accept-Language':'ar-SA,ar;q=0.9,en;q=0.7'}

def _clean_url(href):
    if not href: return ''
    if href.startswith('//'): href='https:'+href
    if href.startswith('/url?q='): href=href.split('/url?q=',1)[1].split('&',1)[0]
    if 'duckduckgo.com/l/?' in href:
        try: return unquote(parse_qs(urlparse(href).query).get('uddg',[href])[0])
        except Exception: pass
    return href

def _norm(s): return re.sub(r'\s+',' ',s or '').strip()

def expand_queries(q):
    base=_norm(q); qs=[base]
    # Legislative-intent expansions without AI.
    if any(x in base for x in ['تعديل','تعديلات','تغير','تغيّر','الفرق','قبل','بعد']):
        qs += [f'"{base}" قرار تعديل', f'{base} تعديل مواد قرار', f'{base} النسخة المعدلة']
    if 'لائحة' in base or 'اللائحة' in base:
        qs += [f'{base} قرار', f'{base} مواد', f'{base} pdf']
    if 'نظام' in base:
        qs += [f'{base} مرسوم قرار', f'{base} مواد']
    out=[]
    for x in qs:
        if x not in out: out.append(x)
    return out[:6]

async def _engine_results(client,q,domain):
    found=[]
    engines=[('https://www.google.com/search?q='+quote_plus(f'site:{domain} {q}'),'google'),
             ('https://html.duckduckgo.com/html/?q='+quote_plus(f'site:{domain} {q}'),'ddg'),
             ('https://www.bing.com/search?q='+quote_plus(f'site:{domain} {q}'),'bing')]
    for url,engine in engines:
        try:
            r=await client.get(url); 
            if r.status_code!=200: continue
            soup=BeautifulSoup(r.text,'html.parser'); candidates=[]
            if engine=='google':
                for a in soup.select('a'):
                    h=a.get('href',''); title=a.get_text(' ',strip=True)
                    if h.startswith('/url?q=') or domain in h: candidates.append((title,h,''))
            elif engine=='ddg':
                for a in soup.select('a.result__a'):
                    block=a.find_parent(class_=re.compile('result')); candidates.append((a.get_text(' ',strip=True),a.get('href',''),block.get_text(' ',strip=True) if block else ''))
            else:
                for li in soup.select('li.b_algo'):
                    a=li.select_one('h2 a')
                    if a: candidates.append((a.get_text(' ',strip=True),a.get('href',''),li.get_text(' ',strip=True)))
            for title,href,snip in candidates:
                href=_clean_url(href)
                try: host=urlparse(href).netloc.lower()
                except: continue
                if domain in host: found.append({'title':_norm(title) or href,'url':href,'snippet':_norm(snip)[:1000]})
            if found: break
        except Exception: continue
    return found

async def fetch_document(client,item):
    url=item['url']
    try:
        r=await client.get(url,timeout=30)
        if r.status_code!=200: return item
        ctype=(r.headers.get('content-type') or '').lower()
        text=''
        if 'pdf' in ctype or url.lower().split('?')[0].endswith('.pdf'):
            try:
                reader=PdfReader(io.BytesIO(r.content))
                text=' '.join((p.extract_text() or '') for p in reader.pages[:35])
                item['document_type']='PDF'
            except Exception: text=''
        else:
            soup=BeautifulSoup(r.text,'html.parser')
            for tag in soup(['script','style','nav','footer','header','noscript']): tag.decompose()
            text=soup.get_text(' ',strip=True); item['document_type']='HTML'
            if not item.get('title'):
                item['title']=_norm(soup.title.get_text()) if soup.title else url
        item['content']=_norm(text)[:80000]
        item['snippet']=item.get('snippet') or item['content'][:900]
    except Exception: pass
    return item

async def discover(query,domains,limit=18):
    seen={}; queries=expand_queries(query)
    async with httpx.AsyncClient(timeout=25,follow_redirects=True,headers=HEADERS) as client:
        # Search selected official domains concurrently, with query expansion.
        jobs=[_engine_results(client,q,d) for d in domains for q in queries[:4]]
        batches=await asyncio.gather(*jobs,return_exceptions=True)
        for batch in batches:
            if isinstance(batch,list):
                for x in batch:
                    if x['url'] not in seen: seen[x['url']]=x
        items=list(seen.values())[:max(limit,12)]
        # Layer 2: read actual official pages/PDFs, not just search snippets.
        enriched=await asyncio.gather(*(fetch_document(client,x) for x in items),return_exceptions=True)
        out=[x for x in enriched if isinstance(x,dict)]
    return out[:limit]
