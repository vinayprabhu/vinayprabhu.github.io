"""Archive the public Google Site, its embedded content and directly used images.

Run with Python 3 and beautifulsoup4. Linked third-party sites are indexed, not mirrored.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit, urldefrag
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, mimetypes, re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent / 'content'
ORIGIN = 'https://www.vinayprabhu.com'

def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'PersonalWebsiteMigration/1.0', 'Referer': ORIGIN+'/'}), timeout=25) as r:
        return r.read(), r.headers.get_content_type(), r.status, r.url

def main():
    for folder in ['archive/raw', 'archive/embeds', 'assets/original', 'data']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    pages, seen, queue, images, failures = [], set(), [ORIGIN+'/home'], set(), []
    while queue:
        url=queue.pop(0)
        if url in seen: continue
        seen.add(url)
        slug=urlsplit(url).path.strip('/') or 'home'
        rawpath='archive/raw/'+slug.replace('/','--')+'.html'
        try:
            if (ROOT/rawpath).exists(): raw=(ROOT/rawpath).read_bytes()
            else: raw, mime, status, final = fetch(url)
        except Exception as e:
            failures.append({'url':url,'error':str(e)}); continue
        slug=urlsplit(url).path.strip('/') or 'home'
        rawpath='archive/raw/'+slug.replace('/','--')+'.html'
        (ROOT/rawpath).write_bytes(raw)
        soup=BeautifulSoup(raw,'html.parser')
        main=soup.select_one('.UtePc') or soup.select_one('[role="main"]') or soup.body
        links=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in soup.select('a[href]')]
        for link in links:
            p=urlsplit(link['url'])
            if p.netloc in ['www.vinayprabhu.com','vinayprabhu.com']:
                new=ORIGIN+(p.path.rstrip('/') or '/home')
                if new not in seen and new not in queue: queue.append(new)
        content_links=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in main.select('a[href]')]
        imgs=[{'url':urljoin(url,i.get('src','')),'alt':i.get('alt',i.get('aria-label',''))} for i in main.select('img[src]')]
        images.update(i['url'] for i in imgs)
        images.update(urljoin(url,i['src']) for i in soup.select('img[src]'))
        embeds=[]
        for i,e in enumerate(soup.select('[data-code]')):
            code=e['data-code']; path='archive/embeds/'+slug.replace('/','--')+f'-{i+1}.html.txt'
            (ROOT/path).write_text(code)
            es=BeautifulSoup(code,'html.parser')
            for x in es(['script','style']):x.decompose()
            embeds.append({'path':path,'text':es.get_text(' ',strip=True),'links':[{'text':a.get_text(' ',strip=True),'url':a['href']} for a in es.select('a[href]')]})
        iframes=[dict(e.attrs) for e in main.select('iframe')]
        blocks=[]
        for e in main.select('h1,h2,h3,h4,p,li'):
            if e.find_parent(['li','p']): continue
            if e.get_text(' ',strip=True):blocks.append({'tag':e.name,'html':str(e),'text':e.get_text(' ',strip=True)})
        page={'slug':slug,'url':url,'title':soup.title.get_text(' ',strip=True),'raw_file':rawpath,'text':main.get_text('\n',strip=True),'blocks':blocks,'links':content_links,'images':imgs,'embeds':embeds,'iframes':iframes}
        pages.append(page)
        (ROOT/'archive'/f'{slug.replace("/","--")}.txt').write_text(page['text']+'\n\n'+ '\n\n'.join(e['text'] for e in embeds))
        print(slug, len(raw),len(blocks),'blocks',len(imgs),'images',len(iframes),'frames',flush=True)
    previous={}
    if (ROOT/'data/original-content.json').exists():
        previous={a['url']:a for a in json.loads((ROOT/'data/original-content.json').read_text())['assets']}
    def download(url):
        if url in previous and previous[url].get('local_path') and (ROOT/previous[url]['local_path']).exists():return previous[url]
        try:
            raw,mime,status,final=fetch(url)
            ext=mimetypes.guess_extension(mime) or '.bin'
            path='assets/original/'+hashlib.sha256(url.encode()).hexdigest()[:16]+ext
            (ROOT/path).write_bytes(raw)
            return {'url':url,'local_path':path,'mime':mime,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        except Exception as e:return {'url':url,'error':str(e)}
    with ThreadPoolExecutor(max_workers=4) as pool: assets=list(pool.map(download,sorted(images)))
    data={'source':ORIGIN,'scraped_at':datetime.now(timezone.utc).isoformat(),'pages':pages,'assets':assets,'failures':failures,'scope':'All publicly linked same-domain pages and their directly embedded images. External links and iframe URLs retained; third-party websites and video streams are not mirrored.'}
    (ROOT/'data/original-content.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
    print('TOTAL',len(pages),'pages',len(assets),'assets','FAILURES',failures,[a for a in assets if 'error' in a],flush=True)

if __name__=='__main__': main()
