"""I-specific controls from the approved helix production sheet. Isolated source."""
import bpy,sys,math,json,hashlib,bmesh
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
from optimize_runtime_meshes import optimize
OUT=ROOT/'production/I_refinement/console_r1';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'blender/collection/I_Controls_r1.blend'
if source.exists():
    saved=json.loads((OUT/'build.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==saved['source_sha256'],'Preserve unrecorded source edits'
    backup=source.parent/'checkpoints'/('I-console-'+saved['source_sha256'][:12]+'.blend')
    backup.parent.mkdir(exist_ok=True);backup.write_bytes(source.read_bytes())
b=Builder('ICTRL','Helix acoustic console')
for name,color,metal,rough,coat in [
    ('IPorcelain',(.79,.755,.685),0,.26,.38),('INickel',(.44,.49,.52),.97,.29,.08),
    ('IBrass',(.47,.30,.12),.95,.31,.05),('IInk',(.026,.031,.029),.12,.45,0),
    ('IRuby',(.27,.013,.011),.18,.24,.38),('IAmber',(.7,.25,.025),.1,.24,.45),
    ('IBlue',(.08,.32,.45),.15,.24,.45)]:
    b.material(name,color,metal,rough,coat=coat)
font=bpy.data.fonts.load('/System/Library/Fonts/STHeiti Medium.ttc')
def g(p):return Vector((p[0],-p[2],p[1]))
def cube(name,dim,mat,parent,p=(0,0,0),bevel=.002):
    return b.cube(name,(dim[0],dim[2],dim[1]),mat,parent,g(p),bevel)
def cyl(name,r,depth,mat,parent,p=(0,0,0),axis=(0,0,1)):
    return b.cyl(name,r,depth,mat,parent,g(p),g(axis).to_track_quat('Z','Y'),64)
def sleeve(name,r,inside,depth,mat,parent,p=(0,0,0),axis=(0,0,1)):
    o=b.sleeve(name,r,inside,depth,mat,parent,g(p),64);o.rotation_euler=g(axis).to_track_quat('Z','Y').to_euler();o.modifiers[0].width=.0004;return o
def beam(name,a,c,r,mat,parent):return b.beam(name,g(a),g(c),r,mat,parent)
def text(word,size,parent,p,mat='IInk'):
    data=bpy.data.curves.new('Type_'+word,'FONT');data.body=word;data.font=font;data.size=size;data.align_x='CENTER';data.align_y='CENTER';data.extrude=.00008;data.resolution_u=4
    o=bpy.data.objects.new(b.name('Legend'),data);b.col.objects.link(o);o.parent=parent;o.location=g(p);o.rotation_euler=(math.pi/2,0,0);data.materials.append(b.mats[mat]);return o
def screw(parent,x,y,z):
    cyl('CaptiveScrew',.004,.003,'INickel',parent,(x,y,z))
    cube('ScrewSlot',(.004,.0009,.0004),'IInk',parent,(x,y,z+.0016),.0001)
def subtract(obj,cutter):
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Manufactured pocket','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    while obj.modifiers.find(mod.name)>0:bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
def pocket(static,cut):
    bpy.context.view_layer.objects.active=cut
    for mod in list(cut.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    for obj in list(static.children):
        if obj.type=='MESH' and any(k in obj.name for k in ['Gasket','Escutcheon','IvoryFace']):subtract(obj,cut)
    bpy.data.objects.remove(cut,do_unlink=True)
def socket(root):
    static=b.empty('WidgetSocket',root);moving=b.empty('MovingGrip',root)
    if root.name=='ICTRL_frequency':
        cyl('Gasket',.095,.007,'IInk',static,(0,0,-.003))
        cyl('Escutcheon',.092,.014,'INickel',static,(0,0,.003))
        cyl('IvoryFace',.087,.006,'IPorcelain',static,(0,0,.013))
        for x in [-.080,.080]:screw(static,x,0,.019)
        return static,moving
    cube('Gasket',(.216,.157,.008),'IInk',static,(0,0,-.004),.014)
    cube('Escutcheon',(.208,.149,.014),'INickel',static,(0,0,.003),.012)
    cube('IvoryFace',(.195,.136,.006),'IPorcelain',static,(0,0,.013),.011)
    for x in [-.088,.088]:screw(static,x,0,.018)
    return static,moving
roots=[];rig={}
for index,kind in enumerate(['frequency','pressure','throat','gauge','service']):
    root=b.empty('ICTRL_'+kind,b.upper);roots.append(root);static,moving=socket(root)
    label=b.empty('ICTRL_Label_'+kind,static,g((0,-.104,.018)))
    # Detached legend is a mounting patch; runtime review seats it on the real cassette.
    text({'frequency':'调频','pressure':'蓄压','throat':'喉口','gauge':'出 / 回','service':'拆装'}[kind],.027,label,(0,0,0))
    rig[kind]={'root':root.name,'moving':moving.name,'label':label.name}
    if kind=='frequency':
        pocket(static,cyl('SpindleCut',.0096,.10,'IInk',static,(0,0,.020)))
        sleeve('WheelSocket',.073,.0095,.024,'IBrass',static,(0,0,.026))
        cyl('WheelSpindle',.009,.05,'INickel',moving,(0,0,.037))
        cyl('WheelRim',.065,.028,'INickel',moving,(0,0,.054))
        cyl('WheelFace',.057,.009,'IPorcelain',moving,(0,0,.073))
        for j in range(48):
            a=j*math.tau/48
            o=cube('Knurl',(.0021,.0045,.020),'IInk',moving,(.065*math.cos(a),.065*math.sin(a),.055),.0004);o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion((0,-1,0),a)
        beam('FrequencyPointer',(0,.018,.079),(0,.049,.079),.0021,'IRuby',moving)
        for j in range(13):
            a=(-.8+j/12*1.6)*math.pi
            beam('FrequencyTick',(.075*math.sin(a),.075*math.cos(a),.026),(.080*math.sin(a),.080*math.cos(a),.026),.0007,'IInk',static)
        text('低',.014,static,(-.063,-.052,.024));text('高',.014,static,(.063,-.052,.024))
        rig[kind]['angle_range']=[-math.pi*.8,math.pi*.8]
    elif kind=='pressure':
        pocket(static,cube('WellCut',(.136,.101,.080),'IInk',static,(-.008,0,.025),.013))
        well=cube('PressureWell',(.142,.107,.006),'IInk',static,(-.008,0,-.006),.014)
        for x in [-.045,.029]:
            cut=cyl('PinCut',.0046,.10,'IInk',static,(x,0,.0));subtract(well,cut);bpy.data.objects.remove(cut,do_unlink=True)
            sleeve('PressureBush',.008,.0044,.026,'IBrass',static,(x,0,.008))
            cyl('PressurePin',.004,.046,'INickel',moving,(x,0,.028))
        cube('PadCarrier',(.130,.093,.010),'INickel',moving,(-.008,0,.048),.012)
        cube('SingleThumbPad',(.118,.082,.018),'IPorcelain',moving,(-.008,0,.062),.016)
        cube('PressureMark',(.004,.060,.001),'IRuby',moving,(-.008,0,.0715),.0005)
        # Independent pressure float beside the thumb, seated on a real rail.
        cube('PressureScaleWell',(.013,.082,.008),'IInk',static,(.072,0,.022),.004)
        beam('PressureFloatRail',(.072,-.034,.030),(.072,.034,.030),.0013,'INickel',static)
        indicator=b.empty('ICTRL_PressureFloat',static)
        cube('PressureFloat',(.009,.009,.005),'IAmber',indicator,(.072,-.029,.035),.002)
        rig[kind].update({'stroke':.015,'indicator':indicator.name,'indicator_travel':.058})
    elif kind=='throat':
        # Continuous pivoted gate lever; horizontal gesture, no sliding stem through a plate.
        pocket(static,cube('GateCut',(.074,.061,.080),'IInk',static,(0,0,.025),.012))
        cube('GateBacking',(.079,.066,.006),'IInk',static,(0,0,-.006),.012)
        for y in [-.022,.022]:
            beam('GateJournalFoot',(0,y,.012),(0,y,.034),.005,'INickel',static)
            sleeve('GateJournal',.008,.0044,.008,'IBrass',static,(0,y,.039),(0,1,0))
        beam('GateAxle',(0,-.029,.039),(0,.029,.039),.004,'INickel',moving)
        beam('GateStem',(0,0,.039),(0,0,.095),.005,'INickel',moving)
        cyl('GateGrip',.016,.038,'IRuby',moving,(0,0,.108),(0,1,0))
        for j in range(9):
            x=(j-4)*.015;beam('GateScale',(x,-.039,.020),(x,-.047,.020),.0007,'IInk',static)
        text('闭',.016,static,(-.065,.033,.020));text('开',.016,static,(.065,.033,.020))
        rig[kind].update({'pivot':[0,0,.039],'angle_range':[-.52,.52]})
    elif kind=='gauge':
        cube('TwinReadoutBed',(.145,.108,.012),'IInk',static,(0,0,.026),.009)
        for side,col,word in [(-1,'IAmber','出'),(1,'IBlue','回')]:
            x=side*.038
            cube('ReedChannel',(.030,.080,.006),'INickel',static,(x,0,.035),.008)
            cube('DarkChannel',(.021,.068,.004),'IInk',static,(x,0,.039),.005)
            beam('ReadoutRail',(x,-.030,.044),(x,.030,.044),.0011,'IBrass',static)
            for j in range(6):beam('ReadoutTick',(x+.012,-.026+j*.0104,.044),(x+.017,-.026+j*.0104,.044),.0006,'IPorcelain',static)
            reed=b.empty('ICTRL_'+('OutgoingReed' if side<0 else 'ReturnReed'),static)
            cube('SignalFloat',(.015,.009,.005),col,reed,(x,-.026,.048),.003)
            sleeve('LensSeat',.007,.0047,.004,'IBrass',static,(x,-.045,.044))
            cyl('SignalLens',.0046,.003,col,static,(x,-.045,.046))
            text(word,.018,static,(x,.059,.021))
            rig[kind]['outgoing' if side<0 else 'return']=reed.name
        rig[kind]['travel']=.052
    else:
        pocket(static,cube('ServiceCut',(.144,.073,.08),'IInk',static,(0,0,.03),.008))
        cube('ServiceWell',(.150,.080,.005),'IInk',static,(0,0,-.006),.009)
        cube('ServiceRocker',(.130,.061,.025),'IPorcelain',moving,(0,0,.040),.008)
        beam('ServiceAxle',(0,-.040,.040),(0,.040,.040),.0035,'INickel',moving)
        for y in [-.035,.035]:
            sleeve('ServiceJournal',.007,.0038,.007,'IBrass',static,(0,y,.040),(0,1,0))
            beam('ServiceFoot',(0,y,.014),(0,y,.032),.004,'INickel',static)
        cube('ServiceSeparator',(.003,.047,.001),'IRuby',moving,(0,0,.053),.0005)
        text('拆',.024,moving,(-.032,0,.054));text('合',.024,moving,(.032,0,.054))
        rig[kind]['pivot']=[0,0,.040]
    root.location=g((index*.27,0,0))
# Standardize outward normals (including custom sleeve/cylinder utility output).
for obj in b.col.objects:
    if obj.type=='MESH':
        if obj.data.users>1:obj.data=obj.data.copy()
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
for img in bpy.data.images:
    if img.source=='FILE' and not img.packed_file:img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(source))
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
glb=ROOT/'app/assets/collection/components/I_controls_r1.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_animations=False);optimize(glb)
data={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'component':str(glb.relative_to(ROOT)),'component_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'reference':'production/I_refinement/r1/structure_and_motion.png','rig':rig,'shared_base_modified':False,'scope':'Independent authored I control assets. Mounting, collision, native input and final material review pending.'}
(OUT/'build.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(ROOT/'app/assets/collection/i_console_rig.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('I_CONSOLE_BUILT',len(roots),flush=True)
