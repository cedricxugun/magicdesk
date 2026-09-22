"""R82 r5: put the slide/hinge underneath the broad cover surface instead of
through its narrow outer edge. Preserve all closed ceramic world geometry."""
import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];IN=R/'review/I_refinement/nautilus_reset_r82/mechanism_r4'
OUT=R/'review/I_refinement/nautilus_reset_r82/mechanism_r5';OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_nautilus_reset_r82_mechanism_r5.blend';assert not SRC.exists()
d=json.loads((IN/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']))
s=bpy.context.scene;s.frame_set(1);col=bpy.data.collections['R82_NEW_FORM'];root=bpy.data.objects['R82_COIL_ROOT']
nickel=bpy.data.materials['R82_Satin_Nickel'];gold=bpy.data.materials['R82_Warm_Acoustic_Alloy'];dark=bpy.data.materials['R82_Recessed_Graphite']
def mesh(n,vs,fs,ma,parent=root):
 me=bpy.data.meshes.new(n+'_mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);col.objects.link(o);o.parent=parent;me.materials.append(ma)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 return o
def cylinder(n,r,length,center,axis,ma,parent=root):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=length);o=bpy.context.object;o.name=n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=center;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=abs(f.normal.z)<.9
 return o
def bar(n,a,b,r,ma,parent=root):
 a,b=Vector(a),Vector(b);return cylinder(n,r,(b-a).length,(a+b)/2,b-a,ma,parent)
def cut(o,tool):
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Slide path port','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
PARS=d['shape_parameters'];T=PARS['T'];END=PARS['END'];GROW=PARS['GROW'];RMAX=PARS['RMAX'];RAD=PARS['RAD'];DEPTH=PARS['DEPTH'];SHIFT=Vector(PARS['SHIFT'])
def frame(t):
 r=RMAX*math.exp(GROW*(t-T));a=END+t-T;n=Vector((math.cos(a),0,math.sin(a)));u=max(0.,(t-(T-1.25))/1.25)
 tang=Vector((r*(GROW*math.cos(a)-math.sin(a)),-.44*3*u*u/1.25,r*(GROW*math.sin(a)+math.cos(a)))).normalized()
 radial=(n-tang*n.dot(tang)).normalized()
 return r,radial,tang,SHIFT+n*r+Vector((0,-.44*u**3,0))
def point(t,u,inset=0):
 r,n,a,c=frame(t);return c+n*(max(.002,RAD*r-inset)*math.cos(u))+n.cross(a).normalized()*(max(.002,DEPTH*r-inset)*math.sin(u))
# Restore the unperforated r3b rear skin before drilling only current paths.
with bpy.data.libraries.load(str(R/'blender/collection/I_nautilus_reset_r82_mechanism_r3b.blend'),link=False)as(src,dst):dst.objects=['R82_Fixed_Rear_Keel']
ref=dst.objects[0];bpy.data.objects['R82_Fixed_Rear_Keel'].data=ref.data.copy();bpy.data.objects.remove(ref,do_unlink=True)
for o in list(col.objects):
 if o.name.startswith(('R82_R4_Rear_Guide_Flange','R82_R3_Rotor_Ear_','R82_R3_Inside_Cover_Pad_')):bpy.data.objects.remove(o,do_unlink=True)
closed_witnesses={}
for p in d['panels']:
 o=bpy.data.objects[p['mesh']];closed_witnesses[p['id']]=[o.matrix_world@o.data.vertices[i].co for i in [0,len(o.data.vertices)//3,len(o.data.vertices)//2,-1]]
for p,j in zip(d['panels'],d['joints']):
 idx=p['id'];tm=(p['ta']+p['tb'])/2
 old=Vector(p['pivot']);new=point(tm,math.pi/2,.018+j['rod_radius']*2.82+.024)
 delta=new-old;node=bpy.data.objects[p['node']];A=Vector(p['axis']);S=Vector(j['slide_direction'])
 for child in list(node.children):
  # Axis hardware belongs to the relocated bearing. Cosmetic shell/edge/latch
  # retain their exact assembled world positions.
  if not child.name.startswith(('R82_R3_Rotating_Pin_','R82_R3_Pin_Stop_')):child.location-=delta
 node.location=new
 for side in [-1,1]:
  for stem in ['Guide_Sleeve','Guide_Wiper','Guide_Foot']:
   bpy.data.objects[f'R82_R3_{stem}_{idx}_{side}'].location+=delta
 car=bpy.data.objects[j['carriage']];car.location=new
 # Longer central lift prevents the small curled cap grazing the next whorl.
 D=Vector(p['translation'])
 if idx==1:D=Vector((0,-.17,0))
 p['pivot']=list(new);p['translation']=list(D);j['pivot']=list(new)
 j['stroke']=D.length;j['slide_direction']=list(D.normalized())
 # Central direction changes minimally: align actual sleeve/rod geometry with it.
 if idx==1:
  newS=D.normalized();old_length=j['guide_length'];j['guide_length']=D.length+.055
  for side in [-1,1]:
   tip=new+A*j['crosshead_span']*side
   sleeve=bpy.data.objects[f'R82_R3_Guide_Sleeve_{idx}_{side}'];sleeve.location=tip-newS*j['guide_length']/2;sleeve.scale.z=j['guide_length']/old_length
   sleeve.rotation_quaternion=newS.to_track_quat('Z','Y')
   for stem,z in [('Guide_Wiper',.001),('Guide_Foot',-(j['guide_length']-.009))]:
    o=bpy.data.objects[f'R82_R3_{stem}_{idx}_{side}'];o.location=tip+newS*z;o.rotation_quaternion=newS.to_track_quat('Z','Y')
   rod=bpy.data.objects[f'R82_R3_Slider_Rod_{idx}_{side}'];rod.location=A*j['crosshead_span']*side-newS*(j['guide_length']/2-.005);rod.scale.z=j['guide_length']/old_length;rod.rotation_quaternion=newS.to_track_quat('Z','Y')
 for side in [-1,1]:
  tp=tm+side*.10;u=math.pi/2
  # Precisely fitted inner mounting patch, directly from the true ceramic inner surface.
  vs=[];fs=[];N=12
  for dep in [.018,.030]:
   for a in range(N+1):
    for b in range(N+1):vs.append(point(tp-.040+.08*a/N,u-.13+.26*b/N,dep)-new)
  count=(N+1)**2
  for lay in [0,1]:
   for a in range(N):
    for b in range(N):
     c=lay*count+a*(N+1)+b;q=(c,c+N+1,c+N+2,c+1);fs.append(q if lay==0 else q[::-1])
  edge=list(range(N+1))+[a*(N+1)+N for a in range(1,N+1)]+[N*(N+1)+b for b in range(N-1,-1,-1)]+[a*(N+1)for a in range(N-1,0,-1)]
  for k,a in enumerate(edge):
   b=edge[(k+1)%len(edge)];fs.append((a,b,b+count,a+count))
  mesh(f'R82_R5_Cover_Pad_{idx}_{side}',vs,fs,nickel,node)
  anchor=point(tp,u,.027)-new
  bar(f'R82_R5_Short_Rotor_Ear_{idx}_{side}',A*j['crosshead_span']*side,anchor,j['rod_radius']*1.25,nickel,node)
# Clearance holes are only added where an actual guide path crosses fixed metal.
ports=[]
for name in ['R82_Fixed_Rear_Keel','R82_Acoustic_Chamber_Liner']:
 o=bpy.data.objects[name];bpy.context.view_layer.update()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in me.vertices],[tuple(t.vertices)for t in me.loop_triangles],all_triangles=True);ev.to_mesh_clear()
 for j in d['joints']:
  P=Vector(j['pivot']);A=Vector(j['axis']);S=Vector(j['slide_direction']);L=j['guide_length']
  for side in [-1,1]:
   tip=P+A*j['crosshead_span']*side;start=tip-S*(L+.05);ray_length=L+j['stroke']+.10
   hit=tree.ray_cast(start,S,ray_length)
   if hit[0] is None:continue
   ro=j['rod_radius']*2.25+.002
   cut(o,cylinder('r5_slide_port',ro,ray_length,start+S*ray_length/2,S,dark))
   ports.append({'body':name,'id':j['id'],'side':side,'radius':ro,'hit':list(hit[0])})
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
for f in range(1,301):
 s.frame_set(f)
 for p,j in zip(d['panels'],d['joints']):
  idx=p['id'];t=(f-25-(idx-1)*1.5)/82 if f<150 else 1-(f-174-(6-idx)*1.5)/82;t=max(0,min(1,t))
  lift=smooth(t/.30);turn=smooth((t-.30)/.70)
  obj=bpy.data.objects[p['node']];obj.location=Vector(p['pivot'])+Vector(p['translation'])*lift;obj.rotation_quaternion=Quaternion(Vector(p['axis']),p['angle']*turn)
  obj.keyframe_insert('location',frame=f);obj.keyframe_insert('rotation_quaternion',frame=f)
  car=bpy.data.objects[j['carriage']];car.location=obj.location;car.keyframe_insert('location',frame=f)
s.frame_set(1);bpy.context.view_layer.update()
error=0
for p in d['panels']:
 o=bpy.data.objects[p['mesh']]
 actual=[o.matrix_world@o.data.vertices[i].co for i in [0,len(o.data.vertices)//3,len(o.data.vertices)//2,-1]]
 error=max(error,max((a-b).length for a,b in zip(actual,closed_witnesses[p['id']])))
assert error<1e-5,error
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
d.update({'source_parent':d['source'],'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'current_ports':ports,'closed_shape_witness_error':error,'status':'independent_under_cover_joint_candidate_pending_checks'})
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
print('R82_R5_SAVED',flush=True)
