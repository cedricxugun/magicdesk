"""Measure a split-collar envelope at A's actual rear metal flange; no source edits."""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_c_core/mount_c1';OUT.mkdir(parents=True,exist_ok=True)
spec=json.loads((ROOT/'review/I_refinement/part_b_shell/linkage_b3/build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
placement=bpy.data.objects['IAM_MODULE'].matrix_world.copy()
profile=[(.570,.580),(.609,.580),(.613,.588),(.613,.638),(.561,.638),(.561,.6265),(.584,.6265),(.584,.594),(.570,.587)]
n=192;points=[];faces=[]
for radius,z in profile:
    points.extend(placement@Vector((radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n),z)) for i in range(n))
for k in range(len(profile)):
    for i in range(n):faces.append((k*n+i,k*n+(i+1)%n,((k+1)%len(profile))*n+(i+1)%n,((k+1)%len(profile))*n+i))
ring=BVHTree.FromPolygons(points,faces)
def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    pts=[e.matrix_world@v.co for v in m.vertices];tri=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    return pts,BVHTree.FromPolygons(pts,tri,all_triangles=True)
contacts=[];bounds={}
objects=[o for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH']+[bpy.data.objects[r['mesh']] for r in spec['rig']]+[bpy.data.objects[name] for name in spec['hardware'] if not name.startswith('IB3_Provisional') and name!='IB3_RailRootStudy']+[bpy.data.objects[spec['fixed_collar']]]
for frame in list(range(1,194,16)):
    scene.frame_set(frame);bpy.context.view_layer.update()
    for o in objects:
        pts,tree=geometry(o);hits=tree.overlap(ring)
        if hits:contacts.append({'frame':frame,'object':o.name,'triangles':len(hits)})
        if frame==1 and o.name in ['IAM_RearMountFlange_0074','IAM_EyelidFixedCarrier','IB2_FixedThroatInterface']:
            arr=np.array(pts);bounds[o.name]={'minimum':arr.min(axis=0).tolist(),'maximum':arr.max(axis=0).tolist()}
    print('C1_MOUNT_ENVELOPE',frame,len(contacts),flush=True)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'mount_profile_mouth_local':profile,'mouth_placement_blender':[list(r) for r in placement],'actual_interface_bounds':bounds,'contacts':contacts,'scope':'Unsplit metal collar-envelope candidate at measured rear flange. Checked against actual A source poses, six opening shells and B hardware at 13 source frames. No support arms, clamp bolts, containment, finished C or art acceptance.'}
(OUT/'mount_envelope.json').write_text(json.dumps(report,indent=2)+'\n')
