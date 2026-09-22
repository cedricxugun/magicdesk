"""R82 r4 saved-file verification. Reports every scoped intersection, no blanket pass."""
import bpy,bmesh,json,math,hashlib,sys,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[0] if args else 'mechanism_r4'
assert variant in ['mechanism_r4','mechanism_r5','mechanism_r6','mechanism_r7','mechanism_r8','mechanism_r9']
OUT=R/'review/I_refinement/nautilus_reset_r82'/variant
d=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));s=bpy.context.scene
def geo(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 vs=[o.matrix_world@v.co for v in me.vertices];fs=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear()
 lo=Vector(tuple(min(v[k]for v in vs)for k in range(3)));hi=Vector(tuple(max(v[k]for v in vs)for k in range(3)))
 return BVHTree.FromPolygons(vs,fs,all_triangles=True),lo,hi
def overlaps(a,b):return all(a[1][k]<=b[2][k] and b[1][k]<=a[2][k]for k in range(3))
panels=[bpy.data.objects[p['mesh']]for p in d['panels']]
# Covers against new stationary machinery and translating crossheads/rods.
# Own fitted underside pads/rotor ears are intentional attachment contacts and are
# not certified by this clearance subset.
parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith((
 'R82_R3_Guide_','R82_R3_Slider_Rod_','R82_R3_Crosshead_',
 'R82_R4_Forged_Saddle_','R82_R4_Curved_Keel_Web_','R82_R3_Locked_Trunnion',
 'R82_R3_Bearing_','R82_R3_Seal_','R82_R3_Axle_','R82_R4_Rear_Guide_'))]
rows=[];contacts=[];joints=[]
for frame in [1,24,34,44,53,67,85,115,145,195,230,260,300]:
 s.frame_set(frame);bpy.context.view_layer.update()
 caches={o.name:geo(o)for o in panels+parts}
 for i,a in enumerate(panels):
  for b in panels[i+1:]+parts:
   ca,cb=caches[a.name],caches[b.name]
   if overlaps(ca,cb):
    hit=ca[0].overlap(cb[0])
    if hit:contacts.append({'frame':frame,'a':a.name,'b':b.name,'pairs':len(hit)})
 for j in d['joints']:
  car=bpy.data.objects[j['carriage']]
  P=Vector(j['pivot']);S=Vector(j['slide_direction']);dis=car.matrix_world.translation-P
  axial=dis.dot(S);off=(dis-S*axial).length
  joints.append({'frame':frame,'id':j['id'],'off_axis':off,'engagement':j['guide_length']-axial})
 print('R4_CHECK_FRAME',frame,flush=True)
for p in d['panels']:
 obj=bpy.data.objects[p['node']]
 s.frame_set(1);a=obj.matrix_world.copy()
 s.frame_set(145);b=obj.matrix_world.copy()
 s.frame_set(300);c=obj.matrix_world.copy()
 rows.append({'id':p['id'],'displacement':(b.translation-a.translation).length,'angle':math.degrees(a.to_quaternion().rotation_difference(b.to_quaternion()).angle),'return_error':max(abs(c[i][j]-a[i][j])for i in range(4)for j in range(4))})
phase_errors=[]
for f in range(1,301):
 s.frame_set(f)
 for p in d['panels']:
  o=bpy.data.objects[p['node']];full=Vector(p['translation']).length
  advance=(o.location-Vector(p['pivot'])).length/full
  if abs(o.rotation_quaternion.angle)>.0001 and advance<.999:phase_errors.append({'frame':f,'id':p['id'],'slide_fraction':advance})
out={'source':d['source'],'sha256':hashlib.sha256((R/d['source']).read_bytes()).hexdigest(),'scope':'13 finite poses, ceramic against ceramic and listed guide/saddle parts. Not whole model, source self-intersection, continuous collision or manufacturing acceptance.','panels':rows,'contacts':contacts,'guide_off_axis_max':max(r['off_axis']for r in joints),'guide_engagement_min':min(r['engagement']for r in joints),'phase_errors':phase_errors,'full_art_or_runtime_pass':False}
(OUT/'mechanism_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'source':out['source'],'contacts_by_frame':dict(collections.Counter(x['frame']for x in contacts)),'phase_errors':len(phase_errors),'guide_engagement_min':out['guide_engagement_min']}),flush=True)
