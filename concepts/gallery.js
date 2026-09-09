let selected=new Set();
try{selected=new Set(JSON.parse(localStorage.getItem('magicdesk-art-selection')||'[]').filter(id=>MODELS.some(m=>m.id===id)))}catch{}
let filter='all';
const grid=document.getElementById('grid'),viewer=document.getElementById('viewer');
function render(){
 const visible=MODELS.filter(m=>filter==='all'||filter===m.group||filter==='selected'&&selected.has(m.id));
 grid.innerHTML=visible.map(m=>`<article class="model"><button class="image-button ${selected.has(m.id)?'selected':''}" data-image="${m.id}" aria-label="放大 ${m.id} ${m.name}"><img src="${m.image}" alt="${m.name}的造型与动作设定" loading="lazy"></button><div class="caption-top"><span class="letter">${m.id}</span><h3>${m.name}</h3><span class="status">${m.status}</span></div><p class="english">${m.en}</p><p>${m.hook}</p><p class="motion">${m.motion}</p><details><summary>操作方式与底座适配</summary><p>${m.controls}</p><p>${m.fit}</p>${m.control_plan?`<p><a href="${m.control_plan}">查看控制器映射草案</a></p>`:''}</details>${m.control_plan?'<p class="notice">操作匣待校正：图中按钮尚未全部对应功能。</p>':''}<div class="actions"><button class="action" data-select="${m.id}" aria-pressed="${selected.has(m.id)}">${selected.has(m.id)?'已加入候选':'加入候选'}</button>${m.exploded?`<button class="action" data-exploded="${m.id}">查看拆解</button>`:''}${m.design?`<a class="action" href="${m.design}">动效脚本</a>`:''}${m.actual?`<button class="action" data-actual="${m.id}">查看本机开发画面</button>`:''}</div></article>`).join('');
 document.getElementById('empty').hidden=visible.length>0;
 document.getElementById('selection').hidden=selected.size===0;
 document.getElementById('chosen').textContent='候选：'+MODELS.filter(m=>selected.has(m.id)).map(m=>m.id+' '+m.name).join('、');
 document.getElementById('compare').disabled=selected.size<2;
 document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===filter)));
}
function openImage(title,src,body=''){
 document.getElementById('dialogTitle').textContent=title;
 document.getElementById('dialogContent').innerHTML=`<img class="detail-image" src="${src}" alt="${title}">${body?`<div class="dialog-body">${body}</div>`:''}`;
 viewer.showModal();
}
grid.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.select){const id=b.dataset.select;selected.has(id)?selected.delete(id):selected.add(id);try{localStorage.setItem('magicdesk-art-selection',JSON.stringify([...selected]))}catch{}render();}
 else if(b.dataset.image){const m=MODELS.find(m=>m.id===b.dataset.image);openImage(m.id+' · '+m.name,m.image,`<p>${m.hook}</p><p><strong>招牌动作：</strong>${m.motion}</p><p><strong>专属操作：</strong>${m.controls}</p><p><strong>底座适配：</strong>${m.fit}</p>`)}
 else if(b.dataset.exploded){const m=MODELS.find(m=>m.id===b.dataset.exploded);openImage(m.id+' · '+m.name+' / 机械拆解',m.exploded,`<p>仅拆解物理机器，共同底座保持完整。模拟行星、黑洞和空间喉道不作为机械零件拆出。</p><p>${m.fit}</p>`)}
 else if(b.dataset.actual){const m=MODELS.find(m=>m.id===b.dataset.actual);openImage(m.id+' · '+m.name+' / 本机开发画面',m.actual,'<p>这是当前 App 的实际渲染，使用同一底座和相机。仍处于制作与视觉校正阶段，不代表 AAA 美术验收通过。</p>');}
});
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;render()}));
document.querySelectorAll('[data-board]').forEach(b=>b.addEventListener('click',()=>openImage(b.dataset.board==='selector'?'机械档案匣':'归档与重铸',b.querySelector('img').getAttribute('src'))));
document.getElementById('closeDialog').addEventListener('click',()=>viewer.close());
viewer.addEventListener('click',e=>{if(e.target===viewer)viewer.close()});
document.getElementById('clear').addEventListener('click',()=>{selected.clear();try{localStorage.removeItem('magicdesk-art-selection')}catch{}render()});
document.getElementById('compare').addEventListener('click',()=>{
 document.getElementById('dialogTitle').textContent='候选装置对比';
 document.getElementById('dialogContent').innerHTML='<div class="compare-grid">'+MODELS.filter(m=>selected.has(m.id)).map(m=>`<article><img src="${m.image}" alt="${m.name}"><h3>${m.id} · ${m.name}</h3><p>${m.hook}</p><p>${m.motion}</p><p>${m.controls}</p><p>${m.fit}</p></article>`).join('')+'</div>';
 viewer.showModal();
});
render();
