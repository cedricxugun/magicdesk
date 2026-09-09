"""G archive player: new sibling source, sealed media, real closing case,
front exhibition carriage and six individually rigged mechanical specimens."""
import bpy,bmesh,math,json,pathlib,sys
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder,C,pose,window
from optimize_runtime_meshes import optimize
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_complete.blend'))
scene=bpy.context.scene;scene.frame_set(1)
data=json.loads((ROOT/'app/assets/collection/models/G_complete.json').read_text(encoding='utf-8'))
b=Builder.__new__(Builder);b.id='G4';b.title='The mechanical archive';b.scene=scene;b.col=bpy.data.collections['MODULE_G3'];b.root=bpy.data.objects[data['root']];b.upper=bpy.data.objects[data['upper']]
b.serial=30000;b.parts=[];b.controls=[];b.motions=[];b.sockets={};b.qa_shells=[];b.extra={}
b.mats={m.name.removeprefix('Collection_'):m for m in bpy.data.materials if m.name.startswith('Collection_')}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
for obj in b.col.all_objects:obj.animation_data_clear()
for col in list(bpy.data.collections):
    if col.name.startswith('G_CAPTURED_OPTICS'):
        for obj in list(col.all_objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(col)
old=bpy.data.objects.get('G3_Relief')
if old:
    for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
if scene.sequence_editor:
    strips=getattr(scene.sequence_editor,'strips',None)
    if strips:
        for s in list(strips):
            if s.name.startswith('G inscription'):strips.remove(s)
front=(math.pi/2,0,0)
b.material('OpticalGlass',(.022,.038,.039),.70,.095,coat=.65)
b.material('ArchiveGold',(.82,.55,.20),.98,.215)
b.material('RubyGlow',(.42,.021,.007),.28,.14,coat=.65,emission=1.8)
for obj in list(b.col.all_objects):
    if obj.type=='MESH' and any(k in obj.name for k in ['SpineBearing','CoverBrightEdge','CoverBoreStep','CoverBorePolish','ApertureBarrel']):
        obj.data=obj.data.copy()
        for i in range(len(obj.data.materials)):obj.data.materials[i]=b.mats['ArchiveGold']

def receiver(parent,label,side):
    # Opaque sealed substrate plus convex smoked lens. It is no longer a hole.
    b.cyl(label+'Back',.123,.025,'Black',parent,(.47,0,-.09),front,64)
    b.sphere(label+'Lens',.119,'OpticalGlass',parent,(.47,-side*.020,-.09),(1,.22,1))
    for radius in [.047,.084,.108]:b.torus('EncodedReceiverTrack',radius,.0016,'ArchiveGold',parent,(.47,-side*.048,-.09),front)
    for i in range(24):
        a=i*math.tau/24;r=.099
        b.cyl('CodeBit',.0027,.0015,'Nickel' if i%3 else 'Red',parent,(.47+r*math.cos(a),-side*.048,-.09+r*math.sin(a)),front,8)
    dot=b.empty(label+'ReadPoint',parent,(.47,-side*.054,-.09))
    b.sphere('ReadingContact',.009,'Signal',dot,scale=(1,.35,1));return dot.name

receivers=[]
for leaf in data['g_mechanism']['leaves']:receivers.append(receiver(bpy.data.objects[leaf['face']],'G4_Receiver'+str(leaf['index']),leaf['side']))
for side in [-1,1]:
    face=bpy.data.objects['G3_CoverFace'+str(side)];receiver(face,'CoverReceiver'+str(side),side)
    # Extend both covers across the formerly exposed spine gap; a 10 mm centre
    # seam remains for the lock, instead of a 430 mm apparent opening.
    b.cube('SpineClosureLeaf',(.215,.070,1.64),'Porcelain',face,(-.075,0,0),.023)
    b.beam('SpineClosureRim',(-.178,-side*.043,-.74),(-.178,-side*.043,.74),.006,'Nickel',face)
    lock=b.empty('G4_Lock'+str(side),face,(-.13,-side*.065,-.43))
    b.cube('ArchiveLatch',(.085,.034,.17),'Red',lock,bevel=.013)
    b.screw(lock,(0,-side*.024,.047),(0,-side,0),.010)
    data.setdefault('g_archive_locks',[]).append({'name':lock.name,'side':side,'home':pose(lock.matrix_basis)})

case_nodes=[]
back=b.part('BackCase',(0,.80,.20),.40)
def back_pose(o,t):o.location=(0,.43+.22*window(t,.06,.30),1.79)
back_node=b.control('BackCase',back,back_pose);b.cube('ClosedBookBack',(2.22,.045,1.68),'Satin',back_node,bevel=.025)
case_nodes.append(back_node.name)
for side in [-1,1]:
    part=b.part('CaseSide'+str(side),(side*.75,.28,.10),.35)
    def side_pose(o,t,s=side):o.location=(s*(1.125+.25*window(t,.06,.30)),.21*window(t,.06,.30),1.79)
    node=b.control('CaseSide'+str(side),part,side_pose)
    b.cube('ClosedBookSide',(.045,.88,1.67),'Porcelain',node,bevel=.017)
    roof=b.cube('ClosingRoofHalf',(1.125,.88,.041),'Porcelain',node,(-side*.5625,0,.844),.012)
    cutter=b.cyl('TemporarySpindleClearance',.18,.22,'Black',node,(-side*1.125,0,.844),n=72)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=roof
    modifier=roof.modifiers.new('Spine collar clearance','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
    b.beam('RoofGoldEdge',(-side*1.08,-.435,.85),(0,-.435,.85),.007,'ArchiveGold',node)
    for z in [-.74,.74]:b.beam('BindingBrightEdge',(0,-.39,z),(0,.40,z),.008,'Nickel',node)
    case_nodes.append(node.name)

platter_part=b.part('ExhibitionCarriage',(0,-.62,.38),.50)
lift=b.empty('G4_PlatterLift',platter_part)
slide=b.empty('G4_PlatterSlide',lift)
platform=b.empty('G4_Platter',slide,(0,-.28,.82))
b.cyl('ExhibitionWell',.45,.052,'Satin',platform)
b.cyl('MachinedPlatter',.418,.018,'Nickel',platform,(0,0,.035))
for r in [.15,.28,.39,.443]:b.torus('PlatterTooling',r,.008 if r in [.39,.443] else .0035,'ArchiveGold' if r in [.39,.443] else 'Black',platform,(0,0,.047))
b.torus('ProjectionContact',.397,.004,'Signal',platform,(0,0,.048))
for x in [-.26,.26]:
    b.beam('CarriageGuide',(x,-.90,.755),(x,.04,.755),.016,'Nickel',platter_part)
    b.cube('CarriageBearing',(.064,.15,.060),'Satin',slide,(x,-.30,.765),.012)
    b.cyl('PlatterLiftHousing',.038,.17,'Satin',platter_part,(x,-.23,.70),n=32)
    b.cyl('PlatterLiftPiston',.023,.19,'Nickel',lift,(x,-.23,.72),n=32)
exhibition=b.empty('G4_ExhibitRoot',platform,(0,0,.060))
catalog=[]
def item(index,title,parameter,action):
    root=b.empty('G4_Exhibit'+str(index),exhibition)
    d={'id':index,'title':title,'parameter':parameter,'action':action,'root':root.name,'rig':[]};catalog.append(d);return root,d
def rig(d,obj,kind,**extra):d['rig'].append({'name':obj.name,'kind':kind,'home':pose(obj.matrix_basis),**extra});return obj
def gear(parent,name,r,z=0):
    root=b.empty(name,parent,(0,-.038,z));b.cyl('GearWeb',r*.80,.035,'Satin',root,rot=front,n=48)
    for i in range(24):
        a=i*math.tau/24;b.cube('GearTooth',(.030,.040,.035),'ArchiveGold',root,(r*math.cos(a),0,r*math.sin(a)),.003,(0,-a,0))
    b.torus('GearPolishedRim',r*.80,.008,'ArchiveGold',root,(0,-.022,0),front)
    b.cyl('GearHub',r*.19,.057,'Satin',root,rot=front,n=32);return root

# 1: a visible clock movement, two hands and a genuinely pivoting pendulum.
root,d=item(0,'发条钟塔','拨动时针','敲钟')
for x in [-.23,.23]:
    b.beam('ClockPillar',(x,0,.02),(x,0,.69),.026,'ArchiveGold',root)
    for z in [.05,.24,.64]:b.cyl('PillarCollar',.044,.046,'ArchiveGold',root,(x,0,z),n=32)
    b.cube('TowerPorcelainInset',(.055,.067,.29),'Porcelain',root,(x,.007,.33),.012)
b.cube('ClockBridge',(.55,.15,.06),'Porcelain',root,(0,0,.70),.02)
b.tube('TowerPediment',[(-.27,-.08,.70),(-.19,-.08,.74),(0,-.08,.87),(.19,-.08,.74),(.27,-.08,.70)],.010,'ArchiveGold',root)
b.sphere('TowerFinial',.028,'Red',root,(0,0,.858))
b.beam('FinialTip',(0,0,.88),(0,0,.94),.007,'ArchiveGold',root)
b.cube('TowerFoot',(.54,.21,.045),'ArchiveGold',root,(0,0,.026),.012)
face=b.empty('ClockFace',root,(0,-.018,.47))
b.sleeve('ClockDialRim',.239,.197,.044,'ArchiveGold',face).rotation_euler=front
b.sleeve('ClockDial',.198,.130,.023,'Porcelain',face).rotation_euler=front
center_gear=gear(face,'G4_ClockCenterGear',.092);center_gear.location.y=.018;rig(d,center_gear,'gear',ratio=-.45)
for i in range(12):
    a=i*math.tau/12;b.beam('HourTick',(.17*math.sin(a),-.026,.17*math.cos(a)),(.188*math.sin(a),-.026,.188*math.cos(a)),.0035,'Black',face)
for n,length,key in [('Hour',.115,'Red'),('Minute',.175,'Black')]:
    hand=b.empty('G4_Clock'+n,face,(0,-.047,0));b.beam('Hand',(0,0,-.021),(0,0,length),.007 if n=='Hour' else .0045,key,hand);rig(d,hand,n.lower())
for i,(x,z,r) in enumerate([(-.14,.185,.072),(.15,.205,.091)]):
    holder=b.empty('ClockGearHolder'+str(i),root,(x,0,z));rig(d,gear(holder,'G4_ClockGear'+str(i),r),'gear',ratio=(-1 if i else 1)*1.5)
pend=b.empty('G4_ClockPendulum',root,(0,.04,.33));b.beam('PendulumRod',(0,0,0),(0,0,-.24),.008,'Nickel',pend);b.sphere('PendulumBob',.059,'ArchiveGold',pend,(0,0,-.24),(1,.45,1));rig(d,pend,'pendulum')

# 2: four volumetric porcelain wing lobes and metallic structural veins.
root,d=item(1,'瓷翼机械蝶','展开蝶翼','振翅')
b.beam('ButterflyPerch',(0,0,.015),(0,0,.30),.012,'Nickel',root)
for i in range(5):b.sphere('AbdomenSegment',.040-i*.003,'Porcelain' if i%2 else 'Nickel',root,(0,0,.29+i*.051),(.72,.8,1.2))
b.sphere('ButterflyHead',.051,'Red',root,(0,0,.57))
for side in [-1,1]:
    b.tube('Antenna',[(side*.022,0,.60),(side*.040,0,.70),(side*.10,0,.73)],.0035,'Nickel',root)
    b.sphere('AntennaTip',.010,'ArchiveGold',root,(side*.10,0,.73))
    wing=b.empty('G4_ButterflyWing'+str(side),root,(side*.036,0,.46))
    control=[Vector(p) for p in [(.01,.07),(.10,.22),(.29,.32),(.42,.27),(.40,.13),(.26,.025),(.36,-.12),(.27,-.25),(.10,-.22),(.015,-.08)]]
    outline=[]
    for k in range(len(control)):
        p0,p1,p2,p3=[control[j%len(control)] for j in [k-1,k,k+1,k+2]]
        for j in range(5):
            t=j/5;p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);outline.append(tuple(p))
    verts=[(side*x,y,z) for y in [-.011,.011] for x,z in outline];n=len(outline)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=b.fast['fast_instance'](b.name('SculptedWing'),verts,faces,'Porcelain',wing,(0,0,0))
    bevel=obj.modifiers.new('Fired porcelain bevel','BEVEL');bevel.width=.012;bevel.segments=3
    b.tube('WingBorder',[(side*x,-.019,z) for x,z in outline+[outline[0]]],.0075,'ArchiveGold',wing)
    for x,z in control[1:-1]:b.tube('WingVein',[(side*.016,-.022,0),(side*x*.52,-.030,z*.45),(side*x,-.022,z)],.0045,'ArchiveGold',wing,1)
    for x,z in [(.28,.22),(.23,-.16)]:b.sphere('WingEye',.027,'Red',wing,(side*x,-.021,z),(1,.20,.68))
    b.joint(wing,(0,0,0),.033,(0,0,1));rig(d,wing,'wing',side=side)

# 3: solid little vessel, hinged rigid sail and a constrained rocking cradle.
root,d=item(2,'潮汐帆船','调整风帆','起航')
ship=b.empty('G4_ShipCradle',root,(0,0,.12));rig(d,ship,'ship')
b.sphere('PorcelainHull',1,'Porcelain',ship,(0,0,.12),(.40,.135,.090))
b.tube('Gunwale',[(.395*math.cos(i*math.tau/80),.135*math.sin(i*math.tau/80),.15) for i in range(81)],.013,'ArchiveGold',ship)
for x in [-.23,-.075,.08,.23]:
    for side in [-1,1]:
        y=side*.122*math.sqrt(max(.1,1-(x/.40)**2))
        b.cyl('PortholeGlass',.024,.008,'OpticalGlass',ship,(x,y,.115),front,32);b.torus('PortholeGold',.027,.004,'ArchiveGold',ship,(x,y+side*.006,.115),front)
b.cube('Deck',(.55,.18,.018),'Satin',ship,(0,0,.172),.045)
b.beam('Mast',(-.04,0,.16),(-.04,0,.74),.014,'ArchiveGold',ship)
sail=b.empty('G4_Sail',ship,(-.04,0,.49));rig(d,sail,'sail')
verts=[(0,-.005,.23),(.30,-.005,-.19),(0,-.005,-.19),(0,.018,.23),(.30,.055,-.19),(0,.018,-.19)]
b.fast['fast_instance'](b.name('RigidPorcelainSail'),verts,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'Porcelain',sail,(0,0,0))
b.beam('Boom',(0,0,-.19),(.32,0,-.19),.009,'Nickel',sail)
b.tube('SailEdge',[(0,-.014,.23),(.30,-.014,-.19),(0,-.014,-.19)],.005,'ArchiveGold',sail,1)
b.tube('SailRigging',[(-.30,0,.18),(-.04,0,.73),(.36,0,.18)],.0035,'ArchiveGold',ship,1)
b.cube('SignalFlag',(.10,.008,.052),'Red',ship,(.003,0,.73),.003)
for i in range(3):
    wave=b.empty('G4_TideRib'+str(i),root,(0,(i-1)*.14,.05));b.ribbon('TideCrest',[(x/20*.40,0,math.sin(x/20*math.pi*2+i)*.022) for x in range(-20,21)],[.004+.018*math.sin((x+20)/40*math.pi) for x in range(-20,21)],.007,'Nickel',wave);rig(d,wave,'wave',phase=i*1.7)

# 4: three flowers with articulated petals, not a particle cloud.
root,d=item(3,'发条花园','调整花开','绽放')
b.cyl('GardenBowl',.25,.11,'Satin',root,(0,0,.07));b.torus('GardenLip',.249,.016,'ArchiveGold',root,(0,0,.127));b.torus('GardenFoot',.25,.009,'ArchiveGold',root,(0,0,.022))
for i,(x,y,height) in enumerate([(-.20,.04,.48),(.19,.05,.56),(0,-.11,.39)]):
    b.beam('FlowerStem',(x*.5,y,.10),(x,y,height),.013,'ArchiveGold',root)
    center=b.empty('G4_Flower'+str(i),root,(x,y,height));b.sphere('FlowerHeart',.044,'ArchiveGold',center)
    for stamen in range(5):
        a=stamen*math.tau/5;p=(.041*math.cos(a),.041*math.sin(a),.09+(stamen%2)*.035);b.beam('StamenFilament',(0,0,.012),p,.003,'ArchiveGold',center);b.sphere('StamenHead',.012,'ArchiveGold',center,p)
    for j in range(6):
        a=j*math.tau/6;socket=b.empty('PetalRadial',center);socket.rotation_euler.z=a
        petal=b.empty('G4_Petal%d_%d'%(i,j),socket,(.030,0,0))
        def petal_point(u,v):
            width=.006+.060*math.sin(math.pi*u)**.8
            return Vector((u*.20,v*width,.06*math.sin(math.pi*u)+.08*u*u+.012*v*v))
        verts=[];faces=[];nx=24;ny=8;stride=(nx+1)*(ny+1)
        for shell in [-1,1]:
            for a in range(nx+1):
                for c in range(ny+1):verts.append(petal_point(a/nx,c/ny*2-1)+Vector((0,0,shell*.004)))
        for shell in range(2):
            for a in range(nx):
                for c in range(ny):
                    k=shell*stride+a*(ny+1)+c;face=(k,k+1,k+ny+2,k+ny+1);faces.append(face if shell else tuple(reversed(face)))
        border=[a*(ny+1) for a in range(nx+1)]+[nx*(ny+1)+c for c in range(1,ny+1)]+[a*(ny+1)+ny for a in range(nx-1,-1,-1)]+list(range(ny-1,0,-1))
        for a,c in zip(border,border[1:]+border[:1]):faces.append((a,c,c+stride,a+stride))
        b.fast['fast_instance'](b.name('SculptedFlowerPetal'),verts,faces,'Porcelain',petal,(0,0,0),smooth_faces=True)
        b.tube('PetalMidrib',[tuple(petal_point(a/nx,0)+Vector((0,0,.005))) for a in range(nx+1)],.0025,'ArchiveGold',petal,1)
        outline=[tuple(petal_point(a/nx,-1)) for a in range(nx+1)]+[tuple(petal_point(a/nx,1)) for a in range(nx,-1,-1)];outline.append(outline[0])
        b.tube('PetalGoldBinding',outline,.0032,'ArchiveGold',petal,1)
        b.joint(petal,(0,0,0),.017,(0,1,0));rig(d,petal,'petal',flower=i,petal=j)

# 5: an actual geared orrery silhouette with three spatially tilted rings.
root,d=item(4,'三环星轨仪','倾斜轨道','加速公转')
b.beam('OrreryColumn',(0,0,0),(0,0,.47),.022,'Nickel',root)
center=b.empty('OrreryCore',root,(0,0,.47));b.sphere('RedSun',.094,'RubyGlow',center)
for i,r in enumerate([.18,.27,.36]):
    tilt=b.empty('G4_OrbitTilt'+str(i),center);tilt.rotation_euler=(math.radians(25+i*22),math.radians(-18+i*20),0);rig(d,tilt,'orbit_tilt',index=i)
    ring=b.empty('G4_OrbitRing'+str(i),tilt);b.torus('OrbitTrack',r,.010,'ArchiveGold',ring)
    b.sphere('IvoryPlanet',.031+i*.007,'Porcelain',ring,(r,0,0));b.torus('PlanetMeridian',.032+i*.007,.002,'ArchiveGold',ring,(r,0,0),front)
    b.torus('PlanetRedBelt',.032+i*.007,.004,'Red',ring,(r,0,0))
    b.sphere('OrbitCounterweight',.020,'ArchiveGold',ring,(-r,0,0));rig(d,ring,'orbit',ratio=[1,-.67,.44][i])

# 6: solid spiral treads; a burgundy traveller visibly climbs one step at a time.
root,d=item(5,'回环阶梯','改变方向','巡游')
b.beam('StairSpine',(0,0,.015),(0,0,.76),.021,'ArchiveGold',root)
for i in range(18):
    a=i/18*math.tau*1.35;z=.065+i*.036
    b.cube('IvoryTread',(.18,.12,.020),'Porcelain',root,(.22*math.cos(a),.22*math.sin(a),z),.005,(0,0,a))
    b.beam('TreadCantilever',(0,0,z),(.22*math.cos(a),.22*math.sin(a),z),.007,'Nickel',root)
    b.beam('RailStanchion',(.30*math.cos(a),.30*math.sin(a),z),(.30*math.cos(a),.30*math.sin(a),z+.064),.004,'ArchiveGold',root)
b.tube('SpiralHandrail',[(.30*math.cos(i/90*math.tau*1.35),.30*math.sin(i/90*math.tau*1.35),.129+i/90*17*.036) for i in range(91)],.007,'ArchiveGold',root)
runner=b.empty('G4_StairTraveller',root,(.22,0,.09));b.sphere('Traveller',.037,'RubyGlow',runner);rig(d,runner,'traveller')

data['g_archive']={'contents':catalog,'specimen_scale':1.18,'platform':platform.name,'lift':lift.name,'slide':slide.name,'exhibition':exhibition.name,'receivers':receivers,'locks':data.pop('g_archive_locks'),'case_nodes':case_nodes,'atlas':'res://assets/collection/art/G/optical_atlas.png','board':'production/G_archive/images/G_archive_flow.png'}
data['source_blend']='blender/collection/G_archive.blend';data['g_mechanism']['relief']='';data['g_mechanism']['relief_layers']=[]
for p in b.parts:data['parts'].append({'name':p['obj'].name,'home':pose(p['obj'].matrix_basis),'offset':p['offset'],'stage':p['stage']})
for obj,fn in b.controls:
    samples=[]
    for i in range(101):fn(obj,i/100);samples.append(pose(obj.matrix_basis))
    fn(obj,0);data['controls'].append({'name':obj.name,'samples':samples})
data['part_count']=len(data['parts']);data['qa_shells']+=b.qa_shells
for item in data['controls']:
    obj=bpy.data.objects.get(item['name']);p=item['samples'][0]
    if obj:obj.matrix_basis=C.inverted()@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
for content in catalog:bpy.data.objects[content['root']].hide_render=True
scene.timeline_markers.clear();scene.timeline_markers.new('Await archive interaction take',frame=1);scene.frame_end=1800
out=ROOT/'app/assets/collection/models/G_archive.glb';out.with_suffix('.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
seen=set()
for obj in b.col.all_objects:
    if obj.type=='MESH' and obj.name.startswith('G4_') and obj.data.as_pointer() not in seen:
        seen.add(obj.data.as_pointer());bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/data['source_blend']))
optimize(out)
print('G_ARCHIVE_CREATED',len(catalog),'contents',data['part_count'],'parts',flush=True)
