"""Locate actual contact triangles in the existing cassette coordinate frame."""
import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'review/I_refinement/nautilus_r1/linear_drives_r20'
s=json.loads((p/'build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
inverse=bpy.data.objects['IN2_Cassette03_Frame'].matrix_world.inverted()
def mesh(name):
    o=bpy.data.objects[name];o.data.calc_loop_triangles()
    v=[inverse@o.matrix_world@p.co for p in o.data.vertices]
    t=[tuple(t.vertices) for t in o.data.loop_triangles]
    return v,t,BVHTree.FromPolygons(v,t,all_triangles=True)
rows=[]
contacts=json.loads((p/'internal_contacts.json').read_text())['unresolved_contacts']
for r in contacts:
    if r['opening']!=0 or '03' not in r['a']:continue
    av,at,a=mesh(r['a']);bv,bt,b=mesh(r['b']);hits=a.overlap(b)
    points=[av[k] for i,j in hits for k in at[i]]+[bv[k] for i,j in hits for k in bt[j]]
    if points:rows.append({'a':r['a'],'b':r['b'],'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]})
(p/'pressure_contact_bounds.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
