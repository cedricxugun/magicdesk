"""Inspect exact old functional mouth and identify only its obsolete outer cowl."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1';OUT.mkdir(parents=True,exist_ok=True)
spec=json.loads((R/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
m=bpy.data.objects['IAM_Mouth'];inv=m.matrix_world.inverted()
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 pts=[inv@o.matrix_world@v.co for v in o.data.vertices]
 rows.append({'name':o.name,'parent':o.parent.name if o.parent else None,'materials':[m.name for m in o.data.materials],
 'bounds':[[min(p[k]for p in pts),max(p[k]for p in pts)]for k in range(3)],
 'r_max':max((p.x*p.x+p.y*p.y)**.5 for p in pts),
 'verts':len(pts),'keys':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []})
outer=[r for r in rows if 'PorcelainUpper'in r['name']or'PorcelainLower'in r['name']or r['name'].startswith('IAM_Collar')]
core=[r for r in rows if r not in outer]
(OUT/'old_mouth_inventory.json').write_text(json.dumps({'source':spec['source'],'source_sha256':spec['source_sha256'],'outer_cowl':outer,'core':core,'scope':'Read-only inventory, no source mutation or removal yet'},indent=2)+'\n')
print('OUTER',[(r['name'],round(r['r_max'],4))for r in outer])
print('CORE_BIG',[(r['name'],round(r['r_max'],4),r['bounds'][2])for r in core if r['r_max']>.83])
print('COUNT',len(rows),len(core))
print('DIAPHRAGM',spec['diaphragm'])
