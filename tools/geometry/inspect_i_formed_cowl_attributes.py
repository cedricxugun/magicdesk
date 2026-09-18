import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];s=json.loads((ROOT/'review/I_refinement/nautilus_r1/linear_drives_r20/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
inv=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();rows=[]
for o in bpy.data.objects['IN1_BodyRoot'].children_recursive:
    if o.type!='MESH' or 'formed_loft_t' not in o.data.attributes:continue
    a=o.data.attributes['formed_loft_t'];w=o.data.attributes['formed_wall_fraction'];points=[]
    for i,v in enumerate(o.data.vertices):
        if a.data[i].value<-.001:continue
        p=inv@o.matrix_world@v.co
        points.append({'t':a.data[i].value,'wall':w.data[i].value,'p':list(p),'r':(p.x*p.x+p.y*p.y)**.5})
    front=[p for p in points if abs(p['t'])<1e-6]
    rows.append({'mesh':o.name,'points':len(points),'front_count':len(front),'front_z':[min(p['p'][2]for p in front),max(p['p'][2]for p in front)]if front else [],'front_r':[min(p['r']for p in front),max(p['r']for p in front)]if front else [],'outer_front_r':[min(p['r']for p in front if p['wall']<.1),max(p['r']for p in front if p['wall']<.1)]if any(p['wall']<.1 for p in front)else []})
(ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/loft_attributes.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
