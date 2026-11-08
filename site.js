document.body.classList.add('js');
const menu=document.querySelector('.nav-toggle');
if(menu)menu.addEventListener('click',()=>{const nav=document.querySelector('#navigation');const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));menu.textContent=open?'Close':'Menu';});
const search=document.querySelector('#paper-search');
if(search){
 const buttons=[...document.querySelectorAll('.filter')];const papers=[...document.querySelectorAll('[data-paper]')];let category='all';
 const update=()=>{const q=search.value.trim().toLowerCase();let count=0;papers.forEach(p=>{const show=(category==='all'||p.dataset.category===category)&&p.textContent.toLowerCase().includes(q);p.hidden=!show;if(show)count++;});document.querySelector('#result-count').textContent=`${count} of ${papers.length} entries`;document.querySelector('#no-results').hidden=count>0;};
 search.addEventListener('input',update);buttons.forEach(b=>b.addEventListener('click',()=>{category=b.dataset.filter;buttons.forEach(x=>x.setAttribute('aria-pressed',String(x===b)));update();}));update();
}
