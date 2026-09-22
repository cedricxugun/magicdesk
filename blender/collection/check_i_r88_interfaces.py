"""Test the actual manufactured brackets against moving linear hardware,
and classify only explicit flat bolt/foot seats as intentional contact."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[0] if args else 'built_r2';assert variant in ['built_r1','built_r2','built_r3','built_r4']
OUT=R/'review/I_refinement/nautilus_reset_r82/back_hardware_r88'/variant;s=json.loads((OUT/'build.json').read_text());assert hashlib.sha256((R/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
def geo(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@q.co for q in me.vertices];t=[tuple(x.vertices)for x in me.loop_triangles];ev.to_mesh_clear()
 return BVHTree.FromPolygons(v,t,all_triangles=True),v,t,[min(x[k]for x in v)for k in range(3)],[max(x[k]for x in v)for k in range(3)]
def hit(a,b):
 if any(a[4][k]<b[3][k]or b[4][k]<a[3][k]for k in range(3)):return []
 return a[0].overlap(b[0])
names={name for row in s['forged_supports']for name in [row['support'],row['collar'],row.get('bearing'),row.get('end_cap'),*row['fasteners']]if name}
fixed={name:geo(bpy.data.objects[name])for name in names}
moving=[o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith(('I85_Rod_','I85_Crosshead_','I85_HingePin_','I85_RotorStop_'))]
motion_contacts=[]
poses=[1]+list(range(85,176,3))+[205,260,324,430]
for f in poses:
 scene.frame_set(f);bpy.context.view_layer.update()
 for ob in moving:
  g=geo(ob)
  for name,fg in fixed.items():
   n=len(hit(g,fg))
   if n:motion_contacts.append({'frame':f,'moving':ob.name,'fixed':name,'triangle_pairs':n})
 print('R88_MOVING_CLEARANCE',f,len(motion_contacts),flush=True)
scene.frame_set(1);bpy.context.view_layer.update();rear=geo(bpy.data.objects['R82_Fixed_Rear_Keel']);static_contacts=[];seats=[];seat_gaps=[]
for row in s['forged_supports']:
 bracket=row['support'];bg=fixed[bracket]
 for name in {bracket,row['collar'],row.get('bearing'),row.get('end_cap'),*row['fasteners']}-{None}:
  g=fixed[name];pairs=hit(g,rear)
  if pairs:static_contacts.append({'a':name,'b':'R82_Fixed_Rear_Keel','triangle_pairs':len(pairs)})
 for bolt in row['fasteners']:
  ob=bpy.data.objects[bolt];inv=ob.matrix_world.inverted();direction=(ob.matrix_world.to_3x3()@Vector((0,0,-1))).normalized();gaps=[]
  for i in range(12):
   a=math.tau*i/12;origin=ob.matrix_world@Vector((.0028*math.cos(a),.0028*math.sin(a),.002));point,normal,tri,distance=bg[0].ray_cast(origin,direction,.025)
   gaps.append(None if point is None else -.002-(inv@point).z)
  seat_gaps.append({'bolt':bolt,'radial_samples':12,'gaps':gaps})
  g=fixed[bolt];pairs=hit(g,bg)
  if not pairs:continue
  inv=bpy.data.objects[bolt].matrix_world.inverted();za=[(inv@g[1][i]).z for pair in pairs for i in g[2][pair[0]]];zb=[(inv@bg[1][i]).z for pair in pairs for i in bg[2][pair[1]]]
  record={'a':bolt,'b':bracket,'triangle_pairs':len(pairs),'bolt_min_z':min(za),'foot_max_z':max(zb)}
  if min(za)>=-.002-2e-5 and max(zb)<=-.002+2e-5:seats.append(record)
  else:static_contacts.append(record)
 for name in [row['guide'],row.get('bearing')]:
  if name:
   pairs=hit(bg,geo(bpy.data.objects[name]))
   if pairs:static_contacts.append({'a':bracket,'b':name,'triangle_pairs':len(pairs)})
 if row.get('end_cap'):
  cap=row['end_cap'];g=fixed[cap];guide=geo(bpy.data.objects[row['guide']]);pairs=hit(g,guide)
  if pairs:
   inv=bpy.data.objects[cap].matrix_world.inverted();za=[(inv@g[1][i]).z for pair in pairs for i in g[2][pair[0]]];zb=[(inv@guide[1][i]).z for pair in pairs for i in guide[2][pair[1]]]
   record={'a':cap,'b':row['guide'],'triangle_pairs':len(pairs),'cap_min_z':min(za),'guide_max_z':max(zb)}
   if min(za)>=-.002-2e-5 and max(zb)<=-.002+2e-5:seats.append(record)
   else:static_contacts.append(record)
gaps_ok=all(g is not None and abs(g)<2e-5 for row in seat_gaps for g in row['gaps'])
report={'source_sha256':s['source_sha256'],'poses':poses,'moving_parts':len(moving),'fixed_parts':len(names),'motion_contacts':motion_contacts,'static_contacts':static_contacts,'flat_bolt_seating':seats,'bolt_floor_gap_samples':seat_gaps,'seat_gap_check':gaps_ok,'subset_clear':not motion_contacts and not static_contacts and gaps_ok,'scope':'Actual new fixed brackets/bearings/fasteners vs all named outer-hinge rods/crossheads/pins/stops at 36 source poses, plus static rear-skin, own-guide/bearing and explicit bolt/foot-seat checks. Only matching head-bottom half-spaces permit a flat seat; 12 annular rays per bolt verify the actual counterbore floor. Not whole assembly/self-intersection/continuous motion or art acceptance.'}
(OUT/'interface_check.json').write_text(json.dumps(report,indent=2)+'\n');print('R88_INTERFACE_DONE',len(motion_contacts),len(static_contacts),flush=True)
