"""Dense evaluated tooth-sector engagement sweep with existing fixed root transforms."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from f_gear_geometry import *
path=ROOT/'blender/collection/F_gear_refinement.blend';bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1)
roots=[bpy.data.objects[n] for n in ['F2_MainGear','F2_CounterGear']];rims=[bpy.data.objects['F4_InvoluteRim'+str(n)] for n in TEETH]
for root in roots:root.animation_data_clear()
home=[r.matrix_basis.copy() for r in roots]
def geometry(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    result=([v.co.copy() for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles]);ev.to_mesh_clear();return result
shapes=[geometry(o) for o in rims];hits=[];gaps=[]
for i in range(201):
    trim=(math.tau/36)/2.2*i/200
    for root,h,speed in zip(roots,home,[2.2,-3.6]):root.matrix_basis=h@Matrix.Rotation(trim*speed,4,'Y')
    bpy.context.view_layer.update()
    trees=[BVHTree.FromPolygons([o.matrix_world@v for v in shape[0]],shape[1],all_triangles=True) for o,shape in zip(rims,shapes)]
    overlap=trees[0].overlap(trees[1])
    if overlap:hits.append({'trim':trim,'triangles':len(overlap)})
    # Closest flank distances from actual wheel boundary at mid-width, independent of caps.
    gap=min(trees[1].find_nearest(rims[0].matrix_world@Vector((x,-.030,z)))[3] for x,z in outline(36,PHASE[0]));gaps.append(gap)
report={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':201,'main_angle':[0,math.tau/36],'teeth':TEETH,'center_distance':DISTANCE,'module':MODULE,'surface_intersections':hits,'closest_flank_gap':[min(gaps),max(gaps)],'passed':not hits and max(gaps)<.0007,'scope':'Actual evaluated beveled rims over one repeating tooth sector. Does not cover nearby housing/hub collisions or all assembly states.'}
out=ROOT/'review/F_complete/revision_20260911/gears/mesh_check.json';out.write_text(json.dumps(report,indent=2)+'\n');print('F_GEAR_MESH_CHECK',json.dumps(report),flush=True)
if not report['passed']:raise SystemExit(1)
