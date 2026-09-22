"""R82 precision follow-up: forged cheek volume, flat-face normals, fitted ports,
and a physical slide-before-turn opening. Keeps previous candidates unchanged."""
import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];IN=R/'review/I_refinement/nautilus_reset_r82/mechanism_r3b'
OUT=R/'review/I_refinement/nautilus_reset_r82/mechanism_r4';OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_nautilus_reset_r82_mechanism_r4.blend';assert not SRC.exists()
d=json.loads((IN/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']))
s=bpy.context.scene;s.frame_set(1);col=bpy.data.collections['R82_NEW_FORM'];root=bpy.data.objects['R82_COIL_ROOT']
nickel=bpy.data.materials['R82_Satin_Nickel'];gold=bpy.data.materials['R82_Warm_Acoustic_Alloy'];dark=bpy.data.materials['R82_Recessed_Graphite']
def mesh(n,vs,fs,ma):
 me=bpy.data.meshes.new(n+'_mesh');me.from_pydata(vs,[],fs);me.update()
 o=bpy.data.objects.new(n,me);col.objects.link(o);o.parent=root;me.materials.append(ma)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 return o
def cylinder(n,r,depth,p,axis,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=depth)
 o=bpy.context.object;o.name=n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=root;o.location=p;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=abs(f.normal.z)<.9
 return o
def cut(o,tool):
 bpy.context.view_layer.objects.active=o
 mod=o.modifiers.new('Actual fitted port','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(tool,do_unlink=True)
def ring(n,ro,ri,length,pos,axis,ma):
 vs=[];fs=[];N=64
 for z,rad in [(-length/2,ro),(length/2,ro),(-length/2,ri),(length/2,ri)]:
  for j in range(N):a=math.tau*j/N;vs.append((rad*math.cos(a),rad*math.sin(a),z))
 for a,b in [(0,1),(1,3),(3,2),(2,0)]:
  for j in range(N):fs.append((a*N+j,a*N+(j+1)%N,b*N+(j+1)%N,b*N+j))
 o=mesh(n,vs,fs,ma);o.location=pos;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
 for f in o.data.polygons:f.use_smooth=abs(f.normal.z)<.9
 mod=o.modifiers.new('Shoulder fillet','BEVEL');mod.width=.001;mod.segments=3
 return o
def bevel(o,w):
 mo=o.modifiers.new('Forged edge radius','BEVEL');mo.width=w;mo.segments=5;mo.limit_method='ANGLE';mo.harden_normals=True
 mo=o.modifiers.new('Machined planar normals','WEIGHTED_NORMAL');mo.keep_sharp=True
def bez(a,b,c,d,t):return Vector(a)*(1-t)**3+Vector(b)*3*t*(1-t)**2+Vector(c)*3*t*t*(1-t)+Vector(d)*t**3

# Remove the flat-plate candidate cheeks. Replace with a genuinely thicker,
# convex four-section forging; front faces remain mathematically planar.
for side in [-1,1]:
 old=bpy.data.objects[f'R82_R3_Saddle_Cheek_{side}'];bpy.data.objects.remove(old,do_unlink=True)
 cy=.06+side*.268
 outline=[]
 for i in range(49):
  a=math.pi-math.pi*i/48;outline.append((.224*math.cos(a),1.13+.224*math.sin(a)))
 curve=[bez((.224,1.13),(.215,1.02),(.34,.89),(.428,.813),i/28)for i in range(1,29)]
 outline +=[(p.x,p.y)for p in curve]+[(.435,.795),(.425,.777),(.40,.770),(-.40,.770),(-.425,.777),(-.435,.795),(-.428,.813)]
 outline +=[(-p.x,p.y)for p in reversed(curve[:-1])]
 N=len(outline);vs=[];fs=[]
 layers=[(-.088,.91),(-.082,.955),(-.064,.990),(-.035,1.),(.035,1.),(.064,.990),(.082,.955),(.088,.91)]
 for y,scale in layers:
  for x,z in outline:vs.append((x*scale,cy+y,.79+(z-.79)*scale))
 for k in range(len(layers)-1):
  for j in range(N):fs.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
 fs +=[tuple(range(N-1,-1,-1)),tuple((len(layers)-1)*N+j for j in range(N))]
 o=mesh(f'R82_R4_Forged_Saddle_{side}',vs,fs,nickel)
 cut(o,cylinder('r4_bearing_bore',.166,.30,(0,cy,1.13),(0,1,0),dark))
 for f in o.data.polygons:
  if abs(f.normal.y)>.97:f.use_smooth=False
 bevel(o,.004)
 # Extend original bearing through the thicker true bore and move its shoulders.
 b=bpy.data.objects[f'R82_R3_Bearing_{side}'];b.scale.z=.177/.084
 for suffix,off in [('Seal',.094),('Bearing_Shoulder',.101),('Axle_Endcap',.115),('Axle_Index',.124)]:
  ob=bpy.data.objects[f'R82_R3_{suffix}_{side}'];ob.location.y=cy+side*off
ax=bpy.data.objects['R82_R3_Locked_Trunnion'];ax.scale.z=.765/.68

# A flattened, gently bowed forged web replaces both cylindrical rods.
for k in [0,1]:
 ob=bpy.data.objects[f'R82_R3_Forged_Keel_Arm_{k}'];cu=ob.data
 pts=[Vector(p.co[:3])for p in cu.splines[0].points]
 bpy.data.objects.remove(ob,do_unlink=True)
 vs=[];fs=[];N=32
 for i,c in enumerate(pts):
  u=i/(len(pts)-1);tan=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
  cross=Vector((-tan.z,0,tan.x)).normalized()
  width=.048+.045*math.sin(math.pi*u)**.8
  depth=.026+.008*math.sin(math.pi*u)
  for j in range(N):
   a=math.tau*j/N;vs.append(c+cross*(width*math.cos(a))+Vector((0,depth*math.sin(a),0)))
 for i in range(len(pts)-1):
  for j in range(N):fs.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
 fs +=[tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))]
 mesh(f'R82_R4_Curved_Keel_Web_{k}',vs,fs,nickel)

# Cut the rear sheet where guide sleeves genuinely pass through. The preceding
# candidate visibly crossed the sheet with no port; these are actual bores.
back=bpy.data.objects['R82_Fixed_Rear_Keel']
ev=back.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
vs=[back.matrix_world@v.co for v in me.vertices];tris=[tuple(t.vertices)for t in me.loop_triangles]
tree=BVHTree.FromPolygons(vs,tris,all_triangles=True);ev.to_mesh_clear()
ports=[]
for j in d['joints']:
 P=Vector(j['pivot']);A=Vector(j['axis']);S=Vector(j['slide_direction']);L=j['guide_length'];span=j['crosshead_span'];ro=j['rod_radius']*2.25
 for side in [-1,1]:
  tip=P+A*span*side
  pos,normal,index,distance=tree.ray_cast(tip-S*(L+.2),S,L+.4)
  if pos is None:continue
  cut(back,cylinder('r4_port_tool',ro+.0012,L+.45,tip-S*L*.5,S,dark))
  ring(f'R82_R4_Rear_Guide_Flange_{j["id"]}_{side}',ro*1.40,ro+.0014,.009,pos-S*.004,S,gold)
  ports.append({'id':j['id'],'side':side,'entry':list(pos),'bore_radius':ro+.0012})
# Synchronous stages: unlatch, translate fully out of seating, then rotate.
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
for f in range(1,301):
 s.frame_set(f)
 for p,j in zip(d['panels'],d['joints']):
  idx=p['id'];t=(f-25-(idx-1)*1.5)/82 if f<150 else 1-(f-174-(6-idx)*1.5)/82
  t=max(0,min(1,t));lift=smooth(t/.30);turn=smooth((t-.30)/.70)
  obj=bpy.data.objects[p['node']];obj.location=Vector(p['pivot'])+Vector(p['translation'])*lift
  obj.rotation_quaternion=Quaternion(Vector(p['axis']),p['angle']*turn)
  obj.keyframe_insert('location',frame=f);obj.keyframe_insert('rotation_quaternion',frame=f)
  car=bpy.data.objects[j['carriage']];car.location=obj.location;car.keyframe_insert('location',frame=f)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
d.update({'source_parent':d['source'],'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'rear_ports':ports,
 'opening':'unlock first, 30% duration pure translation, 70% duration rotation; all six; inverse path closing',
 'remaining':['latch catch and guide foot seating detail','all-component finite and continuous collision checks','interior acoustic totality and mouth/score/music adaptation','materials/whole art review/runtime/service/effects']})
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for v in pref.devices:v.use=v.type=='CUDA'
 s.cycles.device='GPU'
except:pass
s.cycles.samples=48;s.render.resolution_x=1000;s.render.resolution_y=1100
cam=s.camera
for name,frame_num,loc,target,scale in [('closed',1,(-4,-7,3.65),(0,0,1.57),4.1),('open',145,(-4,-7,3.65),(0,0,1.57),4.1),('rear_connection',1,(-2,6,2.8),(0,.1,1.12),1.7),('guide_detail',145,(-3,-5,3.8),(-.62,-.24,2.15),1.2)]:
 s.frame_set(frame_num);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R82_R4_REFINED',flush=True)
