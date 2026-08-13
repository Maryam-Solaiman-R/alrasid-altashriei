import re
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"


def _clean_url(href: str) -> str:
    if not href: return ""
    if href.startswith("//"): href = "https:" + href
    # Bing sometimes returns direct URLs; DDG uses uddg
    if "duckduckgo.com/l/?" in href:
        try: return unquote(parse_qs(urlparse(href).query).get("uddg", [href])[0])
        except Exception: return href
    return href

async def discover(query: str, domains: list[str], limit: int = 6) -> list[dict]:
    """Discover public web results restricted to the selected official domains.
    Uses public search result pages; no legislation is stored locally.
    """
    found=[]; seen=set()
    headers={"User-Agent":UA,"Accept-Language":"ar-SA,ar;q=0.9,en;q=0.7"}
    async with httpx.AsyncClient(timeout=25, follow_redirects=True, headers=headers) as client:
        for domain in domains:
            q=f"site:{domain} {query}"
            engines=[
                ("https://www.google.com/search?q="+quote_plus(q), "google"),
                ("https://html.duckduckgo.com/html/?q="+quote_plus(q), "ddg"),
                ("https://www.bing.com/search?q="+quote_plus(q), "bing"),
            ]
            for url, engine in engines:
                try:
                    r=await client.get(url)
                    if r.status_code != 200: continue
                    soup=BeautifulSoup(r.text,"html.parser")
                    candidates=[]
                    if engine=="google":
                        for a in soup.select('a'):
                            h=a.get('href','')
                            if h.startswith('/url?q='):
                                h=h.split('/url?q=',1)[1].split('&',1)[0]
                            candidates.append((a.get_text(' ',strip=True), h, ''))
                    elif engine=="ddg":
                        for a in soup.select('a.result__a'):
                            block=a.find_parent(class_=re.compile('result'))
                            snippet=block.get_text(' ',strip=True) if block else ''
                            candidates.append((a.get_text(' ',strip=True),a.get('href',''),snippet))
                    else:
                        for li in soup.select('li.b_algo'):
                            a=li.select_one('h2 a')
                            if a: candidates.append((a.get_text(' ',strip=True),a.get('href',''),li.get_text(' ',strip=True)))
                    for title, href, snippet in candidates:
                        href=_clean_url(href)
                        try: host=urlparse(href).netloc.lower()
                        except Exception: continue
                        if domain not in host or href in seen: continue
                        seen.add(href); found.append({"title":title or href,"url":href,"snippet":snippet[:900]})
                        if len(found)>=limit: return found
                    if found: break
                except Exception:
                    continue
    return found
