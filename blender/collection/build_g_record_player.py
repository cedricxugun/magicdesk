"""Six-media record player, built to the chosen constant-size / same-disc print
design. Reuses only the six authored curiosities; no book structure is retained.
All positions are Blender Z-up. Runtime metadata is converted to Godot Y-up.
"""
import bpy,bmesh,math,json,pathlib,sys
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder,C,pose
from optimize_runtime_meshes import optimize
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_curiosities.blend'))
old=json.loads((ROOT/'blender/collection/G_curiosities.json').read_text(encoding='utf-8'))
catalog=old['contents'];keep=set()
for item in catalog:
    node=bpy.data.objects[item['root']];keep.update([node]+list(node.children_recursive));node.parent=None;node.matrix_world=Matrix.Identity(4)
for node in list(bpy.data.objects):
    if node not in keep:bpy.data.objects.remove(node,do_unlink=True)
scene=bpy.context.scene;scene.name='G_Record_Player';scene.frame_set(1)
b=Builder.__new__(Builder);b.id='GR';b.title='Sixfold archive player';b.scene=scene
b.col=bpy.data.collections.new('MODULE_GR');scene.collection.children.link(b.col)
for node in keep:
    for col in list(node.users_collection):col.objects.unlink(node)
    b.col.objects.link(node);node.animation_data_clear();node.hide_render=False;node.hide_viewport=False
b.parts=[];b.controls=[];b.motions=[];b.sockets={};b.qa_shells=[];b.extra={};b.serial=60000
b.mats={m.name.removeprefix('Collection_'):m for m in bpy.data.materials if m.name.startswith('Collection_')}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats};exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
b.root=b.empty('GR_MODULE');b.upper=b.empty('GR_UPPER',b.root)
b.material('PlayerPorcelain',(.86,.81,.70),0,.19,coat=.55)
b.material('PlayerGold',(.82,.55,.20),.98,.215)
b.material('PlayerNickel',(.47,.50,.51),.96,.26)
b.material('RecordBlack',(.007,.009,.011),.32,.25,coat=.32)
b.material('RecordGroove',(.018,.021,.023),.70,.21)
b.material('PlayerRubber',(.012,.014,.013),.02,.61)
b.material('PlayerRuby',(.32,.013,.008),.3,.16,coat=.65)
b.material('PlayerSignal',(1,.31,.065),.1,.22,emission=2)
front=(math.pi/2,0,0)
def bezier(a,c,d,e,steps=32):
    a,c,d,e=map(Vector,[a,c,d,e]);return [tuple((1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*e) for t in [i/steps for i in range(steps+1)]]
def revolve(name,profile,key,parent,loc=(0,0,0),n=80):
    verts=[];faces=[];uv=[]
    for j,(z,rx,ry) in enumerate(profile):
        for i in range(n):
            a=i*math.tau/n;verts.append((rx*math.cos(a),ry*math.sin(a),z));uv.append((i/n,j/max(1,len(profile)-1)))
    for j in range(len(profile)-1):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))])
    return b.fast['fast_instance'](b.name(name),verts,faces,key,parent,loc,smooth_faces=True,uv=uv)
def bone(parent,name,length,radius,key='PlayerPorcelain'):
    n=64;steps=28;verts=[];faces=[];uv=[]
    padding=min(.055,length*.16)
    for j in range(steps+1):
        t=j/steps;z=padding+(length-padding*2)*t;cx=radius*.25*math.sin(math.pi*t)
        profile=radius*(.70+.30*math.sin(math.pi*t)**.65)
        for i in range(n):
            a=i*math.tau/n;verts.append((cx+profile*math.cos(a),profile*.85*math.sin(a),z));uv.append((i/n,t))
    for j in range(steps):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces.extend([tuple(range(n-1,-1,-1)),tuple(steps*n+i for i in range(n))])
    b.fast['fast_instance'](b.name(name),verts,faces,key,parent,(0,0,0),smooth_faces=True,uv=uv)
    b.cyl('BoneInnerLink',radius*.44,length,'PlayerGold',parent,(0,0,length*.5),n=32)
    for z in [padding+.006,length-padding-.006]:b.torus('BoneGildedCuff',radius*.77,min(.007,radius*.25),'PlayerGold',parent,(0,0,z))
    b.tube('BoneServiceConduit',[(radius*.81,-radius*.51,.04),(radius*1.04,-radius*.55,length*.27),(radius*.95,-radius*.56,length*.74),(radius*.76,-radius*.51,length-.03)],.006,'Black',parent)
def joint(parent,loc,radius=.095):
    b.cyl('JointCore',radius,.19,'PlayerNickel',parent,loc,(0,math.pi/2,0),64)
    for side in [-1,1]:
        p=Vector(loc)+Vector((side*.101,0,0));b.cyl('GoldJointCheek',radius*.94,.024,'PlayerGold',parent,p,(0,math.pi/2,0),64)
        p+=Vector((side*.016,0,0));b.cyl('RubyTorqueInsert',radius*.62,.008,'PlayerRuby',parent,p,(0,math.pi/2,0),56)
        b.torus('JointRim',radius*.72,.005,'PlayerNickel',parent,p,(0,math.pi/2,0))
        b.cyl('JointFastener',radius*.20,.014,'PlayerGold',parent,p+Vector((side*.005,0,0)),(0,math.pi/2,0),12)
def label(parent,text,loc,size=.045):
    curve=bpy.data.curves.new(b.name('MediaLabel'),'FONT');curve.body=text;curve.align_x='CENTER';curve.align_y='CENTER';curve.size=size;curve.extrude=.0005
    obj=bpy.data.objects.new(curve.name,curve);b.col.objects.link(obj);obj.parent=parent;obj.location=loc;curve.materials.append(b.mats['PlayerRuby']);return obj
def catmull(control,steps=8):
    values=[Vector(v) for v in control];out=[]
    for k in range(len(values)):
        a,c,d,e=[values[j%len(values)] for j in [k-1,k,k+1,k+2]]
        for i in range(steps):
            t=i/steps;out.append(.5*(2*c+(-a+d)*t+(2*a-5*c+4*d-e)*t*t+(-a+3*c-3*d+e)*t*t*t))
    return out
def ceramic_petal(parent,name,outline,center):
    outline=catmull(outline);center=Vector(center);n=len(outline);rings=12;verts=[];faces=[];uv=[]
    for back in [False,True]:
        for j in range(rings+1):
            t=max(.0001,j/rings)
            for i,p in enumerate(outline):
                v=center.lerp(p,t);v.z-=.017*math.sin(math.pi*t);v.z+=.014 if back else 0
                verts.append(v);uv.append((i/n,t))
    stride=(rings+1)*n
    for side in range(2):
        for j in range(rings):
            for i in range(n):
                a=side*stride+j*n+i;f=(a,side*stride+j*n+(i+1)%n,side*stride+(j+1)*n+(i+1)%n,a+n);faces.append(tuple(reversed(f)) if side else f)
    for i in range(n):faces.append((rings*n+i,rings*n+(i+1)%n,stride+rings*n+(i+1)%n,stride+rings*n+i))
    b.fast['fast_instance'](b.name(name),verts,faces,'PlayerPorcelain',parent,(0,0,0),smooth_faces=True,uv=uv)
    b.tube('PetalRolledLip',[tuple(p) for p in outline+[outline[0]]],.0055,'PlayerGold',parent)

# Fixed anatomical column inside the annular six-slot magazine.
stand=b.part('Stand',(0,0,.65),.85)
revolve('CeramicStand',[(.665,.145,.15),(.70,.19,.19),(.76,.17,.17),(.85,.102,.105),(1.17,.095,.095),(1.41,.081,.082),(1.50,.13,.13),(1.575,.09,.09)],'PlayerPorcelain',stand,(0,.38,0))
for z,r in [(.704,.189),(.775,.146),(1.43,.105),(1.505,.130)]:b.torus('StandGoldCollar',r,.013,'PlayerGold',stand,(0,.38,z))
b.cyl('FrontServoHousing',.123,.052,'PlayerGold',stand,(0,.266,1.11),front,80)
b.cyl('FrontServoRuby',.087,.009,'PlayerRuby',stand,(0,.234,1.11),front,72)
b.torus('FrontServoBrightRing',.101,.008,'PlayerNickel',stand,(0,.230,1.11),front)
b.cyl('FrontServoPin',.023,.010,'PlayerGold',stand,(0,.224,1.11),front,12)
b.torus('ShoulderYawRace',.125,.011,'PlayerGold',stand,(0,.38,1.577))
b.cyl('StandRearMotor',.132,.11,'PlayerNickel',stand,(0,.50,.91),front,64)
b.cyl('StandRubySeal',.090,.011,'PlayerRuby',stand,(0,.565,.91),front,64)
for side in [-1,1]:b.tube('StandVein',bezier((side*.095,.30,.78),(side*.12,.31,1.00),(side*.05,.30,1.27),(side*.055,.32,1.47)),.007,'PlayerGold',stand)

mag_part=b.part('Magazine',(0,0,.25),.70);mag=b.empty('GR_MagazineRotor',mag_part,(0,.44,.815))
b.sleeve('AnnularMagazineChassis',.615,.29,.065,'PlayerNickel',mag,n=96)
for r in [.308,.48,.60]:b.torus('MagazineGoldRail',r,.010,'PlayerGold',mag,(0,0,.035))
for k in range(36):
    a=k*math.tau/36;b.cube('MagazineIndexTooth',(.021,.018,.028),'Black',mag,(.613*math.cos(a),.613*math.sin(a),0),.003,(0,0,a))
cup_names=[];disc_names=[];slot_poses=[]
for i in range(6):
    a=i*math.tau/6;home=Matrix.Translation(Vector((.52*math.sin(a),.44-.52*math.cos(a),1.18)))@Matrix.Rotation(a,4,'Z')@Matrix.Rotation(math.pi/3,4,'X')
    cp=b.part('Cradle'+str(i),(.42*math.sin(a),-.42*math.cos(a),.50),.20)
    cup=b.empty('GR_Cradle'+str(i),cp);cup.matrix_basis=home;cup_names.append(cup.name);slot_poses.append(pose(home))
    ceramic_petal(cup,'CupLowerPetal',[(-.19,-.19,-.045),(-.15,-.31,-.045),(0,-.345,-.035),(.15,-.31,-.045),(.19,-.19,-.045),(.12,-.155,-.065),(-.12,-.155,-.065)],(0,-.25,-.052))
    for side in [-1,1]:
        ceramic_petal(cup,'CupSidePetal',[(side*.19,-.25,-.044),(side*.285,-.15,-.012),(side*.30,-.02,-.025),(side*.251,.075,-.043),(side*.211,.015,-.056),(side*.18,-.12,-.061)],(side*.244,-.105,-.050))
    b.beam('CradleFoot',(0,-.2858,-.165),(0,-.235,-.060),.025,'PlayerGold',cup)
    b.cyl('CradleFootPin',.039,.085,'PlayerNickel',cup,(0,-.240,-.075),(0,math.pi/2,0),40)
    b.cube('CradleRubberRest',(.12,.047,.016),'PlayerRubber',cup,(0,-.218,-.014),.012)
    dp=b.part('Record'+str(i),(.66*math.sin(a),-.66*math.cos(a),.80),.05)
    disc=b.empty('GR_Record'+str(i),dp);disc.matrix_basis=home;disc_names.append(disc.name)
    face=b.cyl('OpticalMediaSubstrate',.246,.014,'RecordBlack',disc,n=160)
    for poly in face.data.polygons:
        if abs(poly.normal.z)>.9:
            for li in poly.loop_indices:
                vertex=face.data.vertices[face.data.loops[li].vertex_index].co;face.data.uv_layers.active.data[li].uv=(vertex.x/.492+.5,vertex.y/.492+.5)
    for radius in [.061,.102,.143,.184,.230]:b.torus('MasteredGroove',radius,.0008,'RecordGroove',disc,(0,0,.0078))
    b.tube('ScallopedGoldMediaEdge',[(math.cos(t)*(.250+.0035*math.cos(t*36)),math.sin(t)*(.250+.0035*math.cos(t*36)),0) for t in [j*math.tau/360 for j in range(361)]],.0068,'PlayerGold',disc)
    b.cyl('RecordIvoryLabel',.050,.003,'PlayerPorcelain',disc,(0,0,.0095),n=64);label(disc,str(i+1),(0,0,.0115),.046)
    b.cyl('MediaSpindleCentre',.009,.005,'PlayerGold',disc,(0,0,.013),n=32)
    b.cube('MediaTabStem',(.025,.068,.012),'PlayerGold',disc,(0,.263,0),.008)
    b.cyl('MediaNumberTab',.034,.014,'PlayerGold',disc,(0,.302,0),n=56)
    b.cyl('MediaNumberEnamel',.028,.003,'PlayerPorcelain',disc,(0,.302,.009),n=56);label(disc,str(i+1),(0,.302,.012),.042)

# Two exact-length links and an orientation-controlled wrist. The large joints
# carry torque; the white links are formed solid shells, not cylinder proxies.
upper_part=b.part('UpperArm',(-.35,.20,.48),.55);upper=b.empty('GR_UpperArm',upper_part);joint(upper,(0,0,0),.105);bone(upper,'UpperPorcelainLink',.62,.078)
fore_part=b.part('Forearm',(.35,.10,.76),.42);fore=b.empty('GR_Forearm',fore_part);joint(fore,(0,0,0),.087);bone(fore,'ForearmPorcelainLink',.68,.072)
wrist_part=b.part('Wrist',(0,-.25,.99),.15);wrist=b.empty('GR_Wrist',wrist_part)
revolve('WristMotor',[(0,.045,.045),(.023,.060,.060),(.046,.060,.060),(.080,.046,.046)],'PlayerGold',wrist)
b.torus('WristMotorSeal',.061,.004,'PlayerRuby',wrist,(0,0,.025));b.cyl('WristCap',.045,.016,'PlayerPorcelain',wrist,(0,0,.081),n=56)
b.cyl('WristCouplingNeck',.029,.075,'PlayerNickel',wrist,(0,0,.100),n=48)
b.sphere('WristUniversalCoupling',.041,'PlayerGold',wrist,(0,0,.12))
finger_rigs=[]
for i in range(3):
    a=math.radians(30)+i*math.tau/3
    first=b.empty('GR_Finger%dA'%i,wrist);second=b.empty('GR_Finger%dB'%i,wrist)
    bone(first,'GoldProximalFinger',.185,.014,'PlayerGold');bone(second,'GoldDistalFinger',.145,.012,'PlayerGold')
    b.sphere('FingerKnuckle',.019,'PlayerNickel',first);b.sphere('FingerKnuckle',.017,'PlayerNickel',second)
    pad=b.empty('GR_Finger%dPad'%i,wrist);b.sphere('RimGripPad',.009,'PlayerRubber',pad,scale=(1.0,1.6,1.0));b.torus('PadGoldCollar',.010,.002,'PlayerGold',pad)
    finger_rigs.append({'proximal':first.name,'distal':second.name,'pad':pad.name,'angle':a})

# Distinct small reader (0.80 m), on the front of the authoritative 2.74 m base.
platter_part=b.part('ReaderPlatter',(0,-.50,.25),.4)
revolve('SmallReaderHousing',[(.73,.31,.31),(.752,.39,.39),(.80,.414,.414),(.835,.414,.414),(.87,.382,.382)],'PlayerNickel',platter_part,(0,-.72,0))
for z,r in [(.766,.396),(.840,.413),(.873,.384)]:b.torus('SmallReaderGoldLip',r,.010,'PlayerGold',platter_part,(0,-.72,z))
platter=b.empty('GR_PlatterPivot',platter_part,(0,-.72,.884))
b.cyl('SmallPlatterMat',.37,.012,'PlayerRubber',platter,n=120)
b.torus('PlatterEdgeHighlight',.366,.003,'PlayerNickel',platter,(0,0,.007))
print_root=b.empty('GR_PrintRoot',platter,(0,0,.022))
for item in catalog:
    node=bpy.data.objects[item['root']];node.parent=print_root;node.matrix_basis=Matrix.Identity(4)

tone_base=b.part('ToneLiftBase',(.43,-.12,.24),.45)
socket=revolve('TonearmLiftSocket',[(.69,.071,.071),(.724,.078,.078),(.83,.052,.052),(.935,.050,.050)],'PlayerGold',tone_base,(.58,-.60,0))
cutter=b.cyl('TemporaryToneBore',.030,.29,'Black',tone_base,(.58,-.60,.87),n=64);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=socket
modifier=socket.modifiers.new('Actual lift piston bore','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter;bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
b.cyl('ToneLiftRubyBand',.054,.033,'PlayerRuby',tone_base,(.58,-.60,.85),n=56)
tone_part=b.part('OpticalTonearm',(.38,-.15,.60),.2);tone=b.empty('GR_Tonearm',tone_part,(.58,-.60,1.10))
b.cyl('TonearmLiftPiston',.027,.20,'PlayerNickel',tone,(0,0,-.09),n=48)
path=bezier((0,0,0),(.16,.065,.020),(.40,.045,.025),(.52,0,.030),48)
b.ribbon('CeramicTonearm',path,[.028-.010*i/48 for i in range(49)],.022,'PlayerPorcelain',tone)
b.tube('TonearmGoldUnderside',[(x,y,z-.022) for x,y,z in path],.0045,'PlayerGold',tone)
b.cyl('OpticalHead',.041,.09,'PlayerGold',tone,(.515,0,.031),(0,math.pi/2,0),64)
b.cyl('RubyOptic',.030,.010,'PlayerRuby',tone,(.565,0,.031),(0,math.pi/2,0),56)
b.torus('OpticRim',.034,.004,'PlayerNickel',tone,(.572,0,.031),(0,math.pi/2,0))
b.sphere('ScanAperture',.006,'PlayerSignal',tone,(.52,0,-.029))
needle=b.empty('GR_ScanPoint',tone,(.52,0,-.029))

def aim(node,a,c):
    a=Vector(a);v=(Vector(c)-a).normalized();x=Vector((1,0,0)) if abs(v.x)<.001 else Vector((-v.y,v.x,0)).normalized();y=v.cross(x).normalized();x=y.cross(v).normalized();node.matrix_basis=Matrix(((x.x,y.x,v.x,a.x),(x.y,y.y,v.y,a.y),(x.z,y.z,v.z,a.z),(0,0,0,1)))
def arm(tcp):
    S=Vector((0,.38,1.58));W=Vector(tcp);horizontal=Vector((W.x-S.x,W.y-S.y,0));distance=horizontal.length;direction=horizontal.normalized();height=W.z-S.z;co=max(-1,min(1,(distance*distance+height*height-.62**2-.68**2)/(2*.62*.68)));q2=-math.acos(co);q1=math.atan2(height,distance)-math.atan2(.68*math.sin(q2),.62+.68*math.cos(q2));E=S+direction*(.62*math.cos(q1))+Vector((0,0,.62*math.sin(q1)));aim(upper,S,E);aim(fore,E,W);wrist.location=W
arm((.44,.30,2.22));wrist.location.z-=.12
for f in finger_rigs:
    a=f['angle'];radial=Vector((math.cos(a),math.sin(a),0));x=.31-.04;z=-.17;co=max(-1,min(1,(x*x+z*z-.185**2-.145**2)/(2*.185*.145)));q2=-math.acos(co);q1=math.atan2(z,x)-math.atan2(.145*math.sin(q2),.185+.145*math.cos(q2));A=radial*.04;E=A+radial*(.185*math.cos(q1))+Vector((0,0,.185*math.sin(q1)));T=radial*.31+Vector((0,0,-.17));aim(bpy.data.objects[f['proximal']],A,E);aim(bpy.data.objects[f['distal']],E,T);bpy.data.objects[f['pad']].location=T

parts=[{'name':p['obj'].name,'home':pose(p['obj'].matrix_basis),'offset':p['offset'],'stage':p['stage']} for p in b.parts]
metadata={'id':'G','title':'六瓣换片机','root':b.root.name,'upper':b.upper.name,'parts':parts,'controls':[],'motions':[],'sockets':{},'qa_shells':[],'part_count':len(parts),'base_diameter':2.74,'includes_base':False,'source_blend':'blender/collection/G_record_player.blend','display_calibration':{'scale':1.0,'fixed_mount_height':.615,'base_scaled':False},'g_archive':{'contents':catalog,'specimen_scale':1.0},'record_player':{'magazine':mag.name,'cradles':cup_names,'records':disc_names,'slots':slot_poses,'upper_arm':upper.name,'forearm':fore.name,'wrist':wrist.name,'fingers':finger_rigs,'platter':platter.name,'print_root':print_root.name,'tonearm':tone.name,'scan_point':needle.name,'shoulder':[0,1.58,-.38],'lengths':[.62,.68],'record_radius':.25,'record_thickness':.014,'platter_origin':[0,.884,.72],'disc_height':.014,'magazine_origin':[0,.815,-.44],'tone_origin':[.58,.94,.60],'tone_length':.52,'source_atlas':'res://assets/collection/art/G/optical_atlas.png','seconds_per_turn':60,'grip_offset':.15,'design':'production/G_record_player/images/G_print_sequence.png'}}
seen=set()
for obj in b.col.all_objects:
    if obj.type=='MESH' and obj.data.as_pointer() not in seen:
        seen.add(obj.data.as_pointer());bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
out=ROOT/'app/assets/collection/models/G_record_player.glb';out.with_suffix('.json').write_text(json.dumps(metadata,separators=(',',':')),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
b.reference_scene()
for item in catalog:
    node=bpy.data.objects[item['root']]
    for child in [node]+list(node.children_recursive):child.hide_render=True;child.hide_set(True)
# Reference cassette uses the actual shared replacement plate and control library.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/frame_shared.glb'));added=set(bpy.data.objects)-before;surface=next(o for o in added if o.type=='MESH');base=bpy.data.objects.get('BASE_FIXED_DisplayMesh')
if base:base.data=surface.data.copy();base.matrix_world=surface.matrix_world
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
for i in range(1,6):
    mount=bpy.data.objects.get('BUTTON_%02d_MOUNT'%i)
    if mount:
        for obj in [mount]+list(mount.children_recursive):obj.hide_render=True;obj.hide_set(True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/record_controls.glb'));added=set(bpy.data.objects)-before
for slot,kind in enumerate(['rotary','slider_x','hold','detent','service'],1):
    obj=next(o for o in added if o.name=='GCTRL_'+kind);mount=bpy.data.objects['BUTTON_%02d_MOUNT'%slot];obj.parent=None;obj.location=mount.matrix_world.translation;obj.rotation_euler=(0,0,math.atan2(obj.location.y,obj.location.x)+math.pi/2)
    for child in [obj]+list(obj.children_recursive):added.discard(child)
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
scene.render.fps=30;scene.frame_end=1800;scene.timeline_markers.clear();scene.timeline_markers.new('Record-player mechanism awaiting runtime bake',frame=1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/metadata['source_blend']));optimize(out)
print('RECORD_PLAYER_BUILT',len(parts),'parts; six persistent .50 media; separate .80 reader',flush=True)
