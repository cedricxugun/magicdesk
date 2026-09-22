"""R82 r3: rebuild saddle casting and real prismatic/revolute cover joints.
Source r2 and shared base are preserved. This is still an independent candidate.
"""
import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[2]
IN=R/'review/I_refinement/nautilus_reset_r82/form_r2'
OUT=R/'review/I_refinement/nautilus_reset_r82/mechanism_r3b';OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_nautilus_reset_r82_mechanism_r3b.blend'
assert not SRC.exists(),'Never overwrite a reviewed or edited source.'
d=json.loads((IN/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']))
scene=bpy.context.scene;scene.frame_set(1)
col=bpy.data.collections['R82_NEW_FORM'];root=bpy.data.objects['R82_COIL_ROOT']
ivory=bpy.data.materials['R82_Continuous_Glazed_Porcelain'];nickel=bpy.data.materials['R82_Satin_Nickel']
gold=bpy.data.materials['R82_Warm_Acoustic_Alloy'];dark=bpy.data.materials['R82_Recessed_Graphite'];red=bpy.data.materials['R82_Red_Lacquer']
def empty(n,parent=root):
 o=bpy.data.objects.new(n,None);col.objects.link(o);o.parent=parent;return o
def mesh(n,vs,fs,ma,parent=root):
 me=bpy.data.meshes.new(n+'_mesh');me.from_pydata(vs,[],fs);me.update()
 o=bpy.data.objects.new(n,me);col.objects.link(o);o.parent=parent;me.materials.append(ma)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 return o
def bevel(o,width=.005):
 mod=o.modifiers.new('Machined edge radius','BEVEL');mod.width=width;mod.segments=3;mod.limit_method='ANGLE'
 mod=o.modifiers.new('Corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True
 return o
def cyl(n,rad,length,pos,axis,ma,parent=root):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=rad,depth=length)
 o=bpy.context.object;o.name=n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=pos;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.9
 bevel(o,min(.004,rad*.12));return o
def ring(n,ro,ri,length,pos,axis,ma,parent=root):
 vs=[];fs=[];N=72
 for z,rr in [(-length/2,ro),(length/2,ro),(-length/2,ri),(length/2,ri)]:
  for j in range(N):
   a=math.tau*j/N;vs.append((rr*math.cos(a),rr*math.sin(a),z))
 for a,b in [(0,1),(1,3),(3,2),(2,0)]:
  for j in range(N):fs.append((a*N+j,a*N+(j+1)%N,b*N+(j+1)%N,b*N+j))
 o=mesh(n,vs,fs,ma,parent);o.location=pos;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
 return bevel(o,min(.0025,(ro-ri)*.20))
def bar(n,a,b,r,ma,parent=root):
 a,b=Vector(a),Vector(b);return cyl(n,r,(b-a).length,(a+b)/2,b-a,ma,parent)
def pipe(n,pts,r,ma):
 cu=bpy.data.curves.new(n+'_curve','CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=4;cu.use_fill_caps=True
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,c in zip(sp.points,pts):p.co=(*c,1)
 o=bpy.data.objects.new(n,cu);col.objects.link(o);o.parent=root;cu.materials.append(ma)
 return o
def apply_bool(obj,cutter,operation):
 bpy.context.view_layer.objects.active=obj
 mod=obj.modifiers.new('Real machined opening','BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=cutter
 # Boolean must precede edge dressing.
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)

T=4.70*math.pi;END=3.55;GROW=.205;RMAX=.94;RAD=.552;DEPTH=.61;SHIFT=Vector((0,0,0))
def frame(t):
 r=RMAX*math.exp(GROW*(t-T));a=END+t-T;rad=Vector((math.cos(a),0,math.sin(a)))
 u=max(0.,(t-(T-1.25))/1.25)
 tan=Vector((r*(GROW*math.cos(a)-math.sin(a)),-.44*3*u*u/1.25,r*(GROW*math.sin(a)+math.cos(a)))).normalized()
 cross=(rad-tan*rad.dot(tan)).normalized()
 return r,cross,tan,SHIFT+rad*r+Vector((0,-.44*u**3,0))
def point(t,u,inset=0):
 r,n,a,c=frame(t);return c+n*(max(.002,RAD*r-inset)*math.cos(u))+n.cross(a).normalized()*(max(.002,DEPTH*r-inset)*math.sin(u))
p0=d['panels'][0];obj=bpy.data.objects[p0['mesh']]
SHIFT=(obj.matrix_world@obj.data.vertices[0].co)-point(p0['ta'],.015)
# Verify independent analytical reconstruction against existing shell vertices.
errors=[]
for p in d['panels']:
 o=bpy.data.objects[p['mesh']]
 for i,j in [(0,0),(40,36),(80,72)]:
  errors.append(((o.matrix_world@o.data.vertices[i*73+j].co)-point(p['ta']+(p['tb']-p['ta'])*i/80,.015+(math.pi-.03)*j/72)).length)
assert max(errors)<1e-5,max(errors)

def surface(n,ta,tb,ua,ub,ma,inset,thick,nt,nu,parent=root):
 vs=[];fs=[]
 for layer in [0,thick]:
  for i in range(nt+1):
   for j in range(nu+1):vs.append(point(ta+(tb-ta)*i/nt,ua+(ub-ua)*j/nu,inset+layer))
 N=(nt+1)*(nu+1);s=nu+1
 for lay in [0,1]:
  for i in range(nt):
   for j in range(nu):
    a=lay*N+i*s+j;q=(a,a+s,a+s+1,a+1);fs.append(q if lay==0 else q[::-1])
 edge=list(range(s))+[i*s+nu for i in range(1,nt+1)]+[nt*s+j for j in range(nu-1,-1,-1)]+[i*s for i in range(nt-1,0,-1)]
 for j,a in enumerate(edge):
  b=edge[(j+1)%len(edge)];fs.append((a,b,b+N,a+N))
 return mesh(n,vs,fs,ma,parent)
# Denser exact samples, not a smoothing modifier that changes the coil profile.
for p in d['panels']:
 o=bpy.data.objects[p['mesh']]
 new=surface('tmp',p['ta'],p['tb'],.015,math.pi-.015,ivory,0,.018,max(128,math.ceil((p['tb']-p['ta'])/.025)),96)
 # Geometry is authored in world coordinates while the original mesh is local to P.
 for v in new.data.vertices:v.co-=Vector(p['pivot'])
 old=o.data;o.data=new.data;o.location=(0,0,0);bpy.data.objects.remove(new,do_unlink=True)
# The fixed rear skin uses the same continuous definition at finer angular spacing.
o=bpy.data.objects['R82_Fixed_Rear_Keel']
new=surface('tmp_back',.01,T,math.pi-.04,math.tau+.04,nickel,.016,.022,600,96)
o.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
rear_mat=nickel.copy();rear_mat.name='R82_R3_Rear_Satin';rear_mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.30
o.data.materials[0]=rear_mat

# Remove only generated r2 placeholders, preserving body/base/motion identities.
for o in list(col.objects):
 if o.name.startswith(('R82_Fixed_Slide_','R82_Link_','R82_Hinge_Pin_','R82_Latch_','R82_Keel_Lower_Load_Path','R82_Sculpted_Saddle_Casting','R82_Trunnion_')):
  bpy.data.objects.remove(o,do_unlink=True)

# A pair of forged U-saddle cheeks with real transverse bearing bores.
AX=Vector((0,.06,1.13))
def bezier(a,b,c,d,t):return Vector(a)*(1-t)**3+Vector(b)*3*t*(1-t)**2+Vector(c)*3*t*t*(1-t)+Vector(d)*t**3
def cheek(name,cy):
 # Clockwise XZ outline: circular head, curved descending shoulders, radiused foot.
 outline=[]
 for i in range(49):
  a=math.pi-math.pi*i/48;outline.append((.224*math.cos(a),1.13+.224*math.sin(a)))
 curve=[bezier((.224,1.13),(.215,1.02),(.34,.89),(.428,.813),i/28)for i in range(1,29)]
 outline += [(p.x,p.y)for p in curve]
 outline +=[(.435,.795),(.425,.777),(.40,.770),(-.40,.770),(-.425,.777),(-.435,.795),(-.428,.813)]
 outline +=[(-p.x,p.y)for p in reversed(curve[:-1])]
 N=len(outline);vs=[(x,cy+dy,z)for dy in [-.041,.041]for x,z in outline]
 fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]
 fs +=[(j,(j+1)%N,(j+1)%N+N,j+N)for j in range(N)]
 o=mesh(name,vs,fs,nickel)
 tool=cyl('r3_bore_tool',.166,.20,(0,cy,1.13),(0,1,0),dark)
 apply_bool(o,tool,'DIFFERENCE');bevel(o,.012)
 return o
for side in [-1,1]:
 cy=.06+side*.268
 cheek(f'R82_R3_Saddle_Cheek_{side}',cy)
 ring(f'R82_R3_Bearing_{side}',.164,.140,.084,(0,cy,1.13),(0,1,0),gold)
 ring(f'R82_R3_Seal_{side}',.159,.140,.008,(0,cy+side*.048,1.13),(0,1,0),dark)
 ring(f'R82_R3_Bearing_Shoulder_{side}',.185,.138,.018,(0,cy+side*.054,1.13),(0,1,0),nickel)
 cyl(f'R82_R3_Axle_Endcap_{side}',.132,.013,(0,cy+side*.067,1.13),(0,1,0),nickel)
 # One inset index line, avoiding another large red medallion.
 bar(f'R82_R3_Axle_Index_{side}',(-.005,cy+side*.076,1.08),(-.005,cy+side*.076,1.16),.004,red)
cyl('R82_R3_Locked_Trunnion',.137,.68,AX,(0,1,0),nickel)
# Compact lower crossmember joins the two cheeks above the original base.
for x in [-.28,.28]:bar('R82_R3_Lower_Bridge_'+str(x),(x,-.22,.804),(x,.34,.804),.037,nickel)
# Curved fitted metal attachment pads on the actual rear surface.
cast_endpoints=[]
for k,t in enumerate([T-5.0,T-3.8]):
 pad=surface(f'R82_R3_Keel_Fitted_Pad_{k}',t-.22,t+.22,4.48,4.95,nickel,-.018,.034,32,24)
 c=point(t,4.715,-.005);cast_endpoints.append(c)
 # Smooth broad forged arm from hub to fitted pad, gently curved with no straight diagonal rod.
 p0=AX+Vector((.04 if k else -.035,.18,.01))
 p1=p0+Vector((.0,.015,.16));p2=c+Vector((-.03 if k else .02,.065,-.06))
 pts=[bezier(p0,p1,p2,c,i/48)for i in range(49)]
 pipe(f'R82_R3_Forged_Keel_Arm_{k}',pts,.060 if k else .055,nickel)
 # Small machined terminal shoulder gives the cast-to-skin connection readable depth.
 n=(point(t,4.715,-.012)-point(t,4.715,.006)).normalized()
 ring(f'R82_R3_Keel_Capture_Rim_{k}',.045,.023,.014,c+n*.009,n,gold)
 cyl(f'R82_R3_Keel_Capture_Pin_{k}',.021,.028,c+n*.010,n,nickel)

joints=[];moving=[];latches=[]
for p in d['panels']:
 k=p['id'];node=bpy.data.objects[p['node']]
 P=Vector(p['pivot']);A=Vector(p['axis']).normalized();D=Vector(p['translation']);S=D.normalized();stroke=D.length
 r,rad,tan,c=frame((p['ta']+p['tb'])/2)
 span=max(.018,min(.065,r*.14));rod_r=max(.004,min(.009,r*.022))
 tube_r=rod_r*2.25;bore=rod_r+.0015;length=stroke+.055
 carriage=empty(f'R82_R3_Carriage_{k:02d}');carriage.location=P
 for side in [-1,1]:
  tip=P+A*span*side
  ring(f'R82_R3_Guide_Sleeve_{k}_{side}',tube_r,bore,length,tip-S*length/2,S,nickel)
  ring(f'R82_R3_Guide_Wiper_{k}_{side}',tube_r*1.06,rod_r+.0008,.006,tip+S*.001,S,dark)
  rod=cyl(f'R82_R3_Slider_Rod_{k}_{side}',rod_r,length, A*span*side-S*(length/2-.005),S,nickel,carriage)
  # Guide feet meet the fixed acoustic metal, with independent stepped shoulders.
  ring(f'R82_R3_Guide_Foot_{k}_{side}',tube_r*1.42,bore,.014,tip-S*(length-.009),S,gold)
 # Hollow translating crosshead and real rotating pin, with distinct materials.
 ring(f'R82_R3_Crosshead_{k:02d}',tube_r*1.25,rod_r*1.03,2*span+.018,(0,0,0),A,nickel,carriage)
 cyl(f'R82_R3_Rotating_Pin_{k:02d}',rod_r,2*span+.020,(0,0,0),A,gold,node)
 for side in [-1,1]:
  ring(f'R82_R3_Pin_Stop_{k}_{side}',rod_r*1.64,rod_r*1.02,.005,A*side*(span+.011),A,dark,node)
  tmid=(p['ta']+p['tb'])/2
  tp=min(p['tb']-.03,max(p['ta']+.03,tmid+side*.10))
  anchor=point(tp,.24,.018)
  pad=surface(f'R82_R3_Inside_Cover_Pad_{k}_{side}',tp-.045,tp+.045,.15,.32,nickel,.018,.012,12,12,node);pad.location=-P
  bar(f'R82_R3_Rotor_Ear_{k}_{side}',A*span*side,anchor-P,tube_r*.66,nickel,node)
 # Separate latch gesture precedes the panel lift.
 lp=point(p['tb']-.085,.50,-.002)
 latch=empty(f'R82_R3_Latch_Pivot_{k:02d}',node);latch.location=lp-P;latch.rotation_mode='QUATERNION'
 axis=A
 cyl(f'R82_R3_Latch_Pin_{k:02d}',max(.005,rod_r),.027,(0,0,0),axis,nickel,latch)
 handle_len=max(.028,min(.065,r*.14))
 direction=(rad-axis*rad.dot(axis)).normalized()
 bar(f'R82_R3_Enamel_Lock_Handle_{k:02d}',(0,0,0),direction*handle_len,max(.004,rod_r*.65),red,latch)
 cyl(f'R82_R3_Latch_Tip_{k:02d}',max(.005,rod_r*.8),.014,direction*handle_len,axis,nickel,latch)
 moving.append((carriage,node));latches.append((latch,axis))
 joints.append({'id':k,'carriage':carriage.name,'pivot':list(P),'axis':list(A),'slide_direction':list(S),'stroke':stroke,'guide_length':length,'rod_radius':rod_r,'bore_radius':bore,'minimum_rod_engagement':length-stroke,'crosshead_span':span,'latch':latch.name})
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
for f in range(1,301):
 scene.frame_set(f)
 for car,node in moving:
  car.location=node.location
  car.keyframe_insert('location',frame=f)
 unlock=smooth((f-8)/16) if f<270 else 1-smooth((f-270)/20)
 for latch,axis in latches:
  latch.rotation_quaternion=Quaternion(axis,.70*unlock);latch.keyframe_insert('rotation_quaternion',frame=f)
for car,_ in moving:
 for layer in car.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
d.update({'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
          'source_parent':'blender/collection/I_nautilus_reset_r82_form_r2.blend',
          'status':'independent_refinement_candidate_not_final_or_integrated','reconstruction_max_error':max(errors),
          'shape_parameters':{'T':T,'END':END,'GROW':GROW,'RMAX':RMAX,'RAD':RAD,'DEPTH':DEPTH,'SHIFT':list(SHIFT)},
          'joints':joints,'remaining':['guide foot metal seating/fasteners and latch catch detail','all-component collision sweep','interior acoustic chambers and mouth/score adaptation','whole art acceptance/runtime/effects/service']})
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100
cam=scene.camera
for name,f,loc,target,scale in [
 ('closed',1,(-4,-7,3.65),(0,0,1.57),4.1),
 ('open',145,(-4,-7,3.65),(0,0,1.57),4.1),
 ('rear_connection',1,(-2,6,2.8),(0,.10,1.12),1.7),
 ('hinge_inside',145,(2,-5,4),(0,-.10,2.05),1.9)]:
 scene.frame_set(f);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R82_R3_REFINED',flush=True)
