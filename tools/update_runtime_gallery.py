from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]
qa=ROOT/'tests/collection/delivery';out=ROOT/'concepts/runtime_preview'
assert json.loads((qa/'runtime_report.json').read_text())['all_passed']
out.mkdir(exist_ok=True)
states={'B':'B_selector','F':'F_open','G':'G_open','I':'I_open','J':'J_open','K':'K_open','L':'L_action','M':'M_closed','N':'N_action'}
for ident,name in states.items():shutil.copy2(qa/(name+'.png'),out/(ident+'.png'))
catalog=ROOT/'concepts/collection_20260909/catalog.json';items=json.loads(catalog.read_text())
for item in items:
    if item['id'] in states:
        item['actual']='runtime_preview/'+item['id']+'.png'
        item['status']='本机开发版' if item['id']=='B' else '首批在制'
catalog.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
(ROOT/'concepts/catalog.js').write_text('const MODELS = '+json.dumps(items,ensure_ascii=False,indent=2)+';\n')
p=ROOT/'concepts/gallery.js';s=p.read_text()
s=s.replace("${m.id==='B'?'<button class=\"action\" data-actual=\"B\">查看实际程序画面</button>':''}","${m.actual?`<button class=\"action\" data-actual=\"${m.id}\">查看本机开发画面</button>`:''}")
s=s.replace("else if(b.dataset.actual)openImage('B · 孵日器 / 已有程序画面','../review/final_star_peak.png');","else if(b.dataset.actual){const m=MODELS.find(m=>m.id===b.dataset.actual);openImage(m.id+' · '+m.name+' / 本机开发画面',m.actual,'<p>这是当前 App 的实际渲染，使用同一底座和相机。仍处于制作与视觉校正阶段，不代表 AAA 美术验收通过。</p>');}")
p.write_text(s)
print('RUNTIME_GALLERY_UPDATED',len(states))
