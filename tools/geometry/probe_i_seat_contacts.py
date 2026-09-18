import bpy,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r9';s=json.loads((p/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
report=[]
def geo(o):
    o.data.calc_loop_triangles();v=[o.matrix_world@x.co for x in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles];return v,f,BVHTree.FromPolygons(v,f,all_triangles=True)
for row in json.loads((p/'seat_contacts.json').read_text())['contacts']:
    a=bpy.data.objects[row['a']];b=bpy.data.objects[row['b']]
    if not b.name.startswith('IS9_'):a,b=b,a
    av,af,at=geo(a);bv,bf,bt=geo(b);pairs=at.overlap(bt)
    if not pairs:report.append({'partner':a.name,'seat':b.name,'resolved':True,'pairs':0});continue
    used={k for _,j in pairs for k in bf[j]};inv=b.parent.matrix_world.inverted();points=[inv@bv[k] for k in used]
    report.append({'partner':a.name,'seat':b.name,'local_min':[min(v[i] for v in points) for i in range(3)],'local_max':[max(v[i] for v in points) for i in range(3)],'contact_seat_vertices':[list(v) for v in points[:20]]})
(p/'contact_local_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
