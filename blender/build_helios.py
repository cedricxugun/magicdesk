import bpy,math,json,pathlib,random
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];ASSET=ROOT/'app'/'assets';OUT=ROOT/'blender';REVIEW=ROOT/'review'
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene;S.name='HELIOS — Mechanical Seed';S.unit_settings.system='METRIC';S.render.fps=24
COL=bpy.data.collections.new('HELIOS_ASSET');S.collection.children.link(COL)
PARTS=[];CONTROLS=[];HINGES=[];ACTUATORS=[];random.seed(1955)
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def mat(name,rgb,metal=0,rough=.3,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*[linear(v) for v in rgb],1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 m.diffuse_color=(*[linear(v) for v in rgb],1)
 if emission:p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=emission
 return m
M={'Ivory':mat('Ivory_Enamel',(.86,.82,.73),.05,.29),'Steel':mat('Dark_Brushed_Steel',(.33,.32,.285),.91,.32),'Black':mat('Graphite',(.105,.10,.087),.72,.35),'Chrome':mat('Polished_Nickel',(.58,.55,.49),.96,.24),'Red':mat('Cherry_Enamel',(.34,.055,.032),.3,.28),'Brass':mat('Warm_Nickel',(.45,.34,.22),.88,.3),'Rubber':mat('Black_Polymer',(.038,.035,.032),.04,.49),'Core':mat('Solar_Core_Emission',(1,.115,.008),.42,.23,.8),'Amber':mat('Amber_Light',(1,.25,.023),.25,.25,1.4),'Letter':mat('Ivory_Engraving',(.75,.67,.51),.1,.42)}
for key,file,inputname in [('Ivory','enamel_albedo.png','Base Color'),('Ivory','enamel_roughness.png','Roughness'),('Steel','steel_albedo.png','Base Color'),('Chrome','nickel_albedo.png','Base Color'),('Steel','metal_roughness.png','Roughness'),('Chrome','metal_roughness.png','Roughness')]:
 m=M[key];node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ASSET/file),check_existing=True)
 if inputname=='Roughness':node.image.colorspace_settings.name='Non-Color'
 m.node_tree.links.new(node.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs[inputname])
for key,filename in [('Ivory','enamel_normal.png'),('Steel','metal_normal.png'),('Chrome','metal_normal.png')]:
 m=M[key];nt=m.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSET/filename),check_existing=True);tex.image.colorspace_settings.name='Non-Color';normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.32;nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
M['Ivory'].node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.24
M['Ivory'].node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.2

def put(o,parent=None,loc=(0,0,0),rot=None):
 for c in list(o.users_collection):c.objects.unlink(o)
 COL.objects.link(o);o.parent=parent;o.location=loc
 if rot is not None:
  if isinstance(rot,Quaternion):o.rotation_mode='QUATERNION';o.rotation_quaternion=rot
  else:o.rotation_euler=rot
 return o
def empty(name,parent=None,loc=(0,0,0),rot=None):
 o=bpy.data.objects.new(name,None);COL.objects.link(o);o.parent=parent;o.location=loc
 if rot:o.rotation_euler=rot
 return o
def finish(o,name,key,parent,loc,rot=None,smooth=True,bevel=0):
 o.name=name;put(o,parent,loc,rot);o.data.materials.append(M[key])
 for p in o.data.polygons:p.use_smooth=smooth and len(p.vertices)<=4
 if bevel:
  mod=o.modifiers.new('Soft manufactured edge','BEVEL');mod.width=bevel;mod.segments=3
  normal=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');normal.keep_sharp=True
 return o
def cube(name,dim,key,parent=None,loc=(0,0,0),bevel=.02,rot=None):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,key,parent,loc,rot,True,bevel)
def cyl(name,r,depth,key,parent=None,loc=(0,0,0),rot=None,n=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth)
 return finish(bpy.context.object,name,key,parent,loc,rot,True,min(.004,r*.12))
def sphere(name,r,key,parent=None,loc=(0,0,0),scale=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=r);o=bpy.context.object
 if scale:o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,key,parent,loc,smooth=True)
def torus(name,r,t,key,parent=None,loc=(0,0,0),rot=None):
 bpy.ops.mesh.primitive_torus_add(major_segments=96,minor_segments=10,major_radius=r,minor_radius=t)
 return finish(bpy.context.object,name,key,parent,loc,rot,True)
def tube(name,points,r,key,parent=None):
 data=bpy.data.curves.new(name+'_curve','CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
 sp=data.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,data);COL.objects.link(o);o.parent=parent;data.materials.append(M[key]);return o
def beam(name,a,b,r,key,parent=None):
 a=Vector(a);b=Vector(b);v=b-a
 return cyl(name,r,v.length,key,parent,(a+b)/2,v.to_track_quat('Z','Y'),24)
def part(name,parent,offset=(0,0,.3),stage=.1,spin=.12):
 o=empty('P_'+name,parent);o['explode_part']=True;o['explode_offset']=offset;o['explode_stage']=stage
 PARTS.append({'obj':o,'offset':list(offset),'stage':stage,'spin':spin});return o
exec(compile((OUT/'fast_geometry.py').read_text(encoding='utf-8'),str(OUT/'fast_geometry.py'),'exec'))
R=empty('HELIOS_ROOT');BASE=empty('BASE_FIXED',R);TURN=empty('TURNTABLE',R)
# Fixed display pedestal and stationary physical buttons.
cyl('Base_Rubber_Foot',1.27,.11,'Rubber',BASE,(0,0,.08),n=96)
cyl('Base_Drum',1.34,.36,'Black',BASE,(0,0,.29),n=128)
cyl('Base_Lower_Rim',1.37,.055,'Chrome',BASE,(0,0,.135),n=128)
cyl('Base_Upper_Rim',1.34,.045,'Chrome',BASE,(0,0,.485),n=128)
cyl('Fixed_Deck',1.25,.085,'Steel',BASE,(0,0,.52),n=128)
torus('Deck_Rim',1.24,.026,'Chrome',BASE,(0,0,.567))
for i,angle in enumerate([30,150,270]):
 t=math.radians(angle);cyl('Foot_%d'%i,.22,.09,'Rubber',BASE,(1.05*math.cos(t),1.05*math.sin(t),.05))
def arc_panel(name,r,z0,z1,a0,a1,key,parent):
 verts=[];steps=80
 for z in [z0,z1]:
  for i in range(steps+1):a=a0+(a1-a0)*i/steps;verts.append((r*math.cos(a),r*math.sin(a),z))
 faces=[(i,i+1,steps+2+i,steps+1+i) for i in range(steps)]
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent;me.materials.append(M[key])
 layer=me.uv_layers.new(name='PanelUV')
 for p in me.polygons:
  for li in p.loop_indices:
   vi=me.loops[li].vertex_index;layer.data[li].uv=(vi%(steps+1)/steps,vi//(steps+1))
 sol=o.modifiers.new('Panel thickness','SOLIDIFY');sol.thickness=.025
 for p in me.polygons:p.use_smooth=True
 return o
arc_panel('Fixed_Ivory_Control_Fascia',1.354,.155,.46,math.radians(-153),math.radians(-27),'Ivory',BASE)
BUTTONS=[]
for i,a in enumerate([math.radians(-144+18*i) for i in range(7)]):
 radial=Vector((math.cos(a),math.sin(a),0));mount=empty('BUTTON_%02d_MOUNT'%i,BASE,radial*1.373+Vector((0,0,.31)))
 mount.rotation_mode='QUATERNION';mount.rotation_quaternion=radial.to_track_quat('Z','Y')
 cyl('Button_%d_Gasket'%i,.146,.018,'Rubber',mount,(0,0,.002))
 cyl('Button_%d_Bezel'%i,.138,.043,'Steel',mount,(0,0,.023))
 torus('Button_%d_MilledRim'%i,.124,.009,'Chrome',mount,(0,0,.051))
 cap=cyl('BUTTON_%02d_CAP'%i,.113,.016,'Red' if i==6 else 'Ivory',mount,(0,0,.055),n=64)
 # Enamel inlays match the six symbols on the approved B reference.
 def dot(name,x,y,r):
  cyl(name+'_Recess',r+.002,.0015,'Black',cap,(x,y,.0095),n=24)
  cyl(name+'_Red_Inlay',r,.0014,'Red',cap,(x,y,.0104),n=24)
 if i==0:
  pts=[]
  for cc,aa in [(.033,range(0,181,9)),(-.033,range(180,361,9))]:
   for deg in aa:a=math.radians(deg);pts.append((.017*math.cos(a),cc+.017*math.sin(a),.010))
  pts.append(pts[0]);tube('Reference_Power_Slot',pts,.0025,'Black',cap)
  cube('Reference_Power_Red',(.008,.062,.0015),'Red',cap,(0,0,.010),.001)
 elif i==1:
  dot('Reference_Sun_Core',0,0,.018)
  for j in range(8):
   a=j*math.tau/8;dot('Reference_Sun_Ray',.047*math.cos(a),.047*math.sin(a),.008)
 elif i==2:
  for x,y in [(0,.028),(-.029,-.024),(.029,-.024)]:dot('Reference_Triple',x,y,.020)
 elif i==3:
  for j in range(4):a=j*math.tau/4;dot('Reference_Quad',.033*math.cos(a),.033*math.sin(a),.019)
 elif i==4:
  points=[(-.049,-.043,.010),(.049,-.043,.010),(0,.063,.010)]
  me=bpy.data.meshes.new('Reference_Triangle');me.from_pydata(points,[],[(0,1,2)]);me.materials.append(M['Red']);o=bpy.data.objects.new('Reference_Triangle',me);COL.objects.link(o);o.parent=cap
  tube('Reference_Triangle_Outline',points+[points[0]],.0024,'Black',cap)
  beam('Reference_Triangle_Stem',(0,-.075,.011),(0,.047,.011),.0027,'Black',cap)
 elif i==5:
  for j in range(8):
   a=j*math.tau/8;length=.062 if j%2==0 else .045
   beam('Reference_Star_Ray',(.016*math.cos(a),.016*math.sin(a),.010),(length*math.cos(a),length*math.sin(a),.010),.003,'Red',cap)
  dot('Reference_Star_Core',0,0,.010)
 else:
  for a in [-math.pi/4,math.pi/4]:cube('Shutdown_Nickel_Cross',(.022,.139,.008),'Chrome',cap,(0,0,.013),.003,rot=(0,0,a))
 BUTTONS.append({'index':i,'mount':mount.name,'cap':cap.name,'home':None,'function':['wake','bloom','overload','explode','assemble','rotate','quit'][i]})
for a in [-155,-25,60,120]:
 t=math.radians(a);strip=empty('Base_Accent_%d'%a,BASE,(1.35*math.cos(t),1.35*math.sin(t),.30),rot=(0,0,t))
 cube('Red_Side_Strap_%d'%a,(.02,.042,.18),'Red',strip,bevel=.006)
for i in range(24):
 a=math.tau*i/24;cyl('Deck_Rivet_%02d'%i,.025,.014,'Chrome',BASE,(1.18*math.cos(a),1.18*math.sin(a),.574),n=12)
# Rotating upper machinery. Base and its controls remain fixed.
cyl('Upper_Turntable',1.03,.09,'Black',TURN,(0,0,.61),n=96)
torus('Upper_Turntable_Line',.97,.017,'Brass',TURN,(0,0,.666))
pa=part('Lower_Stator',TURN,(0,0,.26),.30,0)
cyl('Stator_Body',.43,.24,'Steel',pa,(0,0,.785));torus('Stator_Upper_Ring',.44,.026,'Chrome',pa,(0,0,.90));torus('Stator_Lower_Ring',.44,.028,'Chrome',pa,(0,0,.67))
pa=part('Socket_Crown',TURN,(0,0,.48),.23,0)
cyl('Crown_Body',.35,.12,'Chrome',pa,(0,0,.975))
for j in range(12):
 a=j*math.tau/12;cube('Crown_Notch_%d'%j,(.05,.075,.09),'Black',pa,(.349*math.cos(a),.349*math.sin(a),.99),.008,rot=(0,0,a))

Z0=1.02;HEIGHT=2.68;R0=.31
def radius(t):
 ts=[0,.06,.16,.30,.47,.62,.76,.87,.95,1];rs=[.31,.43,.62,.78,.865,.84,.73,.565,.365,.17]
 t=max(0,min(1,t));j=next((i for i in range(len(ts)-1) if t<=ts[i+1]),len(ts)-2);u=(t-ts[j])/(ts[j+1]-ts[j]);h=ts[j+1]-ts[j]
 m0=(rs[j+1]-rs[max(0,j-1)])/(ts[j+1]-ts[max(0,j-1)])
 m1=(rs[min(len(ts)-1,j+2)]-rs[j])/(ts[min(len(ts)-1,j+2)]-ts[j])
 return (2*u**3-3*u*u+1)*rs[j]+(u**3-2*u*u+u)*h*m0+(-2*u**3+3*u*u)*rs[j+1]+(u**3-u*u)*h*m1
def petal_surface(name,key,parent,inside=False):
 nu=24;nv=72;half=math.radians(28.5 if inside else 26.5);verts=[];uv=[]
 for j in range(nv+1):
  t=j/nv;r=radius(t)-(.052 if inside else 0)
  for k in range(nu+1):a=-half+2*half*k/nu;verts.append((r*math.cos(a)-R0,r*math.sin(a),HEIGHT*t));uv.append((k/nu,t))
 faces=[]
 for j in range(nv):
  for k in range(nu):a=j*(nu+1)+k;faces.append((a,a+1,a+nu+2,a+nu+1))
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.materials.append(M[key]);layer=me.uv_layers.new(name='SurfaceUV')
 for p in me.polygons:
  p.use_smooth=True
  for li in p.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
 o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent
 sol=o.modifiers.new('Real shell thickness','SOLIDIFY');sol.thickness=.028 if inside else .035;sol.offset=-1
 bev=o.modifiers.new('Rolled enamel edge','BEVEL');bev.width=.005;bev.segments=3
 return o

for i in range(6):
 th=-math.pi/2+i*math.tau/6;rad=Vector((math.cos(th),math.sin(th),0));tan=Vector((-math.sin(th),math.cos(th),0))
 hinge=empty('PETAL_HINGE_%02d'%i,TURN,rad*R0+Vector((0,0,Z0)),(0,0,th));HINGES.append(hinge)
 shell=part('Petal_%02d_Enamel'%i,hinge,rad*1.32+Vector((0,0,.27)),0,.06*(-1 if i%2 else 1))
 outer=petal_surface('Petal_%02d_OuterSkin'%i,'Ivory',shell)
 lining=part('Petal_%02d_Liner'%i,hinge,rad*.94+Vector((0,0,.35)),.10,-.06)
 petal_surface('Petal_%02d_InnerSkin'%i,'Black',lining,True)
 rails=part('Petal_%02d_RibFrame'%i,hinge,rad*1.08+tan*.23+Vector((0,0,.50)),.16,.08)
 for side in [-1,1]:
  a=math.radians(26.5)*side;pts=[]
  for j in range(45):t=j/44;r=radius(t)-.008;pts.append((r*math.cos(a)-R0,r*math.sin(a),HEIGHT*t))
  tube('Petal_%02d_Edge_%d'%(i,side),pts,.006,'Chrome',rails)
 for j,t in enumerate([.12,.27,.44,.60,.76,.90]):
  r=radius(t)-.073;pts=[]
  for k in range(15):a=math.radians(-25+50*k/14);pts.append((r*math.cos(a)-R0,r*math.sin(a),HEIGHT*t))
  tube('Petal_%02d_InnerRib_%d'%(i,j),pts,.022,'Steel',rails)
  for side in [-1,1]:
   a=math.radians(22)*side;sphere('Petal_Rivet_%02d_%d_%d'%(i,j,side),.017,'Brass',rails,((r+.06)*math.cos(a)-R0,(r+.06)*math.sin(a),HEIGHT*t))
 latch=part('Petal_%02d_Latch'%i,hinge,rad*1.55+tan*.15+Vector((0,0,-.12)),.03,.25)
 t=.34;rr=radius(t);ang=math.radians(23);q=(rr*math.cos(ang)-R0,rr*math.sin(ang),HEIGHT*t)
 cube('Latch_Chrome_%02d'%i,(.04,.065,.16),'Steel',latch,q,.007,rot=(0,0,ang))
 cube('Latch_Red_%02d'%i,(.047,.038,.126),'Red',latch,(q[0]+.02,q[1],q[2]),.006,rot=(0,0,ang))
 for dz in [-.067,.067]:cyl('Latch_Pin_%d_%s'%(i,dz),.013,.014,'Chrome',latch,(q[0]+.038,q[1],q[2]+dz),rot=(0,math.pi/2,0),n=16)
 hub=part('Petal_%02d_HingeCap'%i,hinge,rad*.55+tan*.48+Vector((0,0,.16)),.20,.12)
 cyl('Hinge_Housing_%02d'%i,.15,.29,'Steel',hub,(0,0,.015),rot=(math.pi/2,0,0))
 for side in [-1,1]:
  cyl('Hinge_RedWasher_%02d_%d'%(i,side),.119,.021,'Red',hub,(0,side*.157,.015),rot=(math.pi/2,0,0))
  cyl('Hinge_End_%02d_%d'%(i,side),.082,.026,'Chrome',hub,(0,side*.174,.015),rot=(math.pi/2,0,0))
 # Pivot cradle, and one real telescopic actuator for each petal.
 fixed=part('Petal_%02d_BaseJoint'%i,TURN,rad*1.22+Vector((0,0,-.04)),.22,.15)
 # The fixed pivot is outside the full swept arc of the petal attachment.
 # A pivot directly under that arc collapses the cylinder at mid-opening.
 A=rad*1.25+Vector((0,0,.67));sphere('BaseJoint_Ball_%02d'%i,.075,'Steel',fixed,A)

 barrel=empty('ACTUATOR_%02d_BARREL'%i,TURN);rod=empty('ACTUATOR_%02d_ROD'%i,TURN)
 bp=part('Actuator_%02d_Barrel'%i,barrel,rad*1.10+tan*.18+Vector((0,0,-.18)),.08,.15)
 bp.scale=(1,1,.65)
 cyl('ActuatorBarrel_%02d'%i,.09,.32,'Chrome',bp)
 for z in [-.18,-.14,.135,.18]:cyl('ActuatorCollar_%02d_%s'%(i,z),.108,.03,'Steel',bp,(0,0,z))
 torus('ActuatorRedBand_%02d'%i,.1,.008,'Red',bp,(0,0,-.118))
 rp=part('Actuator_%02d_Rod'%i,rod,rad*1.28-tan*.18+Vector((0,0,.24)),.16,-.12)
 cyl('PistonRod_%02d'%i,.037,.60,'Chrome',rp)
 # Nested compact ram stages preserve a plausible extension ratio.
 cyl('PistonOuterStage_%02d'%i,.052,.34,'Steel',rp,(0,0,-.13))
 cyl('PistonMiddleStage_%02d'%i,.044,.43,'Chrome',rp,(0,0,-.085))
 torus('PistonStageSeal_%02d'%i,.047,.005,'Rubber',rp,(0,0,.04))
 # Upper attachment is mounted on the same physical petal as the shell.
 attach_t=.145
 attach_slope=(radius(attach_t+.001)-radius(attach_t-.001))/(.002*HEIGHT)
 attach_normal=Vector((1,0,-attach_slope)).normalized()
 attach=Vector((radius(attach_t)-R0,0,HEIGHT*attach_t))+attach_normal*.145
 sphere('Petal_ActuatorBall_%02d'%i,.09,'Chrome',rails,attach)
 ACTUATORS.append((barrel,rod,A,hinge,attach))
 for ctrl in [hinge,barrel,rod]:CONTROLS.append({'obj':ctrl,'petal':i})
 # Actual opening in front shell, with enamel/metal rim and inner amber filament.
 if i==0:
  center=Vector((radius(.52)-R0,0,HEIGHT*.52))
  cutter=cube('Window_Cutter',(.60,.18,.75),'Black',shell,center,.084)
  bpy.context.view_layer.objects.active=cutter;cutter.select_set(True)
  for mod in list(cutter.modifiers):
   try:bpy.ops.object.modifier_apply(modifier=mod.name)
   except Exception:pass
  bpy.context.view_layer.objects.active=outer
  sol=outer.modifiers.get('Real shell thickness');bpy.ops.object.modifier_apply(modifier=sol.name)
  boolean=outer.modifiers.new('True inspection aperture','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
  bpy.ops.object.modifier_apply(modifier=boolean.name);bpy.data.objects.remove(cutter,do_unlink=True)
  win=part('Inspection_Window',hinge,rad*1.66+Vector((0,0,.22)),.02,.08)
  pts=[];cy=HEIGHT*.52
  for centerz,angles in [(cy+.26,[math.radians(k) for k in range(0,181,6)]),(cy-.26,[math.radians(k) for k in range(180,361,6)])]:
   for a in angles:
    yy=.102*math.cos(a);zz=centerz+.102*math.sin(a);rr=radius(zz/HEIGHT)
    pts.append((rr-R0+.009,yy,zz))
  pts.append(pts[0]);tube('Inspection_ChromeSeal',pts,.022,'Chrome',win)
  cube('Inspection_DarkGlass',(.04,.14,.66),'Black',win,(center.x-.045,0,center.z),.04)
  filament=part('Inspection_Filament',hinge,rad*1.44+Vector((0,0,.4)),.12,.05)
  beam('Amber_InnerTube',(center.x-.012,0,center.z-.25),(center.x-.012,0,center.z+.25),.016,'Amber',filament)

# Core cradle with three mechanically nested, distinct-radius gimbals.
lift=empty('CORE_LIFT',TURN,(0,0,2.19));CONTROLS.append({'obj':lift,'petal':-1})
G1=empty('GYRO_OUTER',lift);G2=empty('GYRO_MIDDLE',G1);G3=empty('GYRO_INNER',G2);CORE_SPIN=empty('CORE_ROTOR',G3)
def band(name,r,width,depth,key,parent):
 verts=[];N=96
 for k in range(N):
  a=k*math.tau/N
  for rr,yy in [(r-width/2,-depth/2),(r+width/2,-depth/2),(r+width/2,depth/2),(r-width/2,depth/2)]:verts.append((rr*math.cos(a),yy,rr*math.sin(a)))
 faces=[]
 for k in range(N):
  for j in range(4):faces.append((k*4+j,((k+1)%N)*4+j,((k+1)%N)*4+(j+1)%4,k*4+(j+1)%4))
 faces=[tuple(reversed(f)) for f in faces]
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.materials.append(M[key]);o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent
 for p in me.polygons:p.use_smooth=True
 return o
for idx,(g,r) in enumerate([(G1,.70),(G2,.54),(G3,.39)]):
 pa=part('Gimbal_%d_Ring'%idx,g,(0,(idx-1)*.55,.5+idx*.27),.22+idx*.04,.2)
 band('Gimbal_%d_Band'%idx,r,.065,.035,'Chrome',pa)
 for side in [-1,1]:torus('Gimbal_%d_RedTrack_%d'%(idx,side),r+side*.025,.006,'Brass',pa,rot=(math.pi/2,0,0))
 for j in range(8):
  a=j*math.tau/8;cyl('Ring_%d_Fastener_%d'%(idx,j),.022,.013,'Steel',pa,(r*math.cos(a),-.027,r*math.sin(a)),rot=(math.pi/2,0,0),n=12)
pa=part('Middle_Trunnions',G1,(.45,0,.53),.29,.18)
for side in [-1,1]:beam('Middle_Axle_%d'%side,(side*.54,0,0),(side*.71,0,0),.045,'Brass',pa)
pa=part('Inner_Trunnions',G2,(-.45,0,.85),.32,-.18)
for side in [-1,1]:beam('Inner_Axle_%d'%side,(0,0,side*.39),(0,0,side*.55),.04,'Steel',pa)
pa=part('Solar_Crystal',CORE_SPIN,(0,0,1.15),.32,.4)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.275);crystal=finish(bpy.context.object,'CORE_EMISSIVE_CRYSTAL','Core',pa,(0,0,0),smooth=False)
pa=part('Solar_Lattice',CORE_SPIN,(0,-.40,.9),.27,-.2)
mesh=crystal.data
for j,e in enumerate(mesh.edges):a=Vector(mesh.vertices[e.vertices[0]].co)*1.06;b=Vector(mesh.vertices[e.vertices[1]].co)*1.06;beam('Lattice_%03d'%j,a,b,.0065,'Brass',pa)
for side in [-1,1]:beam('Core_Pin_%d'%side,(side*.27,0,0),(side*.395,0,0),.032,'Chrome',pa)
support=empty('CORE_SUPPORT_ROD',TURN);CONTROLS.append({'obj':support,'petal':-1})
pa=part('Core_Support_Post',support,(0,0,.28),.26,0);cyl('Core_Support_Shaft',.075,.5,'Chrome',pa);torus('Core_Support_Collar',.09,.018,'Steel',pa,(0,0,-.19))
pa=part('Core_Bottom_Bearing',G1,(0,0,.62),.30,0);sphere('Outer_Ring_South_Bearing',.115,'Steel',pa,(0,0,-.70));torus('Outer_Ring_South_Band',.10,.015,'Red',pa,(0,0,-.70))
for i,hinge in enumerate(HINGES):
 th=-math.pi/2+i*math.tau/6;rad=Vector((math.cos(th),math.sin(th),0))
 top=part('Crown_Sector_%02d'%i,hinge,rad*1.38+Vector((0,0,.46)),.04,.16)
 verts=[];N=12
 for z in [HEIGHT-.025,HEIGHT+.055]:
  for r in [.085,.158]:
   for k in range(N+1):a=math.radians(-28+56*k/N);verts.append((r*math.cos(a)-R0,r*math.sin(a),z))
 L=N+1;faces=[]
 for k in range(N):faces.extend([(k,k+1,L+k+1,L+k),(2*L+k,3*L+k,3*L+k+1,2*L+k+1),(L+k,L+k+1,3*L+k+1,3*L+k),(k,2*L+k,2*L+k+1,k+1)])
 faces.extend([(0,L,3*L,2*L),(N,2*L+N,3*L+N,L+N)])
 me=bpy.data.meshes.new('CrownSectorMesh');me.from_pydata(verts,[],faces);me.materials.append(M['Steel']);o=bpy.data.objects.new('CrownSector_%02d'%i,me);COL.objects.link(o);o.parent=top
 sphere('Crown_Rivet_%d'%i,.023,'Brass',top,(.158-R0,0,HEIGHT+.015))

exec(compile((OUT/'detail_helios.py').read_text(encoding='utf-8'),str(OUT/'detail_helios.py'),'exec'))

def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def set_control_pose(v,stagger=False):
 for i,h in enumerate(HINGES):
  a=v
  th=-math.pi/2+i*math.tau/6;h.rotation_mode='XYZ';h.rotation_euler=(0,math.radians(68)*a,th)
 for i,(barrel,rod,A,h,attach) in enumerate(ACTUATORS):
  hmat=Matrix.Translation(h.location)@h.rotation_euler.to_matrix().to_4x4();B=hmat@attach;d=B-A;L=d.length;unit=d.normalized();q=d.to_track_quat('Z','Y')
  barrel.location=A+unit*.145;barrel.rotation_mode='QUATERNION';barrel.rotation_quaternion=q
  rod.location=(A+unit*.10+B)*.5;rod.rotation_mode='QUATERNION';rod.rotation_quaternion=q;rod.scale=(1,1,max(.02,L-.10)/.6)
 lift.location=(0,0,2.19+.16*v);end=lift.location.z-.70;support.location=(0,0,(1.+end)/2);support.scale=(1,1,(end-1.)/.5)
def transform_data(m):
 p,q,s=(C@m@C.inverted()).decompose();return {'p':list(p),'q':[q.x,q.y,q.z,q.w],'s':list(s)}
set_control_pose(0);bpy.context.view_layer.update()
for p in PARTS:p['home']=p['obj'].matrix_basis.copy()
control_data=[]
for ctrl in CONTROLS:control_data.append({'name':ctrl['obj'].name,'petal':ctrl['petal'],'samples':[]})
for j in range(101):
 set_control_pose(j/100);bpy.context.view_layer.update()
 for d,c in zip(control_data,CONTROLS):d['samples'].append(transform_data(c['obj'].matrix_local))
set_control_pose(0)
part_data=[]
for i,p in enumerate(PARTS):
 d={'name':p['obj'].name,'offset':list((C.to_3x3()@Vector(p['offset']))),'stage':p['stage'],'spin':p['spin'],'home':transform_data(p['home'])};part_data.append(d)
for b in BUTTONS:b['home']=transform_data(bpy.data.objects[b['cap']].matrix_local)
meta={'title':'HELIOS INCUBATOR','version':'1.0','source':'Helios_Incubator.blend','root':'HELIOS_ROOT','turntable':'TURNTABLE','base':'BASE_FIXED','parts':part_data,'controls':control_data,'buttons':BUTTONS,'gyro':{'outer':G1.name,'middle':G2.name,'inner':G3.name,'core':CORE_SPIN.name},'core_world':[0,2.19,0],'button_functions':['wake','bloom','overload','explode','assemble','rotate','quit'],'part_count':len(PARTS),'concept_reference':'B_孵日器.png'}
meta['button_count']=len(BUTTONS)
(ASSET/'mechanism.json').write_text(json.dumps(meta,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
# Join only static geometry inside each independent moving group. Controls remain separate.
bpy.ops.object.select_all(action='DESELECT')
for o in list(COL.objects):
 if o.type=='MESH' and o.data.uv_layers:o.data.uv_layers.active.name='UVMap'
 if o.type in ['MESH','CURVE']:o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.object.convert(target='MESH')
caps={b['cap'] for b in BUTTONS};part_names={p['obj'].name for p in PARTS};groups={}
for name in caps:
 o=bpy.data.objects[name]
 if o.data.users>1:o.data=o.data.copy()
for o in list(COL.objects):
 if o.type!='MESH':continue
 owner=o if o.name in caps else o.parent
 while owner and owner.name not in caps and owner.name not in part_names and owner not in [BASE,TURN]:owner=owner.parent
 if owner:groups.setdefault(owner,[]).append(o)
for owner,meshes in groups.items():
 if len(meshes)<2:continue
 bpy.ops.object.select_all(action='DESELECT')
 if owner.type=='MESH':active=owner
 else:
  active=bpy.data.objects.new(owner.name+'_DisplayMesh',bpy.data.meshes.new(owner.name+'_JoinedMesh'));COL.objects.link(active);active.parent=owner
 for o in meshes:o.select_set(True)
 active.select_set(True);bpy.context.view_layer.objects.active=active;bpy.ops.object.join()

for o in COL.objects:
 if o.type=='MESH' and o.data.uv_layers:
  o.data.uv_layers.active_index=0;o.data.uv_layers[0].active_render=True

# Environment map: soft-box studio lighting exported to Godot too.
import numpy as np
w,h=1024,512;xx=np.arange(w)[None,:]/w;yy=np.arange(h)[:,None]/h
env=np.zeros((h,w,4),dtype=np.float32);env[:,:,:3]=(.15,.17,.20);env[:,:,3]=1
for cx,cy,sx,sy,power,tint in [(.20,.31,.045,.10,5.8,(1,.89,.74)),(.78,.36,.022,.15,7.0,(.72,.84,1)),(.5,.13,.20,.034,3.0,(1,1,.98)),(.48,.7,.12,.03,.7,(.6,.6,.7))]:
 dx=np.minimum(np.abs(xx-cx),1-np.abs(xx-cx));weight=np.exp(-((dx/sx)**6+((yy-cy)/sy)**6))
 for ch in range(3):env[:,:,ch]+=weight*power*tint[ch]
im=bpy.data.images.new('Helios_Studio_HDR',width=w,height=h,float_buffer=True);im.pixels.foreach_set(env.ravel());im.filepath_raw=str(ASSET/'studio.exr');im.file_format='OPEN_EXR';im.save()
world=bpy.data.worlds.new('Helios Studio');S.world=world;world.use_nodes=True;wn=world.node_tree;bg=wn.nodes.get('Background');bg.inputs['Strength'].default_value=.24;tex=wn.nodes.new('ShaderNodeTexEnvironment');tex.image=im;wn.links.new(tex.outputs['Color'],bg.inputs['Color'])
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.75,-9,4.3));CAM=bpy.context.object;CAM.name='HELIOS_CAMERA';aim(CAM,(0,0,1.92));CAM.data.type='ORTHO';CAM.data.ortho_scale=5.15;S.camera=CAM
for name,loc,energy,size,color in [('Key',(-3.5,-4,6),650,3,(1,.93,.82)),('Rim',(3,2,5),900,3,(.83,.88,1)),('Front',(1,-6,3),110,4,(1,.98,.94))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='STUDIO_'+name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color;aim(o,(0,0,1.8))
S.render.engine='CYCLES';S.cycles.samples=96;S.cycles.use_denoising=True;S.render.resolution_x=1400;S.render.resolution_y=1600;S.render.resolution_percentage=100
S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast';S.render.film_transparent=True;S.render.image_settings.file_format='PNG'

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));ground=bpy.context.object;ground.name='STUDIO_Ground';ground.data.materials.append(mat('Studio_Backdrop',(.055,.059,.061),.1,.5))
S.render.film_transparent=False
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type!='CPU'
 if any(d.use for d in prefs.devices):S.cycles.device='GPU'
except Exception as e:print('CYCLES_DEVICE',e)

def pose(open_v=0,phase=0,explosion=0):
 set_control_pose(open_v,True)
 G1.rotation_euler.z=.2+phase*.65;G2.rotation_euler.x=.6+math.sin(phase*.55)*.9;G3.rotation_euler.z=.7+phase;CORE_SPIN.rotation_euler.x=phase*.8
 for p in PARTS:p['obj'].matrix_basis=p['home'].copy()
 bpy.context.view_layer.update()
 for p in PARTS:
  amount=smooth((explosion-p['stage'])/.70);o=p['obj'];loc,rot,scale=p['home'].decompose()
  delta=o.parent.matrix_world.to_3x3().inverted()@TURN.matrix_world.to_3x3()@Vector(p['offset'])
  o.location=loc+delta*amount;o.rotation_mode='QUATERNION';o.rotation_quaternion=rot@Quaternion((0,0,1),p['spin']*amount);o.scale=scale
 bpy.context.view_layer.update()

# Source-file animated showcase; interactive EXE uses the same sampled mechanism.
pose(0,0,0)
for im in bpy.data.images:
 if im.source=='FILE':
  try:im.pack()
  except Exception:pass
S.frame_start=1;S.frame_end=600
markers={'WAKE':1,'BLOOM':50,'OVERLOAD':160,'EXPLODE':260,'EXPLODED':320,'ASSEMBLE':375,'CLOSE':480,'SLEEP':550}
for name,f in markers.items():S.timeline_markers.new(name,frame=f)
all_anim=[c['obj'] for c in CONTROLS]+[G1,G2,G3,CORE_SPIN]+[p['obj'] for p in PARTS]
for f in range(1,601,2):
 t=(f-1)/24
 if f<50:op=0;phase=t*.6;ex=0
 elif f<145:op=smooth((f-50)/80);phase=1+t*.65;ex=0
 elif f<250:op=1;phase=5+(f-145)/24*3;ex=0
 elif f<320:op=1-smooth((f-260)/36);phase=18.125;ex=1-(1-max(0,min(1,(f-260)/45)))**3
 elif f<375:op=0;phase=18.125;ex=1
 elif f<465:op=0;phase=18.125;ex=1-smooth((f-375)/75)
 else:op=0;phase=18.125+(f-465)/24*.7;ex=0
 S.frame_set(f);pose(op,phase,ex)
 for o in all_anim:
  o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='scale',frame=f)
  o.keyframe_insert(data_path='rotation_quaternion' if o.rotation_mode=='QUATERNION' else 'rotation_euler',frame=f)
for o in all_anim:
 if o.animation_data and o.animation_data.action:o.animation_data.action.name='HELIOS_Demo__'+o.name
S.frame_set(1)
for area in bpy.context.screen.areas if bpy.context.screen else []:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Helios_Incubator.blend'),compress=True)
print('HELIOS_CHECKPOINT_READY',len(PARTS),'explodable groups',flush=True)
# Export only the artifact, keeping all its named real part nodes and hierarchy.
bpy.ops.object.select_all(action='DESELECT')
for o in COL.objects:o.select_set(True)
bpy.context.view_layer.objects.active=R
bpy.ops.export_scene.gltf(filepath=str(ASSET/'helios_model.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
for name,f,scale in [('closed',1,4.55),('open',180,7.25),('exploded',340,8.5)]:
 S.frame_set(f);CAM.data.ortho_scale=scale;S.render.filepath=str(REVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
S.frame_set(1);CAM.data.ortho_scale=5.15
meta_summary={'parts':len(PARTS),'controls':len(CONTROLS),'mesh_objects':len([o for o in COL.objects if o.type=='MESH']),'curve_objects':len([o for o in COL.objects if o.type=='CURVE']),'materials':len(M),'frames':[1,600],'fps':24,'glb':str(ASSET/'helios_model.glb'),'buttons':7}
(OUT/'model_report.json').write_text(json.dumps(meta_summary,indent=2),encoding='utf-8')
print('HELIOS_ASSETS_COMPLETE',json.dumps(meta_summary),flush=True)
