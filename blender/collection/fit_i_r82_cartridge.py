"""Static real-cartridge fit search in the R82 shell. Geometry, not drawn envelopes."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
body=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text());core=json.loads((OUT/'core_build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/body['source']));scene=bpy.context.scene;scene.frame_set(1)
bpy.ops.import_scene.gltf(filepath=str(R/core['component']))
root=bpy.data.objects['IAM_MODULE'];bpy.context.view_layer.update();inv=root.matrix_world.inverted()
def raw(o,relative=None):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();M=o.matrix_world if relative is None else relative@o.matrix_world
 vs=[M@v.co for v in me.vertices];ts=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();return vs,ts
def bbox(vs):return ([min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)])
def overlaps(a,b):return all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k]for k in range(3))
core_parts=[(o.name,*raw(o,inv))for o in root.children_recursive if o.type=='MESH']
names=[p['mesh']for p in body['panels']]+['R82_Fixed_Rear_Keel','R82_Acoustic_Chamber_Liner','R82_Aperture_Inner_Return','R82_Tangential_Aperture_Rolled_Lip']
states=[]
for f in [1,145]:
 scene.frame_set(f);items=[]
 for n in names:
  vs,ts=raw(bpy.data.objects[n]);items.append((n,BVHTree.FromPolygons(vs,ts,all_triangles=True),bbox(vs)))
 states.append((f,items))
pars=body['shape_parameters'];a=pars['END'];r=pars['RMAX'];g=pars['GROW'];C=Vector(pars['SHIFT'])+Vector((r*math.cos(a),-.44,r*math.sin(a)))
front=Vector((r*(g*math.cos(a)-math.sin(a)),-.44*3/1.25,r*(g*math.sin(a)+math.cos(a)))).normalized();back=-front
up=(Vector((0,0,1))-back*back.z).normalized();right=up.cross(back).normalized();basis=Matrix((right,up,back)).transposed()
rows=[];best=None
for scale,depth in [(q,d)for q in [.565,.55,.535]for d in [.03,0.,-.03,.06]]:
 M=basis.to_4x4();M.translation=C+back*depth;M=M@Matrix.Diagonal((scale,scale,scale,1.))
 contacts=[]
 for name,vs,ts in core_parts:
  world=[M@v for v in vs];bounds=bbox(world);tree=None
  for f,parts in states:
   for bn,bt,bb in parts:
    if not overlaps(bounds,bb):continue
    if tree is None:tree=BVHTree.FromPolygons(world,ts,all_triangles=True)
    hits=tree.overlap(bt)
    if hits:contacts.append({'frame':f,'core':name,'body':bn,'pairs':len(hits)})
 hard=[x for x in contacts if x['body'].startswith('R82_Porcelain')or x['body']=='R82_Tangential_Aperture_Rolled_Lip']
 rec={'scale':scale,'depth':depth,'contacts':contacts,'hard_contacts':len(hard),'score':len(hard)*10000+len(contacts)}
 rows.append(rec);print('MOUTH_FIT',scale,depth,'porcelain/lip',len(hard),'all',len(contacts),flush=True)
 if best is None or rec['score']<best['score']:best=rec
 if not hard:break
M=basis.to_4x4();M.translation=C+back*best['depth'];M=M@Matrix.Diagonal((best['scale'],best['scale'],best['scale'],1.));root.matrix_world=M
scene.frame_set(1)
source=R/'blender/collection/I_r82_cartridge_fit_r2.blend';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
report={'body_source':body['source'],'body_sha256':body['source_sha256'],'core_component':core['component'],'core_sha256':core['component_sha256'],'states':'Body closed and fully open against actual static REST cartridge. No tongue-motion, pressure extremes, fixtures or full acceptance.','trials':rows,'selected':best,'placement':{'matrix_blender':[list(v)for v in M],'center':list(C),'front':list(front),'scale':best['scale'],'depth':best['depth']},'source':source.relative_to(R).as_posix()}
(OUT/'fit_search.json').write_text(json.dumps(report,indent=2)+'\n')
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
 for dv in p.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100;cam=scene.camera
for n,f in [('core_fit_closed',1),('core_fit_open',145)]:
 scene.frame_set(f);cam.location=(-4,-7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1;scene.render.filepath=str(OUT/(n+'.png'));bpy.ops.render.render(write_still=True)
print('CORE_FIT_DONE',flush=True)
