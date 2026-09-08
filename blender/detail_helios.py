# Manufacturing detail belongs to the same physical parts as its parent.
# No cosmetic floating pieces: every screw, cable and bracket follows an assembly group.
def bolt(name,parent,pos,normal=(0,0,1),r=.018,key='Chrome'):
 n=Vector(normal).normalized();q=n.to_track_quat('Z','Y');pos=Vector(pos)
 cyl(name+'_Seat',r*1.46,.006,'Black',parent,pos-n*.002,q,n=24)
 cyl(name+'_Washer',r*1.26,.007,'Steel',parent,pos+n*.002,q,n=24)
 cyl(name+'_Head',r,.010,key,parent,pos+n*.008,q,n=6)
 # Recess is blackened; its bevel gives the head a readable machined scale.
 cyl(name+'_Socket',r*.44,.001,'Black',parent,pos+n*.0133,q,n=6)

def plate_link(name,parent,a,b,width=.10,thickness=.035,key='Chrome'):
 # Extruded capsule plate: two lobed bearing ends with a web in between.
 a=Vector(a);b=Vector(b);d=b-a;axis=d.normalized();normal=Vector((0,1,0))
 if abs(normal.dot(axis))>.9:normal=Vector((1,0,0))
 side=axis.cross(normal).normalized();normal=side.cross(axis).normalized();pts=[]
 for center,start in [(b,-math.pi/2),(a,math.pi/2)]:
  for k in range(13):ang=start+k*math.pi/12;pts.append(center+axis*math.cos(ang)*width+side*math.sin(ang)*width)
 N=len(pts);verts=[tuple(p+normal*t) for t in [-thickness/2,thickness/2] for p in pts]
 faces=[tuple(range(N)),tuple(range(N*2-1,N-1,-1))]+[(k+N,(k+1)%N+N,(k+1)%N,k) for k in range(N)]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent;me.materials.append(M[key]);be=o.modifiers.new('Milled perimeter','BEVEL');be.width=.006;be.segments=3
 return o

def normal_at(t,a):
 dr=(radius(min(1,t+.0001))-radius(max(0,t-.0001)))/(.0002*HEIGHT)
 return Vector((math.cos(a),math.sin(a),-dr)).normalized()

def surf(t,a,offset=0):
 r=radius(t)+offset;return Vector((r*math.cos(a)-R0,r*math.sin(a),HEIGHT*t))

def skin_strip(name,parent,t0,t1,a0,a1,offset,key,thickness=.012):
 verts=[];N=48
 for j in range(N+1):
  t=t0+(t1-t0)*j/N
  for a in [a0,a1]:verts.append(surf(t,a,offset))
 faces=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(N)]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(M[key]);o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent
 for p in me.polygons:p.use_smooth=True
 sol=o.modifiers.new('Stamped plate thickness','SOLIDIFY');sol.thickness=thickness
 return o

def label(name,text,parent,loc,size=.025,key='Letter',rot=None):
 cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.align_x='CENTER';cu.size=size;cu.extrude=.00035;cu.bevel_depth=.00012;cu.resolution_u=5
 o=bpy.data.objects.new(name,cu);COL.objects.link(o);o.parent=parent;o.location=loc
 if rot:o.rotation_euler=rot
 cu.materials.append(M[key]);return o

# Lathed base: broad dark tiers, separated by thin polished witness lines.
for r,z,t,key in [(1.36,.112,.009,'Steel'),(1.363,.168,.006,'Black'),(1.338,.451,.009,'Steel'),(1.315,.493,.006,'Black'),(1.20,.574,.007,'Black'),(1.11,.578,.006,'Chrome'),(1.02,.668,.008,'Chrome'),(.89,.661,.006,'Black'),(.78,.665,.009,'Steel')]:
 torus('Deck_Concentric_Machining',r,t,key,BASE,(0,0,z))
for zz in [.164,.454]:
 pts=[(1.367*math.cos(a),1.367*math.sin(a),zz) for a in [math.radians(-152+124*k/96) for k in range(97)]]
 tube('Fascia_Inlaid_Perimeter',pts,.0045,'Chrome',BASE)
for side in [-152,-28]:
 a=math.radians(side);rad=Vector((math.cos(a),math.sin(a),0))
 for z in [.185,.425]:bolt('Fascia_Countersunk',BASE,rad*1.382+Vector((0,0,z)),rad,r=.011)
for i in range(12):
 a=i*math.tau/12;rad=Vector((math.cos(a),math.sin(a),0))
 for z in [.22,.39]:
  if math.sin(a)>-.45:
   obj=empty('Base_ServiceGrille',BASE,rad*1.345+Vector((0,0,z)),(0,0,a))
   cube('Base_Vent_Recess',(.012,.14,.035),'Rubber',obj,bevel=.009)
   cube('Base_Vent_InnerLip',(.017,.102,.013),'Brass',obj,(.006,0,0),bevel=.004)
for b in BUTTONS:
 mount=bpy.data.objects[b['mount']];cap=bpy.data.objects[b['cap']]
 for j in range(36):
  a=j*math.tau/36;cyl('Button_KnurledEdge',.003,.012,'Chrome',mount,(.135*math.cos(a),.135*math.sin(a),.032),n=8)
 torus('Button_Enamel_Inlay',.102,.0018,'Brass',cap,(0,0,.010))
 cyl('Button_Status_Jewel',.007,.004,'Amber',mount,(0,.152,.006),n=16)
 label('Button_Index','%02d'%(b['index']+1),mount,(0,-.157,.012),.021,'Letter')
for i in range(36):
 a=i*math.tau/36
 cube('Turntable_Graduation',(.022,.0025,.002),'Letter',TURN,(.927*math.cos(a),.927*math.sin(a),.664),.0005,rot=(0,0,a))
label('Deck_Serial','HELIOS   /   No. 06',BASE,(0,-1.00,.579),.040,'Chrome')

# Six densely machined frames reveal their hinges and bearing chain through the seams.
for i,h in enumerate(HINGES):
 th=-math.pi/2+i*math.tau/6;rad=Vector((math.cos(th),math.sin(th),0));tan=Vector((-math.sin(th),math.cos(th),0))
 rails=bpy.data.objects['P_Petal_%02d_RibFrame'%i];shell=bpy.data.objects['P_Petal_%02d_Enamel'%i];lining=bpy.data.objects['P_Petal_%02d_Liner'%i]
 # Delete the old spherical external rivets; flush socket hardware replaces them.
 for ob in list(COL.objects):
  if ob.name.startswith('Petal_Rivet_%02d_'%i):bpy.data.objects.remove(ob,do_unlink=True)
 for side in [-1,1]:
  aa=math.radians(27.4)*side
  skin_strip('Petal_Seam_Spine',rails,.012,.994,aa-.023,aa+.023,-.018,'Steel',.025)
  skin_strip('Petal_Seam_PolishedLip',rails,.022,.981,aa-.010,aa+.010,-.006,'Chrome',.007)
  # Sixteen real nested screw heads on each recessed seam, not painted dots.
  for j in range(15):
   t=.055+j*.062
   bolt('Seam_Fastener',rails,surf(t,aa,-.001),normal_at(t,aa),.010)
  for t in [.12,.35,.62,.87]:
   aa2=math.radians(24.4)*side;bolt('Enamel_Countersunk',shell,surf(t,aa2,.004),normal_at(t,aa2),.0065,'Brass')
  # Rear frame flanges define the thickness when the flower opens.
  skin_strip('InnerFrame_Flange',rails,.04,.96,aa-.055,aa+.055,-.079,'Steel',.026)
 for j,t in enumerate([.12,.23,.34,.45,.56,.67,.78,.88]):
  pts=[surf(t,math.radians(-25+50*k/30),-.092) for k in range(31)]
  tube('Interior_Cast_Rib',pts,.014,'Chrome',rails)
  # Raised web and recess alternate; visible on the opening side.
  for side in [-1,1]:
   a=math.radians(21)*side;bolt('InnerRib_Bolt',rails,surf(t,a,-.099),-normal_at(t,a),.011)
 for a in [-.21,.21]:skin_strip('InnerFrame_Longitudinal_Web',rails,.055,.94,a-.012,a+.012,-.094,'Steel',.018)
 # Small warning inlays and engraved production mark on the enamel tip.
 for t0,t1 in [(.862,.98),(.025,.13)]:
  skin_strip('Enamel_Center_Seam',shell,t0,t1,-.0018,.0018,.003,'Black',.001)
 skin_strip('Crown_Red_Witness',shell,.896,.949,-.003,.003,.005,'Red',.001)
 # Cast circular hinge carrier beneath the bottom of each panel.
 hub=bpy.data.objects['P_Petal_%02d_HingeCap'%i]
 for side in [-1,1]:
  q=(math.pi/2,0,0);y=side*.19
  cyl('Hinge_Carrier_Ring',.129,.03,'Chrome',hub,(0,y,.015),q,n=64)
  cyl('Hinge_Bearing_Recess',.101,.036,'Black',hub,(0,y+side*.016,.015),q,n=48)
  cyl('Hinge_Hardened_Hub',.074,.04,'Steel',hub,(0,y+side*.029,.015),q,n=48)
  cyl('Hinge_Central_Bolt',.038,.047,'Chrome',hub,(0,y+side*.04,.015),q,n=6)
  for j in range(6):
   a=j*math.tau/6;bolt('Hinge_Housing_Fastener',hub,(.105*math.cos(a),y+side*.027,.015+.105*math.sin(a)),(0,side,0),.008)
 # Base links end in actual pivot eyes and cover the sparse empty space from v1.
 fixed=bpy.data.objects['P_Petal_%02d_BaseJoint'%i]
 linkframe=empty('Lower_Parallel_Link_%d'%i,fixed,(0,0,0),(0,0,th))
 for side in [-1,1]:
  a=Vector((.96,side*.086,.635));b=Vector((1.25,side*.086,.67))
  plate_link('Lower_Forged_Link',linkframe,a,b,.085,.03,'Chrome')
  for pivot in [a,b]:
   bolt('Lower_Link_Bearing',linkframe,pivot+Vector((0,side*.035,0)),(0,side,0),.029)
  middle=(a+b)/2;cyl('Link_Oil_Port',.023,.005,'Black',linkframe,middle+Vector((0,side*.022,0)),rot=(math.pi/2,0,0),n=24)
 cube('Lower_Clevis_Foot',(.23,.29,.055),'Steel',linkframe,(.96,0,.614),.013)
 for xx in [.88,1.04]:
  for yy in [-.112,.112]:bolt('Clevis_Foot_Bolt',linkframe,(xx,yy,.646),r=.012)
 bp=bpy.data.objects['P_Actuator_%02d_Barrel'%i]
 # Two ribbed collars, service ports, tension rods, and bearing eye on each cylinder.
 for zz in [-.19,.17]:
  for j in range(24):
   a=j*math.tau/24;cube('Actuator_Milled_Collar',(.008,.014,.025),'Chrome',bp,(.105*math.cos(a),.105*math.sin(a),zz),.0018,rot=(0,0,a))
 for side in [-1,1]:
  beam('Cylinder_Tie_Rod',(side*.106,0,-.145),(side*.106,0,.142),.012,'Steel',bp)
  for zz in [-.146,.144]:bolt('Cylinder_Tie_Nut',bp,(side*.106,0,zz),(0,0,1 if zz>0 else -1),.017)
  cyl('Cylinder_Service_Port',.03,.025,'Brass',bp,(0,side*.103,-.07),rot=(math.pi/2,0,0),n=6)
 # Flexible braided hose follows this cylinder group, clear of the sliding rod.
 pts=[(.05,.104,-.08),(.05,.145,-.09),(.042,.158,-.17),(.02,.154,-.23),(-.02,.11,-.24)]
 tube('Actuator_Flexible_Hose',pts,.012,'Rubber',bp)
 for j in range(8):
  zz=-.085-j*.017;cyl('Actuator_Hose_Ferrule',.014,.004,'Steel',bp,(.05,.145,zz),n=12)
 cyl('Piston_Gland_Nut',.075,.045,'Steel',bp,(0,0,.215),n=12)
 torus('Piston_Wiper_Seal',.046,.006,'Rubber',bp,(0,0,.244))
 attach=ACTUATORS[i][4]
 contact=surf(.145,0)
 normal=normal_at(.145,0)
 saddle=empty('External_Petal_Mount_%d'%i,rails,contact+normal*.013)
 saddle.rotation_mode='QUATERNION';saddle.rotation_quaternion=normal.to_track_quat('Z','Y')
 cyl('External_Mount_Foot',.13,.027,'Steel',saddle,n=64)
 torus('External_Mount_Seal',.123,.006,'Rubber',saddle,(0,0,-.014))
 for ang in [math.radians(45+k*90) for k in range(4)]:bolt('External_Foot_Screw',saddle,(.103*math.cos(ang),.103*math.sin(ang),.022),r=.012)
 for side in [-1,1]:
  plate_link('External_Clevis_Bridge',rails,contact+normal*.03+Vector((0,side*.078,0)),attach+Vector((0,side*.078,0)),.057,.024,'Steel')
 for side in [-1,1]:
  cyl('Upper_Petal_Clevis',.115,.035,'Steel',rails,attach+Vector((0,side*.073,0)),rot=(math.pi/2,0,0))
  cyl('Upper_Petal_Pivot_Rim',.092,.039,'Chrome',rails,attach+Vector((0,side*.084,0)),rot=(math.pi/2,0,0))
  bolt('Upper_Petal_Pivot_Axle',rails,attach+Vector((0,side*.111,0)),(0,side,0),.04)
  # Tiny housing cover screws have consistent scale across the machine.
  for j in range(4):
   a=j*math.tau/4;bolt('Upper_Petal_Clevis_Screw',rails,attach+Vector((.087*math.cos(a),side*.108,.087*math.sin(a))),(0,side,0),.008)

# Replace the open-ended crown ring with a six-piece domed nickel crown.
for i,h in enumerate(HINGES):
 top=bpy.data.objects['P_Crown_Sector_%02d'%i]
 for ob in list(top.children):bpy.data.objects.remove(ob,do_unlink=True)
 profile=[(.175,HEIGHT-.022),(.192,HEIGHT+.006),(.194,HEIGHT+.038),(.177,HEIGHT+.043),(.166,HEIGHT+.061),(.127,HEIGHT+.079),(.045,HEIGHT+.09),(0,HEIGHT+.093)]
 verts=[];N=20
 for r,z in profile:
  for j in range(N+1):a=math.radians(-29.65+59.3*j/N);verts.append((r*math.cos(a)-R0,r*math.sin(a),z))
 faces=[];L=N+1
 for j in range(len(profile)-1):
  for k in range(N):v=j*L+k;faces.append((v,v+1,v+1+L,v+L))
 me=bpy.data.meshes.new('Crown_Machined_Dome');me.from_pydata(verts,[],faces);me.materials.append(M['Chrome']);o=bpy.data.objects.new('Crown_Dome_Segment',me);COL.objects.link(o);o.parent=top
 for p in me.polygons:p.use_smooth=True
 cube('Crown_Bearing_Block',(.03,.10,.047),'Steel',top,(.192-R0,0,HEIGHT+.018),.008)
 bolt('Crown_Radial_Fastener',top,(.214-R0,0,HEIGHT+.021),(1,0,0),.020)

# Gimbal rims are layered, with index marks and rolling bearing cartridges.
for idx,(g,r) in enumerate([(G1,.70),(G2,.54),(G3,.39)]):
 pg=bpy.data.objects['P_Gimbal_%d_Ring'%idx]
 for side in [-1,1]:
  torus('Gyro_Perimeter_Witness',r+side*.030,.0035,'Black',pg,rot=(math.pi/2,0,0))
 for j in range(48):
  a=j*math.tau/48;pos=Vector((r*math.cos(a),-.023,r*math.sin(a)))
  if j%4==0:bolt('Gyro_Flush_Screw',pg,pos,(0,-1,0),.008)
  else:
   rr0=r-.018;rr1=r+(.005 if j%2 else .017)
   beam('Gyro_Etched_Index',(rr0*math.cos(a),-.019,rr0*math.sin(a)),(rr1*math.cos(a),-.019,rr1*math.sin(a)),.0015,'Black',pg)
 for side in [-1,1]:
  cyl('Gyro_Bearing_Cartridge',.065,.022,'Steel',pg,(side*r,0,0),rot=(0,math.pi/2,0))
  bolt('Gyro_Bearing_Hub',pg,(side*(r+.016),0,0),(side,0,0),.026)
stator=bpy.data.objects['P_Lower_Stator']
for j in range(36):
 a=j*math.tau/36;cube('Stator_Cooling_Fin',(.06,.018,.13),'Steel',stator,(.431*math.cos(a),.431*math.sin(a),.785),.002,rot=(0,0,a))
for zz in [.703,.882]:torus('Stator_Fin_Retainer',.459,.006,'Chrome',stator,(0,0,zz))
for j in range(12):
 a=j*math.tau/12;bolt('Stator_Top_Countersink',stator,(.385*math.cos(a),.385*math.sin(a),.912),r=.012)
# Three ceramic and copper valve stacks visible behind the closed egg silhouette.
for j,a in enumerate([math.radians(33),math.radians(79),math.radians(145)]):
 rad=Vector((math.cos(a),math.sin(a),0));stack=part('Thermal_Valve_%d'%j,TURN,rad*1.1+Vector((0,0,.55)),.18,.1)
 base=rad*.71+Vector((0,0,1.05))
 if j==0:
  base=Vector((.89,.10,2.02))
  tube('Raised_Valve_Supply',[(.70,.12,.69),(.86,.15,.83),(.89,.10,1.5),(.89,.10,2.02)],.024,'Steel',stack)
  for z in [1.12,1.46,1.86]:torus('Supply_Pipe_Collar',.034,.007,'Chrome',stack,(.89,.10,z))
 axis=empty('Thermal_Valve_Frame',stack,base)
 cyl('Vacuum_Tube_Base',.08,.12,'Steel',axis)
 for z in [.04,.1,.16,.22]:cyl('Ceramic_Insulator_Disc',.09,.026,'Ivory',axis,(0,0,z))
 cyl('Vacuum_Tube_Shield',.061,.24,'Steel',axis,(0,0,.365));sphere('Vacuum_Tube_Dome',.061,'Chrome',axis,(0,0,.483),(1,1,.75))
 for z in [.28,.44]:torus('Valve_Copper_Clamp',.066,.009,'Brass',axis,(0,0,z))
 beam('Valve_Anode',(0,0,.48),(0,0,.59),.012,'Chrome',axis)
 tube('Valve_Copper_Line',[(0,-.08,.14),(.07,-.13,.14),(.16,-.14,.08),(.19,-.12,-.3)],.009,'Brass',axis)

# Inspection aperture: an actual miniature filament cage with lens and retaining bezel.
win=bpy.data.objects['P_Inspection_Window'];fil=bpy.data.objects['P_Inspection_Filament'];cen=Vector((radius(.52)-R0,0,HEIGHT*.52))
for o in list(win.children):
 if o.name.startswith('Inspection_DarkGlass'):o.data.materials.clear();o.data.materials.append(M['Black'])
for side in [-1,1]:
 beam('Inspection_Gold_Electrode',(cen.x+.013,side*.047,cen.z-.23),(cen.x+.013,side*.047,cen.z+.23),.006,'Brass',fil)
for zz in [-.23,.23]:
 cyl('Filament_Retainer',.039,.022,'Chrome',fil,(cen.x,0,cen.z+zz))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.040);o=finish(bpy.context.object,'Inspection_Sunlet','Core',fil,(cen.x+.007,0,cen.z),smooth=False)
for e in o.data.edges:
 a=Vector(o.data.vertices[e.vertices[0]].co)+o.location;b=Vector(o.data.vertices[e.vertices[1]].co)+o.location;beam('Inspection_Crystal_Cage',a,b,.0025,'Brass',fil)
# Curved dark inset completely fills the aperture, including its rounded ends.
verts=[];faces=[];N=48
for j in range(N+1):
 z=cen.z-.35+.70*j/N;dz=max(0,abs(z-cen.z)-.265);width=math.sqrt(max(0,.092**2-dz**2))
 for side in [-1,1]:verts.append((radius(z/HEIGHT)-R0-.018,side*width,z))
for j in range(N):faces.append((j*2,j*2+1,j*2+3,j*2+2))
me=bpy.data.meshes.new('Inspection_Curved_Recess');me.from_pydata(verts,[],faces);me.materials.append(M['Black']);o=bpy.data.objects.new('Inspection_Curved_Recess',me);COL.objects.link(o);o.parent=win
for po in me.polygons:po.use_smooth=True
print('DETAIL_PASS_READY',len(COL.objects),'components before joining',flush=True)
