"""Second detail pass: clock movement, curved sailing vessel, garden machinery,
orrery cage and continuous stair/lift circuit. Retains G5 book and butterfly."""
import bpy,bmesh,math,json,pathlib,sys
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder,pose
from optimize_runtime_meshes import optimize
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive_refined.blend'))
scene=bpy.context.scene;scene.frame_set(1);data=json.loads((ROOT/'app/assets/collection/models/G_archive_refined.json').read_text(encoding='utf-8'))
b=Builder.__new__(Builder);b.id='G6';b.title='Archive specimen details';b.scene=scene;b.col=bpy.data.collections['MODULE_G3'];b.root=bpy.data.objects[data['root']];b.upper=bpy.data.objects[data['upper']]
b.serial=50000;b.parts=[];b.controls=[];b.motions=[];b.sockets={};b.qa_shells=[];b.extra={};b.mats={m.name.removeprefix('Collection_'):m for m in bpy.data.materials if m.name.startswith('Collection_')}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats};exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
front=(math.pi/2,0,0)
def remove(obj):
    for o in list(obj.children_recursive)+[obj]:bpy.data.objects.remove(o,do_unlink=True)
def replace(index):
    d=data['g_archive']['contents'][index];old=bpy.data.objects[d['root']];parent=old.parent;name=old.name;remove(old);root=b.empty(name,parent);d['rig']=[];return root,d
def rig(d,o,kind,**kw):d['rig'].append({'name':o.name,'kind':kind,'home':pose(o.matrix_basis),**kw});return o
def lathe(parent,name,profile,key='ArchiveGold',loc=(0,0,0),n=64):
    verts=[];faces=[]
    for z,r in profile:
        for i in range(n):
            a=i*math.tau/n;verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(profile)-1):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))])
    return b.fast['fast_instance'](b.name(name),verts,faces,key,parent,loc,smooth_faces=True)
def gear(parent,name,r,loc=(0,0,0),teeth=28,axis='front'):
    root=b.empty(name,parent,loc);verts=[];faces=[];n=teeth*6
    for y in [-.010,.010]:
        for inner in [False,True]:
            for i in range(n):
                radius=r*.58 if inner else r*[.87,.91,1.02,1.02,.91,.87][i%6];a=i*math.tau/n
                verts.append((radius*math.cos(a),y,radius*math.sin(a)))
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(i,2*n+i,2*n+j,j),(n+j,3*n+j,3*n+i,n+i)])
    obj=b.fast['fast_instance'](b.name('MachinedGearRim'),verts,faces,'ArchiveGold',root,(0,0,0));bevel=obj.modifiers.new('Tooth edge break','BEVEL');bevel.width=.0012;bevel.segments=2
    for i in range(5):
        a=i*math.tau/5;b.beam('GearSpoke',(.015*math.cos(a),0,.015*math.sin(a)),(r*.64*math.cos(a),0,r*.64*math.sin(a)),.0045,'Nickel',root)
    b.cyl('GearAxle',.013,.046,'Satin',root,rot=front,n=32);b.cyl('AxleCap',.010,.004,'ArchiveGold',root,(0,-.026,0),front,24)
    if axis=='horizontal':root.rotation_euler.x=math.pi/2
    return root

root,d=replace(0)
b.cube('ClockFoot',(.58,.26,.040),'ArchiveGold',root,(0,0,.025),.020)
b.cube('ClockEnamelFoot',(.51,.21,.035),'Red',root,(0,0,.058),.015)
for side in [-1,1]:
    x=side*.244
    lathe(root,'ArchitecturalPillar',[(.06,.045),(.085,.045),(.10,.027),(.18,.023),(.22,.034),(.26,.025),(.67,.025),(.71,.037),(.76,.032),(.91,.026)],loc=(x,0,0))
    b.cube('ColumnEnamelInsert',(.038,.052,.32),'Porcelain',root,(x,-.008,.46),.013)
    lathe(root,'SideFinial',[(.88,.040),(.91,.038),(.94,.026),(.975,.028),(1.045,.002)],loc=(x,0,0))
b.tube('ClockLowerArch',[(.21*math.cos(a),.018,.29+.12*math.sin(a)) for a in [i*math.pi/40 for i in range(41)]],.009,'ArchiveGold',root)
b.cube('ClockCrownBeam',(.57,.20,.043),'Porcelain',root,(0,0,.94),.019)
lathe(root,'ClockCrown',[(.958,.10),(.980,.106),(1.010,.079),(1.050,.040),(1.075,.042),(1.165,.002)],loc=(0,0,0))
b.torus('CrownRubySeal',.098,.008,'Red',root,(0,0,.987))
face=b.empty('G6_ClockDial',root,(0,-.014,.706))
for r,inside,depth,y,key in [(.259,.218,.058,0,'ArchiveGold'),(.224,.144,.021,-.026,'Porcelain'),(.242,.230,.016,-.044,'Satin')]:
    obj=b.sleeve('DialRecess',r,inside,depth,key,face,(0,y,0));obj.rotation_euler=front
for i,label in enumerate(['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']):
    a=i*math.tau/12;curve=bpy.data.curves.new(b.name('RomanHour'),'FONT');curve.body=label;curve.align_x='CENTER';curve.align_y='CENTER';curve.size=.024;curve.extrude=.0003
    obj=bpy.data.objects.new(curve.name,curve);b.col.objects.link(obj);obj.parent=face;obj.location=(.189*math.sin(a),-.043,.189*math.cos(a));obj.rotation_euler=front;curve.materials.append(b.mats['Black'])
for i,(x,z,r,ratio) in enumerate([(-.062,0,.070,1),(.061,0,.052,-1.35),(0,.096,.044,-1.6),(0,-.101,.038,1.9)]):rig(d,gear(face,'G6_ClockGear'+str(i),r,(x,.013,z)),'gear',ratio=ratio)
for kind,length,width in [('hour',.122,.007),('minute',.178,.0045)]:
    hand=b.empty('G6_'+kind,face,(0,-.073,0));b.beam('SculptedHand',(0,0,-.026),(0,0,length),width,'Satin',hand);b.sphere('HandTip',width*1.4,'ArchiveGold',hand,(0,0,length));rig(d,hand,kind)
b.cyl('HandsPin',.014,.015,'ArchiveGold',face,(0,-.084,0),front,24)
pend=b.empty('G6_Pendulum',root,(0,.025,.40));b.beam('PendulumRod',(0,0,0),(0,0,-.257),.007,'Nickel',pend);b.sphere('PendulumBob',.064,'ArchiveGold',pend,(0,0,-.257),(1,.37,1));b.torus('BobInset',.048,.003,'Satin',pend,(0,-.025,-.257),front);rig(d,pend,'pendulum',swing_gain=.24)
for z in [.14,.23,.33]:
    b.tube('ClockSideScroll',[(-.20,-.012,z),(-.165,-.025,z+.018),(-.14,-.020,z+.052)],.004,'ArchiveGold',root)
    b.tube('ClockSideScroll',[(.20,-.012,z),(.165,-.025,z+.018),(.14,-.020,z+.052)],.004,'ArchiveGold',root)

root,d=replace(2)
ship=b.empty('G6_ShipCradle',root,(0,0,.12));rig(d,ship,'ship')
verts=[];faces=[];nx=44;ny=20
for i in range(nx+1):
    t=.018+.964*i/nx;x=-.45+.90*t;width=.16*math.sin(math.pi*t)**.62;top=.205+.042*abs(t*2-1)**2;bottom=.058+.11*abs(t*2-1)**2
    for j in range(ny+1):
        a=j/ny*math.pi;verts.append((x,width*math.cos(a),top-(top-bottom)*math.sin(a)))
for i in range(nx):
    for j in range(ny):
        a=i*(ny+1)+j;faces.append((a,a+1,a+ny+2,a+ny+1))
hull=b.fast['fast_instance'](b.name('FormedHull'),verts,faces,'Porcelain',ship,(0,0,0),smooth_faces=True);solid=hull.modifiers.new('Hull skin thickness','SOLIDIFY');solid.thickness=.009
rim=[verts[i*(ny+1)] for i in range(nx+1)]+[verts[i*(ny+1)+ny] for i in range(nx,-1,-1)];b.tube('HullGoldGunwale',rim+[rim[0]],.009,'ArchiveGold',ship)
b.cube('InsetDeck',(.64,.235,.018),'Satin',ship,(0,0,.201),.08)
for side in [-1,1]:
    for x in [-.25,-.09,.09,.25]:
        y=side*.145*math.sqrt(max(.01,1-(x/.46)**2));b.cyl('PortholeGlass',.023,.008,'OpticalGlass',ship,(x,y,.161),front,32);b.torus('PortholeGoldRim',.027,.004,'ArchiveGold',ship,(x,y+side*.004,.161),front)
b.beam('GildedMast',(-.07,0,.21),(-.07,0,.985),.012,'ArchiveGold',ship)
def sail(name,side,height,width,offset):
    node=b.empty(name,ship,(-.07,offset,.58));N=18;vs=[];fs=[];rows=[]
    for a in range(N+1):
        row=[]
        for c in range(N+1-a):
            u=a/N;v=c/N;row.append(len(vs));vs.append((side*width*u,-.065*math.sin(math.pi*u)*math.sin(math.pi*v)*2,v*height-height*.43))
        rows.append(row)
    for a in range(N):
        for c in range(len(rows[a+1])):
            fs.append((rows[a][c],rows[a+1][c],rows[a][c+1]))
            if c+1<len(rows[a+1]):fs.append((rows[a][c+1],rows[a+1][c],rows[a+1][c+1]))
    obj=b.fast['fast_instance'](b.name('CurvedSail'),vs,fs,'Porcelain',node,(0,0,0),smooth_faces=True);s=obj.modifiers.new('Rigid sail shell','SOLIDIFY');s.thickness=.008
    b.tube('SailGoldEdge',[(0,-.006,height*.57),(side*width,-.006,-height*.43),(0,-.006,-height*.43),(0,-.006,height*.57)],.0045,'ArchiveGold',node)
    b.beam('GoldBoom',(0,0,-height*.43),(side*width*1.02,0,-height*.43),.007,'ArchiveGold',node)
    # A machined sun medallion and burgundy signal stripe, above the curved skin.
    if side>0:
        center=(width*.20,-.054,height*.06);b.torus('SailSun',.027,.0025,'ArchiveGold',node,center,front)
        for i in range(8):
            a=i*math.tau/8;b.beam('SailSunRay',(center[0]+.029*math.cos(a),-.057,center[2]+.029*math.sin(a)),(center[0]+.040*math.cos(a),-.057,center[2]+.040*math.sin(a)),.0018,'ArchiveGold',node)
    rig(d,node,'sail',side=side)
sail('G6_MainSail',1,.65,.38,0);sail('G6_ForeSail',-1,.44,.23,.022)
b.tube('StandingRigging',[(-.43,0,.235),(-.07,0,.98),(.43,0,.235)],.003,'ArchiveGold',ship)
b.cube('MastPennant',(.11,.008,.047),'Red',ship,(-.015,0,.975),.006)
for i in range(3):
    root_wave=b.empty('G6_Tide'+str(i),root,(0,(i-1)*.14,.065))
    pts=[(-.44+j*.022,0,.055*math.sin(j/40*math.pi*2+i*.65)) for j in range(41)]
    b.ribbon('CurvedSeaCradle',pts,[.004+.030*math.sin(j/40*math.pi)**.7 for j in range(41)],.009,'Nickel',root_wave)
    b.tube('WaveGildedCrest',[(x,-.010,z+.013) for x,y,z in pts],.0035,'ArchiveGold',root_wave);rig(d,root_wave,'wave',phase=i*1.7)
b.cyl('ShipUniversalBearing',.049,.085,'ArchiveGold',root,(0,0,.09),n=40)

# Garden: leave the new spoon-shaped petals intact and finish their mechanism.
root=bpy.data.objects[data['g_archive']['contents'][3]['root']];d=data['g_archive']['contents'][3]
for i,(x,y) in enumerate([(-.11,.025),(.10,.04),(0,-.09)]):
    o=gear(root,'G6_GardenDrive'+str(i),.052,(x,y,.11),'horizontal' if False else 24,axis='horizontal');rig(d,o,'gear',ratio=(-1 if i%2 else 1),local_axis='back')
for a in [i*math.tau/12 for i in range(12)]:
    b.cube('GardenEnamelFlute',(.029,.012,.048),'Porcelain',root,(.248*math.cos(a),.248*math.sin(a),.070),.007,(0,0,a))
    b.screw(root,(.233*math.cos(a),.233*math.sin(a),.132),(0,0,1),.006)
for i,(x,y,z) in enumerate([(-.15,.03,.26),(.14,.04,.34),(0,-.09,.245)]):
    b.tube('StemScroll',[(x,y,z),(x+.055,y-.012,z+.02),(x+.09,y-.016,z+.07),(x+.065,y-.009,z+.098)],.005,'ArchiveGold',root)
    b.sphere('PorcelainLeaf',.052,'Porcelain',root,(x+.054,y-.012,z+.045),(.75,.18,1.05))

# Orrery: solid ruby core within three safety meridians and an exposed drive.
root=bpy.data.objects[data['g_archive']['contents'][4]['root']];d=data['g_archive']['contents'][4]
for i in range(3):
    b.torus('SunSafetyMeridian',.107,.0045,'ArchiveGold',root,(0,0,.47),(math.pi/2,0,i*math.pi/3))
    o=gear(root,'G6_OrreryDrive'+str(i),.049,((i-1)*.085,-.045,.10+i*.025));rig(d,o,'gear',ratio=[1,-1.3,.75][i])
lathe(root,'OrreryPedestal',[(.005,.16),(.032,.16),(.05,.112),(.085,.088),(.14,.070)],'ArchiveGold')
b.torus('OrreryEnamelBand',.151,.008,'Red',root,(0,0,.031))

root,d=replace(5);d['stair_return']='spiral ascent -> top transfer -> centre lift descent -> lower transfer'
steps=28;turns=1.90
for side in [-1,1]:b.beam('LiftGuide',(side*.089,0,.04),(side*.089,0,.96),.006,'ArchiveGold',root)
for i in range(steps):
    a=i/(steps-1)*math.tau*turns;z=.074+i*.030
    vs=[];fs=[];n=8
    for height in [z-.009,z+.009]:
        for radius in [.14,.315]:
            for j in range(n+1):
                t=a+(j/n-.5)*.21;vs.append((radius*math.cos(t),radius*math.sin(t),height))
    stride=n+1
    for j in range(n):fs.extend([(j,j+1,stride+j+1,stride+j),(2*stride+j,3*stride+j,3*stride+j+1,2*stride+j+1),(stride+j,stride+j+1,3*stride+j+1,3*stride+j),(j,2*stride+j,2*stride+j+1,j+1)])
    fs.extend([(0,stride,3*stride,2*stride),(n,2*stride+n,3*stride+n,stride+n)])
    tread=b.fast['fast_instance'](b.name('CurvedEnamelTread'),vs,fs,'Porcelain',root,(0,0,0));mod=tread.modifiers.new('Tread edge radius','BEVEL');mod.width=.003;mod.segments=2
    b.beam('TreadCantilever',(.079*math.cos(a),.079*math.sin(a),z),(.245*math.cos(a),.245*math.sin(a),z),.006,'Nickel',root)
    b.sleeve('LiftGuideCollar',.081,.060,.012,'Satin',root,(0,0,z),n=40)
    b.beam('GoldBaluster',(.321*math.cos(a),.321*math.sin(a),z),(.321*math.cos(a),.321*math.sin(a),z+.063),.0035,'ArchiveGold',root)
b.tube('ContinuousSpiralRail',[(.321*math.cos(j/160*math.tau*turns),.321*math.sin(j/160*math.tau*turns),.137+j/160*(steps-1)*.030) for j in range(161)],.0055,'ArchiveGold',root)
runner=b.empty('G6_Traveller',root,(.22,0,.113));b.sphere('RubyTraveller',.031,'RubyGlow',runner);rig(d,runner,'traveller_return',turns=turns,height=(steps-1)*.030)
for z in [.074,.884]:
    b.beam('LiftTransferRail',(0,0,z+.016),(.23*math.cos(math.tau*turns if z>.5 else 0),.23*math.sin(math.tau*turns if z>.5 else 0),z+.016),.005,'ArchiveGold',root)

for item in data['g_archive']['contents']:
    obj=bpy.data.objects[item['root']]
    for child in [obj]+list(obj.children_recursive):child.hide_render=True
data['source_blend']='blender/collection/G_archive_detail.blend';data['g_archive']['visual_revision']='G6: all six specimen geometry detail pass; visual acceptance pending'
seen=set()
for obj in b.col.all_objects:
    if obj.type=='MESH' and obj.data.as_pointer() not in seen:
        seen.add(obj.data.as_pointer());bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
out=ROOT/'app/assets/collection/models/G_archive_detail.glb';out.with_suffix('.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/data['source_blend']));optimize(out)
print('G6_SPECIMENS_DETAILED',len(data['g_archive']['contents']),flush=True)
