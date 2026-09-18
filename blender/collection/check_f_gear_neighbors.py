"""Check new rims against nearby authored upper assembly over the baked F take."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'blender/collection/F_gear_refinement.blend';bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
roots=[bpy.data.objects[n] for n in ['F2_MainGear','F2_CounterGear']];rims=[bpy.data.objects['F4_InvoluteRim'+str(n)] for n in [36,22]]
objects=[o for o in bpy.data.objects['F_UPPER'].children_recursive if o.type=='MESH']
cache={}
for o in objects:
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    points=[v.co.copy() for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles];ev.to_mesh_clear()
    low=Vector(tuple(min(v[i] for v in points) for i in range(3)));high=Vector(tuple(max(v[i] for v in points) for i in range(3)))
    box=[Vector((x,y,z)) for x in [low.x,high.x] for y in [low.y,high.y] for z in [low.z,high.z]];cache[o.name]=(points,faces,box)
def bounds(o):
    points=[o.matrix_world@v for v in cache[o.name][2]]
    return ([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)])
def overlaps(a,b):return all(a[0][i]<b[1][i]-1e-7 and b[0][i]<a[1][i]-1e-7 for i in range(3))
def tree(o):
    points,faces,_=cache[o.name];return BVHTree.FromPolygons([o.matrix_world@v for v in points],faces,all_triangles=True)
dense="--dense-service" in sys.argv
frames=list(range(201)) if dense else sorted(set([1,scene.frame_end]+list(range(1,scene.frame_end+1,15))))
if dense:
    sys.path.insert(0,str(Path(__file__).parent));from f_gear_geometry import DISASSEMBLY_ROUTE,disassembly_offset
    parts=json.loads((ROOT/"app/assets/collection/models/F_complete.json").read_text())["parts"]
    for part in parts:bpy.data.objects[part["name"]].animation_data_clear()
collisions=[];pairs=set();narrow=0
for frame in frames:
    if dense:
        e=frame/200
        for part in parts:
            if part['name']=='F2_P_Differential':offset=disassembly_offset(e)
            else:
                t=max(0.,min(1.,(e-part['stage']*.25)/(1.-part['stage']*.25)));t=t*t*(3.-2*t);offset=[v*t for v in part['offset']]
            x,y,z=[a+b for a,b in zip(part['home']['p'],offset)];bpy.data.objects[part['name']].location=(x,-z,y)
    else:scene.frame_set(frame)
    bpy.context.view_layer.update();boxes={o.name:bounds(o) for o in objects};trees={}
    for root,rim in zip(roots,rims):
        own={root,*root.children_recursive}
        for other in objects:
            if other in own or other in rims:continue
            if not overlaps(boxes[rim.name],boxes[other.name]):continue
            if rim.name not in trees:trees[rim.name]=tree(rim)
            if other.name not in trees:trees[other.name]=tree(other)
            hits=trees[rim.name].overlap(trees[other.name]);narrow+=1;pairs.add((rim.name,other.name))
            if hits:collisions.append({'frame':frame,'rim':rim.name,'other':other.name,'triangles':len(hits)})
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frames':frames if not dense else [],'parked_service_fractions':[i/200 for i in frames] if dense else [],'narrow_phase_tests':narrow,'tested_pairs':[list(p) for p in sorted(pairs)],'surface_intersections':collisions,'passed':not collisions,'scope':'New rims vs other upper-assembly meshes. Dense mode samples201 parked service fractions via runtime part offsets and revised route; regular mode samples baked timeline. Own-wheel seating and continuous between-sample volume are excluded.'}
(ROOT/'review/F_complete/revision_20260911/gears'/('dense_service_check.json' if dense else 'neighbor_check.json')).write_text(json.dumps(report,indent=2)+'\n');print('F_GEAR_NEIGHBORS',json.dumps({k:v for k,v in report.items() if k not in ['surface_intersections','tested_pairs']}),'collisions',len(collisions),flush=True)
if collisions:raise SystemExit(1)
