"""Check real follower pins against the machined cam and fixed mouth hardware."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/r1';source=ROOT/'blender/collection/I_helix_r1.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
mouth=bpy.data.objects['IH1_Mouth'];drive=bpy.data.objects['IH1_IrisCamDrive'];drive.animation_data_clear()
cam=next(c for c in drive.children if c.type=='MESH' and 'IrisCamRing' in c.name)
leaves=[bpy.data.objects['IH1_IrisLeaf'+str(i)] for i in range(6)]
followers=[bpy.data.objects[leaf['cam_follower']] for leaf in leaves]
fixed=[o for o in mouth.children if o.type=='MESH' and any(s in o.name for s in ['IrisCarrier_','IrisOuterHousing_','IrisFrontShoulder_','CamRearSupport_'])]
objects=[cam]+followers+fixed;geometry={}
for obj in objects:
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();geometry[obj.name]=([v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles]);ev.to_mesh_clear()
for leaf in leaves:leaf.animation_data_clear()
def tree(obj):
    points,faces=geometry[obj.name];return BVHTree.FromPolygons([obj.matrix_world@p for p in points],faces,all_triangles=True)
collisions=[];errors=[];engagements=[]
for step in range(41):
    amount=step/40;drive.rotation_euler.z=-.30*amount
    for leaf in leaves:leaf.rotation_euler.z=leaf['home_angle']-leaf['iris_travel']*amount
    bpy.context.view_layer.update();ct=tree(cam);ft=[tree(o) for o in fixed]
    for i,(leaf,follower) in enumerate(zip(leaves,followers)):
        pin=tree(follower)
        if pin.overlap(ct):collisions.append({'amount':amount,'follower':i,'other':'cam'})
        for obj,other in zip(fixed,ft):
            if pin.overlap(other):collisions.append({'amount':amount,'follower':i,'other':obj.name})
        # Independent point evaluation in cam coordinates, matching its cut path.
        world=leaf.matrix_world@Vector((.05,.09,.060-leaf.location.z));actual=drive.matrix_world.inverted()@world
        phi=-1.05*amount;x=.6+.05*math.cos(phi)-.09*math.sin(phi);y=.05*math.sin(phi)+.09*math.cos(phi);a=i*math.tau/6+.30*amount
        expected=Vector((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0))
        errors.append((actual-expected).length)
        axis=drive.matrix_world.to_3x3()@Vector((0,0,1));axis.normalize()
        cam_z=[axis.dot(cam.matrix_world@p) for p in geometry[cam.name][0]];pin_z=[axis.dot(follower.matrix_world@p) for p in geometry[follower.name][0]]
        engagements.append(min(max(cam_z),max(pin_z))-max(min(cam_z),min(pin_z)))
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'positions':41,'follower_samples':len(errors),'max_cam_path_error':max(errors),'minimum_axial_engagement':min(engagements),'surface_intersections':collisions,'passed':not collisions and max(errors)<.000003 and min(engagements)>.009,'scope':'Six actual pin meshes vs cam and selected fixed mouth rings; cut-path closure and axial engagement. Does not cover all shell/support/assembly combinations.'}
(OUT/'cam_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_CAM_CHECK',result['passed'],'collisions',len(collisions),'error',max(errors),'engagement',min(engagements),flush=True)
if not result['passed']:raise SystemExit(1)
