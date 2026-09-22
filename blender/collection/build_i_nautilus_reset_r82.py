"""R82 independent growing-coil form prototype. Not the final I module.
Old sources and registry are read-only. Real shared base is reused.
"""
import bpy,bmesh,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[2]
OUT=R/'review/I_refinement/nautilus_reset_r82/form_r2'
OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_nautilus_reset_r82_form_r2.blend'
assert not SRC.exists(), 'Preserve existing editable source; create a new named iteration.'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
# Import the actual shared base rather than rebuilding a generated pedestal.
bpy.ops.import_scene.gltf(filepath=str(R/'app/assets/helios_model.glb'))
base=bpy.data.objects['BASE_FIXED']
keep=set([base]+list(base.children_recursive))
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
base.name='BASE_FIXED'
col=bpy.data.collections.new('R82_NEW_FORM');scene.collection.children.link(col)
def mat(n,c,metal=0,rough=.2,coat=0):
 m=bpy.data.materials.new(n);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*c,1)
 p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.10
 return m
ivory=mat('R82_Continuous_Glazed_Porcelain',(.78,.735,.64),0,.18,.5)
nickel=mat('R82_Satin_Nickel',(.54,.52,.47),.94,.23)
gold=mat('R82_Warm_Acoustic_Alloy',(.47,.28,.105),.88,.27)
dark=mat('R82_Recessed_Graphite',(.025,.028,.031),.66,.32)
red=mat('R82_Red_Lacquer',(.25,.009,.004),.22,.19,.45)
def empty(n,parent=None):
 o=bpy.data.objects.new(n,None);col.objects.link(o);o.parent=parent;return o
root=empty('R82_COIL_ROOT')
def mesh(n,vs,fs,ma,parent=root):
 me=bpy.data.meshes.new(n+'_mesh');me.from_pydata(vs,[],fs);me.update()
 o=bpy.data.objects.new(n,me);col.objects.link(o);o.parent=parent;me.materials.append(ma)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 return o
def pipe(n,pts,r,ma,parent=root):
 cu=bpy.data.curves.new(n+'_curve','CURVE');cu.dimensions='3D';cu.resolution_u=1
 cu.bevel_depth=r;cu.bevel_resolution=3;cu.use_fill_caps=True
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(n,cu);col.objects.link(o);cu.materials.append(ma);o.parent=parent
 return o
def cyl(n,r,depth,loc,axis,ma,parent=root):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=depth)
 o=bpy.context.object;o.name=n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=loc
 o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
 o.data.materials.append(ma)
 mod=o.modifiers.new('Machined edge radius','BEVEL');mod.width=min(.006,r*.08);mod.segments=3
 mod=o.modifiers.new('Cylinder corner normals','WEIGHTED_NORMAL')
 for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.99
 return o

# The shell is a growing swept volume, not a twist applied to an ellipsoid.
# At one full turn, successive radial sections almost meet: b controls growth.
T=4.70*math.pi;END=3.55;GROW=.205;RMAX=.94;RAD=.552;DEPTH=.61
SHIFT=Vector((.30,0,1.9))
def frame(t):
 r=RMAX*math.exp(GROW*(t-T));a=END+t-T
 radial=Vector((math.cos(a),0,math.sin(a)))
 curl=max(0.,(t-(T-1.25))/1.25)
 dy=-.44*3*curl*curl/1.25
 tangent=Vector((r*(GROW*math.cos(a)-math.sin(a)),dy,r*(GROW*math.sin(a)+math.cos(a)))).normalized()
 cross_radial=(radial-tangent*radial.dot(tangent)).normalized()
 # Terminal turn curls toward the reader continuously; no separate round tube.
 return r,cross_radial,tangent,SHIFT+radial*r+Vector((0,-.44*curl**3,0))
def point(t,u,inset=0):
 r,radial,tangent,c=frame(t)
 cross_depth=radial.cross(tangent).normalized()
 return c+radial*(max(.002,RAD*r-inset)*math.cos(u))+cross_depth*(max(.002,DEPTH*r-inset)*math.sin(u))
raw=[point(T*i/400,math.tau*j/96)for i in range(401)for j in range(96)]
SHIFT.z+=1.02-min(p.z for p in raw)
raw=[point(T*i/400,math.tau*j/96)for i in range(401)for j in range(96)]
cx=(max(p.x for p in raw)+min(p.x for p in raw))/2
SHIFT.x-=cx
def skin(n,ta,tb,ua,ub,ma,inset=0,thick=.018,nt=72,nu=64,parent=root):
 vs=[];fs=[]
 for layer in [0,thick]:
  for i in range(nt+1):
   for j in range(nu+1):vs.append(point(ta+(tb-ta)*i/nt,ua+(ub-ua)*j/nu,inset+layer))
 s=nu+1;N=(nt+1)*s
 for lay in [0,1]:
  for i in range(nt):
   for j in range(nu):
    a=lay*N+i*s+j;q=(a,a+s,a+s+1,a+1);fs.append(q if lay==0 else q[::-1])
 edge=list(range(s))+[i*s+nu for i in range(1,nt+1)]+[nt*s+j for j in range(nu-1,-1,-1)]+[i*s for i in range(nt-1,0,-1)]
 for j,a in enumerate(edge):
  b=edge[(j+1)%len(edge)];fs.append((a,b,b+N,a+N))
 o=mesh(n,vs,fs,ma,parent)
 # Broad surface already smooth from analytic sections; only boundary fillets.
 be=o.modifiers.new('Porcelain real edge radius','BEVEL');be.width=.0035;be.segments=3;be.limit_method='ANGLE';be.angle_limit=.45
 return o

# True metal fixed back and inset acoustic liner. No disguised static ceramic.
skin('R82_Fixed_Rear_Keel',.01,T,math.pi-.04,math.tau+.04,nickel,inset=.016,thick=.022,nt=256,nu=64)
skin('R82_Acoustic_Chamber_Liner',.01,T,.06,math.pi-.06,gold,inset=.042,thick=.012,nt=256,nu=64)
# A slim solid inner curl termination, recessed; no red fan hub.
r,n,t,c=frame(.015)
cyl('R82_Inner_Curl_Termination',r*.46,.025,c,(0,1,0),nickel)

# Six graduated covers, each with actual nonzero opening.
breaks=[.01,T-6.88,T-4.92,T-3.52,T-2.32,T-1.17,T]
panels=[];links=[]
for k,(ta,tb) in enumerate(zip(breaks,breaks[1:]),1):
 ta+=.010;tb-=.010;tm=(ta+tb)/2
 r,rad,tan,c=frame(tm)
 pivot=point(tm,.06,inset=.024)
 node=empty(f'R82_Panel_{k:02d}_Motion');node.location=pivot;node.rotation_mode='QUATERNION'
 o=skin(f'R82_Porcelain_{k:02d}',ta,tb,.015,math.pi-.015,ivory,nt=80,nu=72)
 # Parent without altering the analytic world coordinates.
 o.parent=node;o.matrix_parent_inverse=node.matrix_world.inverted()
 bpy.context.view_layer.update()
 o.matrix_parent_inverse.identity();o.location=-pivot
 for end_t,label in [(ta,'Inboard'),(tb,'Outboard')]:
  pts=[point(end_t,.018+(math.pi-.036)*j/90,inset=.008)for j in range(91)]
  p=pipe(f'R82_Rolled_Edge_{k:02d}_{label}',pts,.006,nickel,node);p.location=-pivot
 # Long slim joint lip, not radial fan spokes.
 for u,label in [(.02,'Outer'),(math.pi-.02,'Inner')]:
  p=pipe(f'R82_Seal_{k:02d}_{label}',[point(ta+(tb-ta)*j/120,u,inset=.015)for j in range(121)],.0045,dark,node);p.location=-pivot
 # Twin small hinge/slide stations. Connecting rods are animated endpoint-to-endpoint.
 for h,dt in enumerate([-.12,.12]):
  tp=min(tb-.05,max(ta+.05,tm+dt));rr,rd,ax,cc=frame(tp)
  fixed=point(tp,.18,inset=.025)
  socket=cyl(f'R82_Fixed_Slide_{k}_{h}',max(.011,rr*.043),.052,fixed,(0,1,0),nickel)
  moving=point(tp,.40,inset=.021)
  rod=cyl(f'R82_Link_{k}_{h}',max(.007,rr*.018),1,(0,0,0),(0,0,1),gold)
  links.append((rod,fixed,moving-pivot,node))
  bearing=cyl(f'R82_Hinge_Pin_{k}_{h}',max(.013,rr*.05),.038,moving,ax,nickel,node)
  bearing.location=moving-pivot
 # One restrained inset latch per cover.
 latch=cyl(f'R82_Latch_{k:02d}',max(.012,r*.028),.042,point(tb-.10,.54),tan,red,node)
 latch.location=point(tb-.10,.54)-pivot
 panels.append(dict(id=k,node=node.name,mesh=o.name,pivot=list(pivot),axis=list(tan),
                    translation=[float(rad.x*.032),-(.070+r*.115),float(rad.z*.032)],
                    angle=math.radians(17+5*(1-r/RMAX)),ta=ta,tb=tb))
# Inset curved chamber ribs establish a true coil, with graduated subdivisions.
for j in range(20):
 t=.10+(T-.16)*j/19
 r,rad,tt,c=frame(t)
 pipe(f'R82_Acoustic_Rib_{j:02d}',[point(t,.08+(math.pi-.16)*k/72,inset=.030)for k in range(73)],.0055,nickel)
# Continuous short terminal lip, built from the same sections as the growing body.
pipe('R82_Tangential_Aperture_Rolled_Lip',[point(T,math.tau*k/160,inset=.014)for k in range(161)],.016,nickel)
skin('R82_Aperture_Inner_Return',T-.18,T,0,math.tau,dark,inset=.060,thick=.014,nt=22,nu=96)
# Real formed saddle. Lower body transfers to a low horizontal bearing and plinth.
# A swept elliptical casting replaces flat A-frame plates.
def loft(n,rows,ma):
 vs=[];fs=[];N=96
 for z,xr,yr in rows:
  for j in range(N):
   a=math.tau*j/N;vs.append((xr*math.cos(a),yr*math.sin(a)+.06,z))
 for i in range(len(rows)-1):
  for j in range(N):fs.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
 fs +=[tuple(range(N-1,-1,-1)),tuple((len(rows)-1)*N+j for j in range(N))]
 return mesh(n,vs,fs,ma)
rows=[]
for i in range(33):
 u=i/32
 # C2 smooth shoulder across a solid compact load-bearing casting.
 s=u*u*u*(u*(u*6-15)+10)
 rows.append((.708+.46*u,.46-.13*s+.10*math.sin(math.pi*u),.31-.075*s))
loft('R82_Sculpted_Saddle_Casting',rows,nickel)
cyl('R82_Base_Locating_Flange',.51,.046,(0,.06,.716),(0,0,1),nickel)
cyl('R82_Trunnion_Continuous_Shaft',.17,.72,(0,.06,1.09),(0,1,0),nickel)
for s in [-1,1]:
 cyl(f'R82_Trunnion_Shoulder_{s}',.192,.046,(0,.06+s*.33,1.09),(0,1,0),dark)
 cyl(f'R82_Trunnion_Cap_{s}',.165,.031,(0,.06+s*.36,1.09),(0,1,0),nickel)
 cyl(f'R82_Trunnion_Inlay_{s}',.024,.034,(0,.06+s*.38,1.09),(0,1,0),red)
# The rear keel passes into this cast upper cradle; ceramic must clear it.
pipe('R82_Keel_Lower_Load_Path',[Vector((0,.23,.98)),Vector((.08,.30,1.12)),Vector((.18,.32,1.25)),point(T-4.5,math.pi*1.50,inset=.012)],.082,nickel)

def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
def progress(f,index):
 # Hold / unlock and open / stable hold / close along identical spatial route.
 start=25+(index-1)*1.5
 if f<=150:return smooth((f-start)/82)
 return 1-smooth((f-174-(6-index)*1.5)/82)
def pose(f):
 for p in panels:
  o=bpy.data.objects[p['node']];u=progress(f,p['id']);v=smooth(u)
  o.location=Vector(p['pivot'])+Vector(p['translation'])*u
  o.rotation_quaternion=Quaternion(Vector(p['axis']),p['angle']*v)
 bpy.context.view_layer.update()
 for rod,a,b,node in links:
  end=node.matrix_world@b;vec=end-a;rod.location=(a+end)/2
  rod.rotation_quaternion=vec.to_track_quat('Z','Y');rod.scale.z=vec.length
 for p in panels:
  o=bpy.data.objects[p['node']]
  for prop in ['location','rotation_quaternion']:o.keyframe_insert(prop,frame=f)
 for rod,*_ in links:
  for prop in ['location','rotation_quaternion','scale']:rod.keyframe_insert(prop,frame=f)
scene.frame_start=1;scene.frame_end=300;scene.render.fps=30
for f in range(1,301):pose(f)
for o in list(bpy.data.objects):
 if o.animation_data and o.animation_data.action:
  ac=o.animation_data.action
  for layer in ac.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(1)
# Studio reflection cards provide true broad highlights; no bump or noise on ceramic.
scene.world=bpy.data.worlds.new('R82_Studio_World');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.17,.20,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.28
def area(n,loc,target,power,color,size,size_y):
 data=bpy.data.lights.new(n,'AREA');data.energy=power;data.color=color;data.shape='RECTANGLE';data.size=size;data.size_y=size_y
 o=bpy.data.objects.new(n,data);scene.collection.objects.link(o);o.location=loc
 o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('R82_Long_Key',(-3,-4,5),(0,0,1.8),700,(1,.88,.74),4,1.6)
area('R82_Cool_Fill',(3,-2,3.6),(0,0,1.7),500,(.75,.85,1),3,1)
area('R82_Rim',(1.5,3,4.8),(0,0,1.9),950,(1,.92,.79),3,2)
area('R82_Front_Card',(-.5,-5,2),(0,0,1.8),150,(1,1,1),1.4,4)
ground=mat('R82_Studio_Floor',(.032,.027,.023),.1,.34)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.009));floor=bpy.context.object;floor.name='R82_Studio_Ground';floor.data.materials.append(ground)
camdata=bpy.data.cameras.new('R82_Review_Camera');cam=bpy.data.objects.new('R82_Review_Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=4.1
def camera(loc,target=(0,0,1.57)):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
camera((-4,-7,3.65))
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='CUDA'
 scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.render.image_settings.color_mode='RGBA'
scene.frame_set(1)
for a in bpy.context.screen.areas if bpy.context.screen else []:
 if a.type=='VIEW_3D':
  a.spaces.active.shading.type='MATERIAL'
  a.spaces.active.overlay.show_overlays=False
  a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(SRC))
report={'source':str(SRC.relative_to(R)).replace('\\','/'),'status':'isolated_shape_motion_prototype_not_final_or_integrated',
        'panels':panels,'base_source':'app/assets/helios_model.glb',
        'not_yet_done':['matching final art','full joint topology and collision sweep','aperture optics and score/music adaptation','Godot runtime and final material match','full service/explosion and effects']}
(OUT/'build.json').write_text(json.dumps(report,indent=2))
for name,frame_num,loc in [('closed',1,(-4,-7,3.65)),('open',145,(-4,-7,3.65)),('side_closed',1,(0,-8,2.3))]:
 scene.frame_set(frame_num);camera(loc);scene.render.filepath=str(OUT/(name+'.png'))
 bpy.ops.render.render(write_still=True)
print('R82_FORM_RENDERED',flush=True)
