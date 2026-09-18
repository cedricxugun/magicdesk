import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=json.loads((ROOT/'review/I_refinement/nautilus_r1/uniform_precision_r29/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
    if o.type!='MESH'or not any(t in o.name for t in ['CellFilm','CellFrame','ChamberRib']):continue
    points=[o.matrix_world@v.co for v in o.data.vertices];rows.append({'mesh':o.name,'vertices':len(points),'faces':len(o.data.polygons),'uv_layers':[u.name for u in o.data.uv_layers],'materials':[m.name for m in o.data.materials if m],'bounds':[[min(p[k]for p in points)for k in range(3)],[max(p[k]for p in points)for k in range(3)]]})
out=ROOT/'review/I_refinement/nautilus_r1/chamber_response_r35';out.mkdir(parents=True,exist_ok=True);(out/'source_inventory.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'meshes':rows},indent=2)+'\n')
for r in rows:
    if r['mesh'].endswith(('03','07','12')):print(json.dumps(r),flush=True)
