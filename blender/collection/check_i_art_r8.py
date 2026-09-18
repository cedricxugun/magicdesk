"""Actual new liner solids and acoustic retainer support checks."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/art_r8';spec=json.loads((OUT/'build.json').read_text())
source=ROOT/spec['source'];bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
def tree(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    result=BVHTree.FromPolygons([obj.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return result
rows=[]
for item in spec['liners']:
    liner=bpy.data.objects[item['name']];back=bpy.data.objects[item['backing']];shell=bpy.data.objects[item['shell']]
    bm=bmesh.new();bm.from_mesh(liner.data);edges=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
    rows.append({'name':liner.name,'nonmanifold_edges':edges,'volume':volume,'liner_shell':len(tree(liner).overlap(tree(shell))),'backing_shell':len(tree(back).overlap(tree(shell))),'liner_backing':len(tree(liner).overlap(tree(back)))})
front=bpy.data.objects[spec['retainer']];rear=bpy.data.objects[spec['rear_shoulder']];parent=front.parent;tf=tree(front);tr=tree(rear);seats=[]
for i in range(24):
    from math import sin,cos,tau
    a=i*tau/24;p=Vector((.549*cos(a),.549*sin(a),.1));axis=(parent.matrix_world.to_3x3()@Vector((0,0,1))).normalized();origin=parent.matrix_world@p
    hf,_,_,_=tf.ray_cast(origin,-axis);hr,_,_,_=tr.ray_cast(origin,axis)
    seats.append({'front_error':abs((parent.matrix_world.inverted()@hf).z-.094) if hf is not None else None,'rear_error':abs((parent.matrix_world.inverted()@hr).z-.106) if hr is not None else None})
passed=all(r['nonmanifold_edges']==0 and r['volume']>0 and r['liner_shell']==0 and r['backing_shell']==0 and r['liner_backing']==0 for r in rows) and all(r['front_error'] is not None and r['rear_error'] is not None and max(r['front_error'],r['rear_error'])<.00002 for r in seats)
result={'passed':passed,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'liners':rows,'retainer_samples':seats,'scope':'New liner solids/backing/own-shell contact and plate clamp seating samples. Does not certify all new flanges versus other components, complete service motion or artistic acceptance.'}
(OUT/'detail_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_ART_DETAIL_CHECK',passed,[r for r in rows if r['nonmanifold_edges'] or r['liner_shell'] or r['backing_shell'] or r['liner_backing']],flush=True)
