"""R82 r8: preserve the clear r6 cover paths and package the front bearing
closer to the rear bearing. Move the complete bearing stack, not just a cover."""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];IN=R/'review/I_refinement/nautilus_reset_r82/mechanism_r6'
FULL='--full-frames' in sys.argv
variant='mechanism_r9' if FULL else 'mechanism_r8'
OUT=R/'review/I_refinement/nautilus_reset_r82'/variant;OUT.mkdir(parents=True,exist_ok=True)
SRC=R/('blender/collection/I_nautilus_reset_r82_'+variant+'.blend');assert not SRC.exists()
d=json.loads((IN/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));s=bpy.context.scene;s.frame_set(1)
def raw(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 vs=[o.matrix_world@v.co for v in me.vertices];fs=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();return vs,fs
def tree(vs,ts):
 return (BVHTree.FromPolygons(vs,ts,all_triangles=True),[min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)])
def hit(a,b):return all(a[1][k]<=b[2][k] and b[1][k]<=a[2][k]for k in range(3))and bool(a[0].overlap(b[0]))
names=['R82_R4_Forged_Saddle_-1']+[f'R82_R3_{stem}_-1'for stem in ['Bearing','Seal','Bearing_Shoulder','Axle_Endcap','Axle_Index']]
members=[bpy.data.objects[n]for n in names];geometry=[raw(o)for o in members]
# Cache only static local triangles, then stream frames; do not retain 300 BVHs.
local_shapes=[]
for p in d['panels']:
 ob=bpy.data.objects[p['mesh']];node=bpy.data.objects[p['node']];vs,fs=raw(ob);inv=node.matrix_world.inverted()
 local_shapes.append((node,[inv@v for v in vs],fs))
frames=list(range(1,301)) if FULL else list(range(1,301,10))+[300]
peer_contacts=[]
results=[];selected=None
for delta in ([.15,.18,.21] if FULL else [.06,.09,.12,.15,.18,.21]):
 bodies=[tree([v+Vector((0,delta,0))for v in vs],ts)for vs,ts in geometry];conflicts=[]
 peer_contacts=[]
 for f in frames:
  s.frame_set(f)
  shapes=[tree([node.matrix_world@v for v in vs],fs)for node,vs,fs in local_shapes]
  for i,a in enumerate(shapes):
   for j,b in enumerate(shapes[i+1:],i+1):
    if hit(a,b):peer_contacts.append({'frame':f,'a':i+1,'b':j+1})
  for i,a in enumerate(shapes):
   for j,b in enumerate(bodies):
    if hit(a,b):conflicts.append({'frame':f,'panel':i+1,'part':names[j]})
  if conflicts:break
  if f%30==0:print('R9_FRAME',delta,f,flush=True)
 results.append({'delta_y':delta,'conflicts':conflicts})
 print('R8_PACKAGE',delta,len(conflicts),flush=True)
 if not conflicts:selected=delta;break
(OUT/'saddle_packaging_search.json').write_text(json.dumps({'scope':str(len(frames))+' sampled poses; all six ceramics versus complete moved front bearing stack; ceramic-peer pairs also checked. Not a continuous-time or all-internals proof.','frame_samples':len(frames),'results':results,'selected_delta_y':selected,'peer_contacts':peer_contacts},indent=2)+'\n')
assert selected is not None and not peer_contacts,('Unresolved geometry',selected,len(peer_contacts))
s.frame_set(1)
for o in members:o.location.y+=selected
# Shorten shaft/foot ties at the moved front end; rear end stays installed.
shaft=bpy.data.objects['R82_R3_Locked_Trunnion']
bare=max(v.co.z for v in shaft.data.vertices)-min(v.co.z for v in shaft.data.vertices)
old_length=bare*shaft.scale.z;shaft.scale.z=(old_length-selected)/bare;shaft.location.y+=selected/2
for o in bpy.data.objects:
 if o.name.startswith('R82_R3_Lower_Bridge_'):
  bare=max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices)
  old_length=bare*o.scale.z;o.scale.z=(old_length-selected)/bare;o.location.y+=selected/2
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
d.update({'source_parent':d['source'],'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'front_bearing_translation_y':selected,'status':'independent_refinement_candidate; '+str(len(frames))+'-pose ceramic/front-stack and peer subset clear; not full art/runtime acceptance'})
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
 for v in p.devices:v.use=v.type=='CUDA'
 s.cycles.device='GPU'
except:pass
s.cycles.samples=48;cam=s.camera;s.render.resolution_x=1000;s.render.resolution_y=1100
for name,f,loc,target,scale in [('closed',1,(-4,-7,3.65),(0,0,1.57),4.1),('open',145,(-4,-7,3.65),(0,0,1.57),4.1),('rear_connection',1,(-2,6,2.8),(0,.1,1.12),1.7)]:
 s.frame_set(f);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R82_R8_SAVED',flush=True)
