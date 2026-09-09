import pathlib,json,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
p=root/'app/assets/collection/registry.json';d=json.loads(p.read_text(encoding='utf-8'))
g=next(m for m in d['models'] if m['id']=='G');g['scene']='res://assets/collection/models/G_complete.glb';g['metadata']='res://assets/collection/models/G_complete.json'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=root/'app/assets/collection/control_profiles.json';original=subprocess.check_output(['git','show','HEAD:app/assets/collection/control_profiles.json'],cwd=root).decode('utf-8');d=json.loads(original)
hints={'leaf':'滚轮选第 1–6 页；也可横向拖动。每页分别记住折角和写入进度。','fold':'滚轮或横向拖动调折角；Shift＋滚轮精调。中央位置让三页光孔对准。','imprint':'对准后按住写入，松手停在当前位置；写满显出三维记忆，再按可重写。'}
for c in d['models']['G']:
    original=original.replace(json.dumps(c['hint'],ensure_ascii=False),json.dumps(hints[c['key']],ensure_ascii=False))
p.write_text(original,encoding='utf-8')
