"""Isolated I conch volume/anatomy candidate. Never rebuilds the live I or shared base."""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder,smooth
OUT=ROOT/'review/I_refinement/r1';OUT.mkdir(parents=True,exist_ok=True)
owned_source=ROOT/'blender/collection/I_helix_r1.blend'
if owned_source.exists() and (OUT/'build.json').exists():
    expected=json.loads((OUT/'build.json').read_text())['source_sha256']
    assert hashlib.sha256(owned_source.read_bytes()).hexdigest()==expected,'Unrecorded source edits: preserve them and use a new candidate instead of regenerating'
b=Builder('IH1','Helix auditor volume and anatomy candidate')
b.material('HelixPorcelain',(.83,.79,.70),0,.25,normal='ceramic_glaze_normal.png',coat=.48)
b.material('HelixNickel',(.47,.49,.48),.96,.27,rough='metal_roughness.png',normal='metal_normal.png')
b.material('HelixBrass',(.48,.29,.10),.94,.28)
b.material('HelixInk',(.018,.020,.019),0,.32,coat=.18)
b.material('HelixRubber',(.019,.023,.022),0,.52)
b.material('HelixRed',(.28,.012,.008),0,.24,coat=.45)
b.material('HelixDiaphragm',(.33,.35,.33),.93,.26)
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
R=[(0,.90),(.14,.89),(.28,.93),(.43,.85),(.60,.65),(.76,.39),(.9,.18),(1,.055)]
def radius(t):
    for (a,x),(c,y) in zip(R,R[1:]):
        if t<=c:return x+(y-x)*smooth((t-a)/(c-a))
    return R[-1][1]
frames=[];previous_t=tangent(0);normal=(Vector((0,0,1))-previous_t*previous_t.z).normalized()
for i in range(301):
    t=i/300;axis=tangent(t);normal=previous_t.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));previous_t=axis
def axes(t):return frames[min(300,max(0,round(t*300)))]
def ring_point(t,a,r=None):
    n,v=axes(t);rr=radius(t) if r is None else r
    return center(t)+(n*math.cos(a)+v*math.sin(a))*rr
def mesh(name,verts,faces,mat,parent=None,uv=None,bevel=0.):
    o=b.fast['fast_instance'](b.name(name),verts,faces,mat,parent or b.upper,(0,0,0),smooth_faces=True,uv=uv)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    if bevel:
        mod=o.modifiers.new('Machined edge break','BEVEL');mod.width=bevel;mod.segments=3
    return o
def shell(name,lo,hi,angle0,angle1,mat,parent):
    verts=[];faces=[];uv=[];nu=20;nv=40
    # Six body sections; each has a moving front half and fixed rear half.
    for layer in range(2):
        for i in range(nu+1):
            t=lo+(hi-lo)*i/nu
            for j in range(nv+1):
                a=angle0+(angle1-angle0)*j/nv
                rr=radius(t)-layer*max(.008,min(.032,radius(t)*.045))
                rr*=1.+.016*math.sin(a+t*9.)
                verts.append(ring_point(t,a,rr));uv.append((j/nv,i/nu))
    size=(nu+1)*(nv+1)
    for layer in range(2):
        for i in range(nu):
            for j in range(nv):
                k=layer*size+i*(nv+1)+j;face=(k,k+1,k+nv+2,k+nv+1);faces.append(face if layer==0 else face[::-1])
    boundary=list(range(nv+1))+[i*(nv+1)+nv for i in range(1,nu+1)]+[nu*(nv+1)+j for j in range(nv-1,-1,-1)]+[i*(nv+1) for i in range(nu-1,0,-1)]
    for i,k in enumerate(boundary):j=boundary[(i+1)%len(boundary)];faces.append((k,j,j+size,k+size))
    return mesh(name,verts,faces,mat,parent,uv,.003)
fixed=b.empty('IH1_FixedChamber',b.upper);panels=[];guides=[]
b.pedestal_mount(.35)
for a in [-.8,.8]:
    foot=Vector((a*.72,-.30,.73));top=Vector((a*.30,.10,1.46))
    b.joint(fixed,foot,.085);b.beam('LowerSupportBarrel',foot,foot.lerp(top,.65),.082,'HelixNickel',fixed)
    b.beam('LowerSupportRod',foot.lerp(top,.52),top,.039,'HelixNickel',fixed);b.joint(fixed,top,.080)
b.beam('CentralBearingColumn',(.05,.18,.80),(.09,.18,1.38),.13,'HelixNickel',fixed)
b.sphere('CradleHub',.20,'HelixNickel',fixed,(.09,.18,1.40),scale=(1.6,1.2,.7))
# An actual rear housing closes the body rather than leaving an empty center.
for i in range(6):
    lo=i/6+.003;hi=(i+1)/6-.003
    shell('RearPorcelain'+str(i),lo,hi,math.radians(78),math.radians(282),'HelixPorcelain',fixed)
    panel=b.empty('IH1_FrontPanel'+str(i),b.upper);panels.append(panel)
    shell('FrontPorcelain'+str(i),lo,hi,math.radians(-76),math.radians(76),'HelixPorcelain',panel)
    for t in [lo,hi]:
        b.tube('RolledPanelLip',[ring_point(t,math.radians(-76+152*j/48),radius(t)+.003) for j in range(49)],.012,'HelixNickel',panel)
    for a in [math.radians(-72),math.radians(72)]:
        b.tube('SidePanelLip',[ring_point(lo+(hi-lo)*j/28,a,radius(lo+(hi-lo)*j/28)+.003) for j in range(29)],.009,'HelixNickel',panel)
    mid=(lo+hi)/2;n,v=axes(mid)
    opening=n*(.18*(1-.45*mid)*min(1.,radius(mid)/.6))+tangent(mid)*[-.12,-.06,.02,.08,.13,.145][i]
    direction=opening.normalized();panel['open_direction']=list(direction);panel['stroke']=opening.length
    for angle in [-.96,.96]:
        t=mid;a=angle;scale=min(1.,radius(mid)/.6);stroke=panel['stroke'];anchor=ring_point(t,a,radius(t)-.10*scale);axis=direction
        barrel=b.sleeve('GuideBarrel',.026*scale,.015*scale,stroke+.08*scale,'HelixNickel',fixed,anchor-axis*(stroke*.5+.03*scale),32);barrel.rotation_euler=axis.to_track_quat('Z','Y').to_euler();barrel.modifiers[0].width=.001*scale
        rod=b.beam('GuideRod',anchor-axis*(stroke+.045*scale),anchor+axis*.065*scale,.0135*scale,'HelixNickel',panel)
        saddle=ring_point(t,a,radius(t)-.030*scale);b.joint(panel,saddle,.038*scale,axis)
        b.beam('GuideClevis',anchor+axis*.065*scale,saddle,.014*scale,'HelixNickel',panel)
        guides.append({'panel':panel,'anchor':anchor,'axis':axis,'stroke':stroke,'scale':scale,'engagement_open':.055*scale,'barrel_name':barrel.name,'rod_name':rod.name})
        for end in [lo+.02*(hi-lo),hi-.02*(hi-lo)]:
            point=ring_point(end,a,radius(end)+.009);b.screw(panel,point,axis,.012)
# Two continuous metal spines connect the split shells and carry their sliders.
for a in [math.pi/2,-math.pi/2]:
    for shift in [-.032,.032]:b.tube('ChamberSpine',[ring_point(j/160,a+shift,radius(j/160)-.05) for j in range(161)],.025,'HelixNickel',fixed)
# Nested acoustic walls and their real joining ribs.
for i in range(15):
    t=.05+.83*i/14
    b.tube('AcousticChamberRib',[ring_point(t,j*math.tau/96,radius(t)*.66) for j in range(97)],.023,'HelixNickel',fixed)
duct_v=[];duct_f=[];duct_n=120;duct_s=48
for inner in [False,True]:
    for j in range(duct_n+1):
        t=j/duct_n;rr=min(.18,radius(t)*.40)*( .76 if inner else 1.)
        for k in range(duct_s):duct_v.append(ring_point(t,k*math.tau/duct_s,rr))
stride=(duct_n+1)*duct_s
for inner in [0,1]:
    for j in range(duct_n):
        for k in range(duct_s):
            a=inner*stride+j*duct_s+k;b1=inner*stride+j*duct_s+(k+1)%duct_s;face=(a,b1,b1+duct_s,a+duct_s);duct_f.append(face if inner==0 else face[::-1])
for j in [0,duct_n]:
    for k in range(duct_s):a=j*duct_s+k;b1=j*duct_s+(k+1)%duct_s;duct_f.append((a,b1,b1+stride,a+stride))
mesh('HollowAcousticDuct',duct_v,duct_f,'HelixInk',fixed)
for a in [0,math.pi*.66,math.pi*1.33]:
    b.tube('BrassReturnConductor',[ring_point(.04+.87*j/180,a+j/180*math.tau*.7,radius(.04+.87*j/180)*.69) for j in range(181)],.009,'HelixBrass',fixed)

mouth=b.empty('IH1_Mouth',fixed,P[0]);mouth.rotation_mode='QUATERNION'
normal,side=axes(0);mouth.rotation_quaternion=Matrix((-side,normal,tangent(0))).transposed().to_quaternion()
for name,r,inside,depth,z,key in [('OuterLip',.72,.65,.028,-.100,'HelixNickel'),('MouthNeckBridge',.69,.635,.067,-.005,'HelixNickel'),('IrisCarrier',.635,.585,.036,.025,'HelixBrass'),('PerforatedPlateBezel',.598,.558,.028,.11,'HelixNickel'),('DiaphragmSeat',.53,.47,.035,.23,'HelixNickel')]:b.sleeve(name,r,inside,depth,key,mouth,(0,0,z),96)

# The six leaves require a larger internal swept pocket than the visible mouth.
# This pocket is inside the fuller first shell section; the common base is unchanged.
b.sleeve('IrisOuterHousing',.862,.833,.120,'HelixNickel',mouth,(0,0,-.025),128)
b.sleeve('IrisFrontShoulder',.858,.635,.008,'HelixNickel',mouth,(0,0,-.078),128)
b.sleeve('IrisWorkingApertureStop',.707,.49,.014,'HelixNickel',mouth,(0,0,-.103),128)
b.torus('ApertureStopFineEdge',.492,.004,'HelixBrass',mouth,(0,0,-.113))
b.sleeve('LipBridge',.70,.66,.009,'HelixNickel',mouth,(0,0,-.0835),96)
b.torus('ShellSeatSeal',.865,.006,'HelixRubber',mouth,(0,0,.015))
bpy.context.view_layer.update()
for front in [True,False]:
    a0,a1=(math.radians(16),math.radians(164)) if front else (math.radians(168),math.radians(372))
    verts=[];faces=[];ns=64
    hood_profile=[(.652,-.180),(.67,-.193),(.72,-.195),(.80,-.176),(.865,-.142),(.900,-.098),(.903,.018),(.877,.022),(.874,-.094),(.843,-.120),(.786,-.148),(.716,-.164),(.674,-.165),(.662,-.165)]
    for radius,z in hood_profile:
        for j in range(ns+1):
            a=a0+(a1-a0)*j/ns;verts.append(mouth.matrix_local@Vector((radius*math.cos(a),radius*math.sin(a),z)))
    bands=len(hood_profile)
    for band in range(bands):
        for j in range(ns):
            a=band*(ns+1)+j;c=((band+1)%bands)*(ns+1)+j;faces.append((a,a+1,c+1,c))
    faces.extend([tuple(k*(ns+1) for k in range(bands)),tuple(k*(ns+1)+ns for k in range(bands))])
    hood_parent=panels[0] if front else fixed
    mesh('FrontPorcelainHood' if front else 'RearPorcelainHood',verts,faces,'HelixPorcelain',hood_parent,bevel=.004)
    for a in [a0+.06,a1-.06]:
        first=mouth.matrix_local@Vector((.887*math.cos(a),.887*math.sin(a),-.105));last=mouth.matrix_local@Vector((.89*math.cos(a),.89*math.sin(a),.020))
        b.beam('HoodAttachmentStrut',first,last,.016,'HelixNickel',hood_parent)

def perforated_plate():
    verts=[];faces=[]
    for row in range(8):
        ri=.12+row*.054;ro=ri+.054;rm=(ri+ro)/2;count=round(math.tau*rm/.055)
        for cell in range(count):
            a=(cell+.5)*math.tau/count;da=math.pi/count
            outline=[(ri,a-da),(rm,a-da),(ro,a-da),(ro,a),(ro,a+da),(rm,a+da),(ri,a+da),(ri,a)]
            outer=[Vector((rad*math.cos(ang),rad*math.sin(ang),0)) for rad,ang in outline]
            middle=Vector((rm*math.cos(a),rm*math.sin(a),0));hole=[]
            for q in range(8):
                v=(outer[q]-middle).normalized();hole.append(middle+v*.013)
            k=len(verts)
            for z in [.094,.106]:
                for ring in [outer,hole]:verts.extend([(p.x,p.y,z) for p in ring])
            for q in range(8):
                nq=(q+1)%8
                for x,y in [(0,8),(24,16),(16,0),(8,24)]:faces.append((k+x+q,k+x+nq,k+y+nq,k+y+q))
    o=mesh('PerforatedAcousticPlate',verts,faces,'HelixBrass',mouth)
    for polygon in o.data.polygons:polygon.use_smooth=False
    return o
perforated_plate()
leaves=[]
# Design the fully-open blade as the intersection of the allowable swept
# housing disks and an aperture half-plane, then transform it to its closed pose.
# This produces a hexagonal aperture instead of the rejected star-shaped fan.
IRIS_TRAVEL=1.05
profile=[(-1.,-1.),(1.,-1.),(1.,1.),(-1.,1.)]
def clip_polygon(poly,nx,ny,bound):
    result=[]
    for a,c in zip(poly,poly[1:]+poly[:1]):
        da=nx*a[0]+ny*a[1]-bound;dc=nx*c[0]+ny*c[1]-bound
        if da<=1e-10:result.append(a)
        if (da<0)!=(dc<0):
            t=da/(da-dc);result.append((a[0]+(c[0]-a[0])*t,a[1]+(c[1]-a[1])*t))
    return result
profile=clip_polygon(profile,-1,0,-.36)
for step in range(25):
    a=IRIS_TRAVEL*step/24;cx=.6-.6*math.cos(a);cy=.6*math.sin(a)
    for j in range(96):
        angle=j*math.tau/96;nx=math.cos(angle);ny=math.sin(angle)
        profile=clip_polygon(profile,nx,ny,.83*math.cos(math.pi/96)+nx*cx+ny*cy)
profile=[(.6+(x-.6)*math.cos(IRIS_TRAVEL)-y*math.sin(IRIS_TRAVEL),(x-.6)*math.sin(IRIS_TRAVEL)+y*math.cos(IRIS_TRAVEL)) for x,y in profile]
assert len(profile)>8
for i in range(6):
    angle=i*math.tau/6;leaf=b.empty('IH1_IrisLeaf'+str(i),mouth,(.6*math.cos(angle),.6*math.sin(angle),-.060-i*.0025));leaf.rotation_euler.z=angle;leaf['home_angle']=angle;leaves.append(leaf)
    n=len(profile);vs=[(x-.6,y,z) for z in [-.0006,.0006] for x,y in profile];fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    fs.extend((j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n));blade=mesh('IrisLeafSheet',vs,fs,'HelixNickel',leaf)
    cutter=b.cyl('IrisBoreTool',.0095,.03,'HelixInk',leaf,(0,0,0),None,32);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=blade
    mod=blade.modifiers.new('Actual pivot bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    for polygon in blade.data.polygons:polygon.use_smooth=False
    eye=b.sleeve('LeafPivotEye',.018,.0095,.004,'HelixNickel',leaf,(0,0,.003),32);eye.modifiers[0].width=.0004
    b.cyl('IrisPivotPin',.009,.145,'HelixNickel',mouth,(.6*math.cos(angle),.6*math.sin(angle),-.020),None,32)
    b.sphere('IrisPivotWitness',.013,'HelixRed',mouth,(.6*math.cos(angle),.6*math.sin(angle),-.095),scale=(1,1,.35))
cam_drive=b.empty('IH1_IrisCamDrive',mouth,(0,0,.060))
cam_ring=b.sleeve('IrisCamRing',.745,.638,.012,'HelixNickel',cam_drive,(0,0,0),128)
for modifier in list(cam_ring.modifiers):cam_ring.modifiers.remove(modifier)
for i,leaf in enumerate(leaves):
    angle=i*math.tau/6;path=[]
    for j in range(49):
        amount=-.04+1.08*j/48;phi=-IRIS_TRAVEL*amount
        x=.6+.05*math.cos(phi)-.09*math.sin(phi);y=.05*math.sin(phi)+.09*math.cos(phi)
        a=angle+.30*amount;path.append((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0.))
    cutter=b.tube('CamSlotTool',path,.0105,'HelixNickel',cam_drive,3);cutter.data.use_fill_caps=True
    bpy.ops.object.select_all(action='DESELECT');cutter.select_set(True);bpy.context.view_layer.objects.active=cutter;bpy.ops.object.convert(target='MESH');cutter=bpy.context.view_layer.objects.active
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=cam_ring
    mod=cam_ring.modifiers.new('Follower slot '+str(i),'BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    for amount in [0.,1.]:
        phi=-IRIS_TRAVEL*amount;x=.6+.05*math.cos(phi)-.09*math.sin(phi);y=.05*math.sin(phi)+.09*math.cos(phi);a=angle+.30*amount
        point=(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0.)
        cutter=b.sphere('CamSlotRoundedEnd',.0115,'HelixNickel',cam_drive,point)
        bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter.data);bm.free()
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=cam_ring
        mod=cam_ring.modifiers.new('Rounded slot end','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    length=.070-leaf.location.z
    follower=b.cyl('IrisCamFollower',.0075,length,'HelixNickel',leaf,(.05,.09,length*.5),None,32)
    leaf['cam_follower']=follower.name;leaf['iris_travel']=IRIS_TRAVEL
    a=angle+.5*math.pi/3
    b.beam('IrisCarrierSpoke',(.625*math.cos(a),.625*math.sin(a),.027),(.85*math.cos(a),.85*math.sin(a),.027),.012,'HelixNickel',mouth)
mod=cam_ring.modifiers.new('Slot edge radius','BEVEL');mod.width=.0003;mod.segments=2
b.sleeve('CamRearSupport',.862,.63,.018,'HelixNickel',mouth,(0,0,.102),128)
for i in range(6):
    a=i*math.tau/6+.22
    b.cyl('CamBearingRoller',.009,.016,'HelixNickel',mouth,(.754*math.cos(a),.754*math.sin(a),.060),None,32)
    b.cyl('CamBearingPin',.004,.060,'HelixNickel',mouth,(.754*math.cos(a),.754*math.sin(a),.082),None,24)
    b.cyl('CamCaseStandoff',.018,.075,'HelixNickel',mouth,(.85*math.cos(a),.85*math.sin(a),.065),None,32)
diaphragm=b.empty('IH1_Diaphragm',mouth,(0,0,.235));b.sphere('DomedDiaphragm',.46,'HelixDiaphragm',diaphragm,(0,0,0),scale=(1,1,.07))
b.cyl('DiaphragmHub',.095,.09,'HelixNickel',mouth,(0,0,.03),None,64)
for i in range(3):
    a=i*math.tau/3
    b.coil(diaphragm,(.35*math.cos(a),.35*math.sin(a),.045),.027,.085,7)
    b.cyl('RubyCalibrationPin',.011,.12,'HelixRed',mouth,(.13*math.cos(a),.13*math.sin(a),-.04),None,24)
# Rear pressure reservoir, with actual folded wall geometry and bearing end caps.
t=.68;bell=b.empty('IH1_Bellows',fixed,center(t));bell.rotation_euler=tangent(t).to_track_quat('Z','Y').to_euler()
verts=[];faces=[]
for j in range(49):
    z=-.22+.44*j/48;rr=.225+.035*(.5+.5*math.cos(j*math.pi/3))
    for k in range(64):verts.append((rr*math.cos(k*math.tau/64),rr*math.sin(k*math.tau/64),z))
for j in range(48):
    for k in range(64):a=j*64+k;faces.append((a,j*64+(k+1)%64,(j+1)*64+(k+1)%64,a+64))
bellows_wall=mesh('BellowsFoldedWall',verts,faces,'HelixRubber',bell)
wall=bellows_wall.modifiers.new('Bellows wall thickness','SOLIDIFY');wall.thickness=.012;wall.offset=-1.
for z in [-.23,.23]:b.sleeve('BellowsFlange',.275,.18,.035,'HelixNickel',bell,(0,0,z),64)
tip=b.empty('IH1_Apex',fixed,center(1));tip.rotation_euler=tangent(1).to_track_quat('Z','Y').to_euler()
b.sleeve('ApexCollar',.073,.045,.04,'HelixNickel',tip);b.sphere('RubyTip',.035,'HelixRed',tip,(0,0,.075))

def apply_open(amount):
    for panel in panels:panel.location=Vector(panel['open_direction'])*float(panel['stroke'])*amount
    for leaf in leaves:leaf.rotation_euler.z=leaf['home_angle']-IRIS_TRAVEL*amount
    cam_drive.rotation_euler.z=-.30*amount
for frame,amount in [(1,0.),(31,0.),(79,1.),(109,1.),(157,0.)]:
    apply_open(amount)
    for panel in panels:panel.keyframe_insert('location',frame=frame)
    for leaf in leaves:leaf.keyframe_insert('rotation_euler',frame=frame)
    cam_drive.keyframe_insert('rotation_euler',frame=frame)
b.upper.rotation_euler.z=-.35
apply_open(0.);b.scene.frame_start=1;b.scene.frame_end=157;b.scene.frame_set(1)
# Normalize every authored solid, including utility spheres, before export.
seen=set()
for obj in b.col.all_objects:
    if obj.type!='MESH' or obj.data.as_pointer() in seen:continue
    seen.add(obj.data.as_pointer());bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
# This component export is an isolated layout/anatomy artifact, not the live I.
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
component=ROOT/'app/assets/collection/components/I_helix_r1.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_yup=True)
b.reference_scene();b.scene.frame_end=157;b.scene.frame_set(1)
source=ROOT/'blender/collection/I_helix_r1.blend'
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(source.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(source))
for frame,label in [(1,'closed'),(79,'open')]:
    b.scene.frame_set(frame);b.scene.render.resolution_x=1200;b.scene.render.resolution_y=1050;b.scene.cycles.samples=24;b.scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
(OUT/'guide_manifest.json').write_text(json.dumps([{'barrel':g['barrel_name'],'rod':g['rod_name'],'panel':g['panel'].name,'axis':list(g['axis']),'stroke':g['stroke'],'scale':g['scale']} for g in guides],indent=2)+'\n')
report={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'component':str(component.relative_to(ROOT)),'moving_panels':len(panels),'iris_leaves':len(leaves),'minimum_guide_engagement':min(g['engagement_open'] for g in guides),'rear_halves':6,'guide_pairs':len(guides)//2,'section_interpretation':'Six conch body sections, each split into a moving front cover and a fixed rear cover; source image does not fully constrain the hidden back.','scope':'First isolated volume/anatomy candidate with actual perforated plate, diaphragm and bellows. Iris cam assembly clearance, complete kinematic closure, collisions, custom console and VFX runtime remain; not promoted to I or AAA.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_HELIX_R1',json.dumps(report),flush=True)
