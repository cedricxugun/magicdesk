"""Current whole-source mouth-local occupancy; no source changes."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
report=ROOT/'review/I_refinement/nautilus_r1/linear_drives_r20/build.json'
s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
inv=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();rows=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    if not (o.name.startswith('IAM_') or any(t in o.name for t in ['Shoulder','Collar','Throat','FixedMouthCheek'])):continue
    points=[inv@o.matrix_world@v.co for v in o.data.vertices]
    rows.append({'name':o.name,'vertices':len(points),'bounds_min':[min(p[k] for p in points)for k in range(3)],'bounds_max':[max(p[k]for p in points)for k in range(3)],'materials':[m.name for m in o.data.materials if m]})
out=ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21';out.mkdir(parents=True,exist_ok=True)
(out/'source_occupancy.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'basis':'IAM_MODULE local Blender frame','parts':rows},indent=2)+'\n')
for r in rows:
    if any(t in r['name'] for t in ['Porcelain','Shoulder','Collar','FixedMouthCheek']):print(json.dumps(r))
