"""Build a dependency-free static site from the archived content. Requires beautifulsoup4."""
from pathlib import Path
from urllib.parse import urlsplit, urljoin, parse_qs
from html import escape as esc
from bs4 import BeautifulSoup, NavigableString, Tag
import json, shutil, re, zipfile

CODE_ROOT=Path(__file__).resolve().parent
ROOT=CODE_ROOT/'content'
if not (ROOT/'data/original-content.json').exists():
    with zipfile.ZipFile(CODE_ROOT/'site-content.zip') as bundle: bundle.extractall(ROOT)
for name in ['style.css','site.js']:
    shutil.copy2(CODE_ROOT/name,ROOT/'assets'/name)
OUT=CODE_ROOT/'dist'
DATA=json.loads((ROOT/'data/original-content.json').read_text())
PAGES={p['slug']:p for p in DATA['pages']}
ASSETS={a['url']:a for a in DATA['assets']}
ORIGIN='https://vinayprabhu.github.io'
SCHOLAR='https://scholar.google.com/citations?user=5Lck_J0AAAAJ&hl=en'
THESIS='https://kilthub.cmu.edu/articles/thesis/Network_Aided_Classification_and_Detection_of_Data/7430012'
TITLES={'home':'The original introduction','ai-safety':'AI safety & model auditing','snapshots':'Snapshots','media':'In the media','miscellaneous':'Beyond the lab','spice-cabinet':'The SPICE cabinet','spice-cabinet/ood':'OODles of ODDs','spice-cabinet/transformers':'Efficient transformers','spice-cabinet/all-you-need':'X is all you need'}
DECKS={'ai-safety':'Research on adversarial attacks, model auditing, dataset curation, and bias.','snapshots':'Research ideas, arguments, and visual essays in a single frame.','media':'Reporting, interviews, and conversations about my research.','miscellaneous':'Cricket, the playa, and a few other diversions.','spice-cabinet':'Survey Papers as Interactive Cheat-sheet Embedding. A visual, editable approach to reading a field.','spice-cabinet/ood':'A survey of out-of-distribution detection, and a wish list for the field.','spice-cabinet/transformers':'A visual companion to Efficient Transformers: A Survey by Tay et al.','spice-cabinet/all-you-need':'A survey of the papers that followed the “Attention is all you need” refrain.','home':'The text and links from vinayprabhu.com, preserved as part of the migration.'}

def link(url,label,cls=''):
    return f'<a href="{esc(url,quote=True)}"'+(f' class="{cls}"' if cls else '')+f'>{label}</a>'

def cleanurl(url):
    p=urlsplit(url)
    if p.netloc in ['www.google.com','google.com'] and p.path=='/url':url=parse_qs(p.query).get('q',[url])[0];p=urlsplit(url)
    # The original site linked to outdated repositories/paths for these PDFs.
    spice_files={'OOD_SPICE.pdf','efficient_transformers_spice.pdf','X_all_you_need.pdf'}
    if p.netloc in ['github.com','raw.githubusercontent.com'] and p.path.startswith(('/vinayprabhu/SPICEs/','/vinayprabhu/OODles_of_ODDs/')) and Path(p.path).name in spice_files:
        return 'https://github.com/vinayprabhu/SPICEs/blob/main/SPICE_CABINET/'+Path(p.path).name
    if p.netloc in ['vinayprabhu.com','www.vinayprabhu.com']:
        path=p.path.strip('/')
        if path=='home':return '/'
        return '/'+path+'/' + ('#'+p.fragment if p.fragment else '')
    if not p.netloc and url.startswith('/') and not url.endswith('/') and not Path(p.path).suffix:return url+'/'
    if url.startswith('#h.'):return '#original-text'
    return url

def head(title,desc,path):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Vinay Prabhu</title><meta name="description" content="{esc(desc,quote=True)}"><meta name="theme-color" content="#f5f3ed"><link rel="canonical" href="{ORIGIN+path}"><meta property="og:title" content="{esc(title,quote=True)} · Vinay Prabhu"><meta property="og:description" content="{esc(desc,quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{ORIGIN+path}"><meta property="og:image" content="{ORIGIN}/assets/portrait.png"><link rel="icon" type="image/svg+xml" href="/assets/favicon.svg"><link rel="stylesheet" href="/assets/style.css"><script src="/assets/site.js" defer></script></head>'''

def shell(title,desc,body,path='/',active=''):
    nav=''.join(link(u,label).replace('<a ', '<a aria-current="page" ',1) if active==label else link(u,label) for u,label in [('/','About'),('/research/','Research'),('/projects/','Projects'),('/media/','Media'),('/archive/','Archive')])
    return head(title,desc,path)+f'''<body><a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="wrap header-inner"><a class="wordmark" href="/">Vinay Prabhu<span>.</span></a><button class="nav-toggle" type="button" aria-expanded="false" aria-controls="navigation">Menu</button><nav id="navigation" aria-label="Main navigation">{nav}</nav></div></header><main id="main" class="wrap">{body}</main><section class="wrap contact" aria-labelledby="contact-title"><div><h2 id="contact-title">Ideas are better in conversation.</h2><p>Research, collaborations, or a good question.</p></div><a href="mailto:vinayup@gmail.com">vinayup@gmail.com ↗</a></section><footer><div class="wrap footer-inner"><span>© 2026 Vinay Uday Prabhu · A work in progress.</span><span><a href="{SCHOLAR}">Scholar ↗</a><a href="https://github.com/vinayprabhu">GitHub ↗</a><a href="/archive/">Site archive</a><a href="#main">Back to top ↑</a></span></div></footer></body></html>'''

def pagehead(title,deck,label='Research notebook'):
    return f'<header class="page-head"><div class="eyebrow">{esc(label)}</div><h1>{esc(title)}</h1><p class="deck">{deck}</p></header>'

def write(path,content):
    if path.endswith('.html'):
        content=content.replace('↗','<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16" fill="none"><path d="M3 13L13 3M3 3h10v10" stroke="currentColor" stroke-width="1.3"/></svg>')
    file=OUT/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(content)

def paper(title,url,category,description='',attrs=''):
    return f'<article class="paper" {attrs}><div class="meta">{esc(category)}</div><div><h3>{link(cleanurl(url),esc(title))}</h3>'+(f'<p>{description}</p>' if description else '')+f'</div><a class="arrow" href="{esc(cleanurl(url),quote=True)}" aria-label="Read {esc(title,quote=True)}">↗</a></article>'

def getpaper(key):
    return next(a for a in PAGES['ai-safety']['links'] if key.lower() in a['text'].lower())

def build_home():
    selected=''.join(paper(getpaper(k)['text'],getpaper(k)['url'],cat) for k,cat in [('Large image datasets','Datasets & ethics'),('Beyond the imitation game','Language models'),('Auditing saliency','Model auditing')])
    selected+=paper('Network Aided Classification and Detection of Data',THESIS,'Doctoral thesis · 2015','Carnegie Mellon University. Graph structure as a prior for classification and detection.')
    body=f'''<section class="hero" aria-labelledby="name"><div><div class="eyebrow">Research scientist · Builder · Tinkerer</div><h1 id="name">Vinay Uday<span>Prabhu.</span></h1><p class="lead">Machine learning, from first principles<br class="desktop-br"> to the physical world.</p><p class="intro">I work across machine learning, information theory, and scientific discovery. Currently, I’m building <a href="https://venomics.ai/">Venomics AI</a>, exploring venom-derived molecules as a starting point for new therapeutics.</p><div class="text-links"><a href="{SCHOLAR}">Google Scholar ↗</a><a href="https://github.com/vinayprabhu">GitHub ↗</a><a href="mailto:vinayup@gmail.com">Get in touch ↗</a></div></div><aside class="hero-aside"><div><img class="portrait" src="/assets/portrait.png" alt="Vinay at Burning Man, looking across the playa" width="460" height="460"><p class="portrait-caption">SOMEWHERE ON THE PLAYA</p></div><div class="current-note"><div class="kicker"><span class="status"></span>Currently building</div><p><a href="https://venomics.ai/">Venomics AI ↗</a></p><span style="font-size:12px;color:var(--muted)">Biodiversity, peptides & machine learning.</span></div></aside></section>
    <section class="section" aria-labelledby="venomics-journey"><p class="eyebrow">Interactive journey</p><h2 id="venomics-journey" style="font:clamp(25px,3vw,34px)/1.35 var(--serif);font-weight:400;max-width:850px;margin:12px 0 0"><a href="https://vinayprabhu.github.io/venomics/">Take a fun adventurous journey to see a venom evolve into a drug</a></h2></section>
    <section class="section"><div class="section-header"><h2><span class="section-number">01</span>Lines of inquiry</h2><a href="/research/">Explore the research ↗</a></div><div class="research-grid"><article><div class="topic-mark" aria-hidden="true">∑</div><h3>Learning & inference</h3><p>Graph structure, statistical physics, information theory, and the geometry of learning.</p><a href="{THESIS}">Doctoral research ↗</a></article><article><div class="topic-mark" aria-hidden="true">↔</div><h3>Auditing AI</h3><p>Adversarial robustness, dataset bias, and the gap between benchmark performance and the world.</p><a href="/ai-safety/">Safety, ethics & alignment ↗</a></article><article><div class="topic-mark" aria-hidden="true">⌘</div><h3>Science you can build</h3><p>Venom-derived therapeutics, frugal XR hardware, and embodied educational avatars.</p><a href="/projects/">Projects & experiments ↗</a></article></div></section>
    <section class="section"><div class="section-header"><h2><span class="section-number">02</span>Selected research</h2><a href="/research/">Browse all entries ↗</a></div>{selected}</section>
    <section class="section"><div class="section-header"><h2><span class="section-number">03</span>A brief trajectory</h2></div><div class="split"><div class="prose"><p>I began my research career at IIT Madras, working on wireless communication, sparse channel estimation, and time-of-arrival estimation. My doctoral research at Carnegie Mellon University brought together spectral graph theory, statistical physics, network science, and information theory.</p><p>After work on medical time series and drug interactions, I became the first employee and Chief Scientist at UnifyID AI Labs. We studied human kinematics through motion-sensor data and ran five AI fellowship cohorts between 2016 and 2021.</p><p>At HAL51, which I co-founded with <a href="https://www.linkedin.com/in/jjangsangy/">Sanghyun Han</a>, I built frugal XR hardware and explored the practical problems of putting AI avatars in classrooms. These days, my attention is on biology.</p></div><ol class="timeline"><li><strong>Venomics AI</strong><span>Building at the intersection of AI and venom biology.</span></li><li><strong>HAL51 · LemurBox</strong><span>Frugal science, XR, and educational AI avatars.</span></li><li><strong>UnifyID AI Labs</strong><span>Chief Scientist & first employee. <a href="https://www.prove.com/blog/prove-acquires-unifyid">Acquired by Prove in 2021 ↗</a></span></li><li><strong>Carnegie Mellon University</strong><span>Doctoral research. <a href="{THESIS}">PhD thesis, 2015 ↗</a></span></li><li><strong>IIT Madras</strong><span>Information theory and wireless communications.</span></li></ol></div></section>
    <section class="section"><div class="section-header"><h2><span class="section-number">04</span>Elsewhere in the notebook</h2></div><div class="index-links"><a class="index-link" href="/spice-cabinet/"><div><strong>The SPICE cabinet</strong><small>Interactive visual surveys of machine learning.</small></div><span>↗</span></a><a class="index-link" href="https://alignchronicles.github.io/"><div><strong>Alignment chronicles</strong><small>Writing and explorations in AI safety.</small></div><span>↗</span></a><a class="index-link" href="/snapshots/"><div><strong>Snapshots</strong><small>Research arguments, distilled into a frame.</small></div><span>↗</span></a><a class="index-link" href="/miscellaneous/"><div><strong>Beyond the lab</strong><small>Cricket, Burning Man, and Camp BYTE.</small></div><span>↗</span></a></div></section>'''
    write('index.html',shell('Research, ideas & experiments','Vinay Uday Prabhu: machine learning, AI safety, information theory, and venom-derived drug discovery.',body,active='About'))
    write('home/index.html','<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/"><title>Vinay Prabhu</title><a href="/">Continue to Vinay Prabhu’s website</a>')

def build_research():
    entries=[];category='Auditing & robustness'
    for a in PAGES['ai-safety']['links']:
        title=a['text']
        if title in ['Video','Project page','here']:continue
        if title.startswith('Multimodal datasets'):category='Datasets & ethics'
        entries.append((title,a['url'],category))
    entries.append(('Network Aided Classification and Detection of Data',THESIS,'Theory & inference'))
    for a in PAGES['home']['links']:
        if any(k in a['text'] for k in ['channel estimation','time-of-arrival','Latent sentiment','Bipartisan cloture','Outage secrecy','Filter design']):entries.append((a['text'][0].upper()+a['text'][1:],a['url'],'Theory & inference'))
    buttons=''.join(f'<button type="button" class="filter" data-filter="{esc(c,quote=True)}" aria-pressed="{str(i==0).lower()}">{esc(label)}</button>' for i,(c,label) in enumerate([('all','All'),('Auditing & robustness','Auditing & robustness'),('Datasets & ethics','Datasets & ethics'),('Theory & inference','Theory & inference')]))
    rows=''.join(paper(t,u,c,attrs=f'data-paper data-category="{esc(c,quote=True)}"') for t,u,c in entries)
    body=pagehead('Research','Selected publications, research notes, and my doctoral thesis. The complete and current publication record is on <a href="'+SCHOLAR+'">Google Scholar ↗</a>.','Publications & ideas')
    body+=f'<div class="page-main"><div class="toolbar"><div class="filters" aria-label="Filter research">{buttons}</div><label><span class="kicker">Search entries</span><br><input id="paper-search" class="search" type="search" placeholder="A topic or paper title…"></label></div><p id="result-count" class="count" aria-live="polite">{len(entries)} entries</p>{rows}<p id="no-results" hidden>No matching entries. Try another search or category.</p><p class="source-note">These entries were linked from the original website. Titles and source links are retained; publication dates and venues are shown only where verified.</p></div>'
    write('research/index.html',shell('Research','Publications and research on AI safety, datasets, graph inference, and information theory.',body,'/research/','Research'))
    (ROOT/'data/research.json').write_text(json.dumps([{'title':t,'url':u,'category':c} for t,u,c in entries],indent=2))

def build_projects():
    projects=[('01 / NOW','Venomics AI','I’m building Venomics AI to explore venom-derived molecules for therapeutic discovery. The work brings biodiversity and machine learning into the same research programme.',[('https://venomics.ai/','Visit Venomics AI')]),('02 / HARDWARE','HAL51 & LemurBox','At HAL51, co-founded with Sanghyun Han, I developed frugal XR hardware. LemurBox turns a smartphone into a display for a rigged, LLM-powered 3D avatar. Bringing these educational avatars into classrooms made AI safety a practical engineering problem.',[('https://hal51.ai/','HAL51'),('https://www.youtube.com/watch?v=caEJpOOrN1k','LemurBox demo'),('https://www.youtube.com/watch?v=J-ihwfPD3YA','In the classroom'),('https://www.linkedin.com/in/jjangsangy/','Sanghyun Han')]),('03 / KINEMATICS','UnifyID AI Labs','As the first employee and Chief Scientist, I worked on modelling human kinematics using IMU motion-sensor data. I also ran an AI fellowship spanning five cohorts between 2016 and 2021. UnifyID was acquired by Prove in 2021.',[('https://www.youtube.com/watch?v=XkCzDkpT6dI','Kinematics talk'),('https://sites.google.com/unify.id/ai-fellowship/','AI fellowship'),('https://www.prove.com/blog/prove-acquires-unifyid','Acquisition announcement')]),('04 / VISUAL SURVEYS','The SPICE cabinet','Survey Papers as Interactive Cheat-sheet Embedding: visual, editable surveys that let readers follow references and see a field at a glance. The collection covers out-of-distribution detection, transformer architectures, and “X is all you need” papers.',[('/spice-cabinet/','Explore the cabinet'),('https://github.com/vinayprabhu/SPICEs','Source'),('https://youtu.be/uzx2gxOhn14','Walkthrough')]),('05 / AFTER HOURS','Art on the playa','From time to time, I write code, blog, and bring experiments to Burning Man. Camp BYTE stands for Burners for Ÿntelligent Technology Emancipation.',[('https://youtu.be/sMcYkzWC2rI?feature=shared','Watch'),('/miscellaneous/','Beyond the lab')])]
    body=pagehead('Projects & experiments','A selection of things I’ve built, investigated, and brought into the world.','From ideas to things')+'<div class="page-main">'
    for n,t,p,links in projects:body+=f'<article class="project"><div class="project-index">{n}</div><div><h2>{t}</h2><p>{p}</p><div class="text-links">'+''.join(link(u,esc(l)+' ↗') for u,l in links)+'</div></div></article>'
    body+='</div>';write('projects/index.html',shell('Projects & experiments','Venomics AI, HAL51 and LemurBox, UnifyID AI Labs, SPICE visual surveys, and art.',body,'/projects/','Projects'))

def sanitized(node):
    if isinstance(node,NavigableString):return esc(str(node))
    if not isinstance(node,Tag):return ''
    if node.name in ['script','style','head','iframe','img','svg','button']:return ''
    if node.name=='a':
        url=cleanurl(node.get('href',''))
        if not url or urlsplit(url).scheme not in ['', 'https','http','mailto']:return ''.join(sanitized(c) for c in node.children)
        return link(url,''.join(sanitized(c) for c in node.children))
    children=''.join(sanitized(c) for c in node.children)
    if node.name in ['p','h2','h3','h4','ul','ol','li','strong','em','b','i','blockquote','sup','sub']:
        return f'<{node.name}>'+children+f'</{node.name}>'
    if node.name=='h1':return '<h2>'+children+'</h2>'
    if node.name=='br':return '<br>'
    return children

def figure(image,caption=''):
    asset=ASSETS.get(image['src'],{})
    caption=caption or image.get('alt') or 'Image from the original website'
    if 'local_path' in asset:
        src='/'+asset['local_path']
        return f'<figure><a href="{src}" aria-label="Open full-size image: {esc(caption,quote=True)}"><img src="{src}" alt="{esc(caption,quote=True)}" loading="lazy"></a><figcaption>{esc(caption)}</figcaption></figure>'
    return f'<figure><div class="missing">The original host did not provide this image during migration. {link(image["src"],"Original image ↗")}</div><figcaption>{esc(caption)}</figcaption></figure>'

def original_article(slug):
    s=BeautifulSoup((ROOT/PAGES[slug]['raw_file']).read_text(),'html.parser')
    root=s.select_one('.UtePc')
    blocks=[b for b in root.select('.tyJCtd') if not b.find_parent(class_='tyJCtd')]
    output=[]
    for i,b in enumerate(blocks):
        img=b.select_one('img')
        if img:
            caption=''
            if i+1<len(blocks) and not blocks[i+1].select_one('img'):caption=blocks[i+1].get_text(' ',strip=True)
            output.append('<div class="gallery">'+figure(img,caption)+'</div>');continue
        embed=b.select_one('[data-code]')
        if embed:
            embedded=BeautifulSoup(embed['data-code'],'html.parser')
            for f in embedded.select('iframe[src]'):
                output.append(link(f['src'],'Open interactive survey ↗','video-link'))
            continue
        for f in b.select('iframe[src]'):
            src=f['src'];title=f.get('aria-label','Watch video').replace('YouTube Video, ','')
            if 'youtube.com/embed/' in src:src='https://www.youtube.com/watch?v='+urlsplit(src).path.split('/')[-1]
            output.append(link(src,esc(title),'video-link'))
        text=sanitized(b)
        if text.strip():output.append(text)
    return ''.join(output)

def build_original_pages():
    for slug,p in PAGES.items():
        if slug=='home':continue
        body=pagehead(TITLES[slug],DECKS[slug],'Visual notebook' if slug=='snapshots' else 'Collected work')
        if slug=='snapshots':
            s=BeautifulSoup((ROOT/p['raw_file']).read_text(),'html.parser')
            blocks=[b for b in s.select('.UtePc .tyJCtd') if not b.find_parent(class_='tyJCtd')]
            figs=[]
            for i,b in enumerate(blocks):
                image=b.select_one('img')
                if image:figs.append(figure(image,blocks[i+1].get_text(' ',strip=True) if i+1<len(blocks) else 'Research snapshot'))
            body+='<div class="page-main"><div class="gallery">'+''.join(figs)+'</div></div>'
        elif slug=='media':
            # Preserve every story, associated original image, and link, including unlabeled linked images.
            s=BeautifulSoup((ROOT/p['raw_file']).read_text(),'html.parser')
            blocks=[b for b in s.select('.UtePc .tyJCtd') if not b.find_parent(class_='tyJCtd')]
            cards=[];pending_image=None
            for b in blocks:
                image=b.select_one('img')
                if image:pending_image=image
                anchors=b.select('a[href]')
                if anchors:
                    a=anchors[0];label=a.get_text(' ',strip=True) or 'Research coverage'
                    asset=ASSETS.get(pending_image['src'],{}) if pending_image else {}
                    pic=f'<img src="/{asset["local_path"]}" alt="Illustration accompanying {esc(label,quote=True)}" loading="lazy">' if 'local_path' in asset else ''
                    cards.append(f'<article class="media-item"><div class="media-source">{esc(urlsplit(cleanurl(a["href"])).netloc.removeprefix("www."))}</div>{pic}<h2>{link(cleanurl(a["href"]),esc(label)+" ↗")}</h2>'+(''.join(link(cleanurl(x['href']),esc(x.get_text(' ',strip=True))) for x in anchors[1:]))+'</article>');pending_image=None
            body+='<div class="page-main"><div class="media-grid">'+''.join(cards)+'</div><a class="video-link" href="https://www.youtube.com/watch?v=wV0dDIoppsw">Interview at Data by the Bay</a><details><summary>Original media page, with all captions</summary><div class="article">'+original_article(slug)+'</div></details></div>'
        else:
            extra=''
            if slug=='ai-safety':extra='<div class="callout"><a href="/research/">Search and filter the complete research index ↗</a></div>'
            body+='<div class="page-main article" id="original-text">'+extra+original_article(slug)+'</div>'
        body+=f'<p class="source-note">Migrated from <a href="{esc(p["url"])}">vinayprabhu.com</a>. Original wording is retained on this collection page. <a href="/archive/">Download the source archive ↗</a></p>'
        write(slug+'/index.html',shell(TITLES[slug],DECKS[slug],body,'/'+slug+'/', 'Media' if slug=='media' else 'Research' if slug=='ai-safety' else 'Archive'))

def build_archive():
    body=pagehead('The archive','All nine pages of the original site, with their text, links, embedded-widget source, and available images.','Preserved, reorganised')
    body+='<div class="page-main"><ul class="archive-list">'
    for slug in PAGES:
        url='/archive/home/' if slug=='home' else '/'+slug+'/'
        body+=f'<li>{link(url,esc(TITLES[slug])+" ↗")}<small>{esc(slug)}</small></li>'
    body+='</ul><div class="text-links"><a href="/downloads/vinayprabhu-original-site.zip" download>Download original-site archive ↓</a><a href="/data/original-content.json" download>Structured content (JSON) ↓</a></div>'
    failed=[a for a in DATA['assets'] if 'error' in a]
    body+=f'<div class="callout"><p>Captured 8 November 2026: {len(PAGES)} pages, {len(DATA["assets"])-len(failed)} downloaded image assets, and all discovered content links. {len(failed)} image URLs returned HTTP 403; their original URLs remain in the archive. Linked external websites, videos, and hosted documents remain at their original destinations.</p></div><details><summary>Migration notes</summary><div class="article"><p>The homepage has been edited for clarity. Collection pages preserve the original wording, including unfinished notes. The old neon animations are preserved as source files. Interactive surveys and videos have direct links so readers can open them without loading third-party players automatically.</p><p>The original domain remains unchanged. This copy is hosted on GitHub Pages. The existing project-site links, including the original <a href="https://vinayprabhu.github.io/alignchronicles/">blog link</a>, are retained in the structured archive.</p></div></details></div>'
    write('archive/index.html',shell('Archive','All original website pages, images, links, and downloadable source content.',body,'/archive/','Archive'))
    body=pagehead('The original introduction',DECKS['home'],'From the original site')+'<div class="article page-main">'+original_article('home')+'</div>'
    write('archive/home/index.html',shell('Original introduction',DECKS['home'],body,'/archive/home/','Archive'))

def main():
    OUT.mkdir(exist_ok=True)
    shutil.copytree(ROOT/'assets',OUT/'assets',dirs_exist_ok=True)
    (OUT/'downloads').mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT/'downloads/vinayprabhu-original-site.zip','w',zipfile.ZIP_DEFLATED) as z:
        for folder in ['archive','assets/original','data']:
            for f in (ROOT/folder).rglob('*'):
                if f.is_file():z.write(f,f.relative_to(ROOT))
    build_home();build_research();build_projects();build_original_pages();build_archive()
    shutil.copytree(ROOT/'data',OUT/'data',dirs_exist_ok=True)
    write('.nojekyll','')
    write('robots.txt','User-agent: *\nAllow: /\nSitemap: '+ORIGIN+'/sitemap.xml\n')
    pages=['/','/research/','/projects/','/archive/']+['/'+s+'/' for s in PAGES if s!='home']
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+ORIGIN+p+'</loc></url>' for p in pages)+'</urlset>')
    write('404.html',shell('Page not found','Page not found.',pagehead('A page out of place.','This address does not belong to the new site. Try the <a href="/archive/">archive</a>, or return to the <a href="/">homepage</a>.','404'),'/404.html'))
    print('Built',len(list(OUT.rglob('*.html'))),'HTML pages')

if __name__=='__main__':main()
