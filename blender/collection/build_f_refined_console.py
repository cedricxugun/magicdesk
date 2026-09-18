"""F-specific manufactured controls; preserves shared base and generic/G libraries."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
from optimize_runtime_meshes import optimize
b=Builder('FCTRL','Lagrange legible tactile console')
b.material('FConsolePorcelain',(.78,.755,.69),0,.26,normal='ceramic_glaze_normal.png',coat=.38)
b.material('FConsoleNickel',(.44,.49,.52),.97,.27,normal='metal_normal.png')
b.material('FConsoleBrass',(.50,.32,.13),.98,.30,normal='metal_normal.png')
b.material('FConsoleInk',(.035,.038,.033),.08,.46)
b.material('FConsoleRuby',(.22,.010,.013),.20,.22,coat=.45)
b.material('FConsoleGlass',(.16,.052,.012),.25,.14,coat=.55)
b.material('FConsoleZone',(.43,.24,.10),.58,.42)
font_file=Path('/System/Library/Fonts/STHeiti Medium.ttc')
assert font_file.exists(),'Local source font needed for engraved Chinese legends'
font=bpy.data.fonts.load(str(font_file))
def g(p):return Vector((p[0],-p[2],p[1]))
def cube(name,dim,mat,parent,p=(0,0,0),bevel=.003):return b.cube(name,(dim[0],dim[2],dim[1]),mat,parent,g(p),bevel)
def cyl(name,r,depth,mat,parent,p=(0,0,0),axis=(0,0,1)):
    return b.cyl(name,r,depth,mat,parent,g(p),g(axis).to_track_quat('Z','Y'),64)
def sleeve(name,r,inside,depth,mat,parent,p=(0,0,0),axis=(0,0,1)):
    o=b.sleeve(name,r,inside,depth,mat,parent,g(p),64);o.rotation_euler=g(axis).to_track_quat('Z','Y').to_euler();o.modifiers[0].width=.0005;return o
def beam(name,a,c,r,mat,parent):return b.beam(name,g(a),g(c),r,mat,parent)
def text(word,size,parent,p):
    data=bpy.data.curves.new('Engraving_'+word,'FONT');data.body=word;data.font=font;data.size=size;data.align_x='CENTER';data.align_y='CENTER';data.extrude=.00010;data.resolution_u=4
    o=bpy.data.objects.new(b.name('Legend'),data);b.col.objects.link(o);o.parent=parent;o.location=g(p);o.rotation_euler=(math.pi/2,0,0);data.materials.append(b.mats['FConsoleInk']);return o
def screw(parent,p):
    cyl('CaptiveScrew',.005,.003,'FConsoleNickel',parent,p)
    cube('ScrewSlot',(.005,.001,.0004),'FConsoleInk',parent,(p[0],p[1],p[2]+.0016),.0001)
def subtract(obj,cutter):
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Manufactured clearance bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    while obj.modifiers.find(mod.name)>0:bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
def legend(parent,word):
    # Editable type prototype; runtime seats it on the actual shared curved panel.
    patch=b.empty(b.name('LegendSurface'),parent,g((0,-.123,0)))
    text(word,.037,patch,(0,0,0))
def plate(root):
    static=b.empty('WidgetSocket',root);moving=b.empty('MovingGrip',root)
    cube('RecessedGasket',(.220,.148,.008),'FConsoleInk',static,(0,0,-.004),.016)
    cube('NickelEscutcheon',(.211,.139,.014),'FConsoleNickel',static,(0,0,.003),.015)
    cube('IvoryFace',(.200,.128,.006),'FConsolePorcelain',static,(0,0,.013),.012)
    for sign in [-1,1]:screw(static,(sign*.090,0,.018))
    return static,moving
roots=[]
for i,kind in enumerate(['rotary','hold','detent','gauge','service']):
    root=b.empty('FCTRL_'+kind,b.upper);roots.append(root)
    if kind in ['rotary','gauge']:
        static=b.empty('WidgetSocket',root);moving=b.empty('MovingGrip',root)
        sleeve('SocketHousing',.102,.013 if kind=='rotary' else .079,.030,'FConsoleNickel',static,(0,0,.005))
        sleeve('DarkSeatingLip',.098,.089,.007,'FConsoleInk',static,(0,0,.023))
    else:static,moving=plate(root)
    if kind=='rotary':
        sleeve('ShaftBush',.014,.0094,.018,'FConsoleBrass',static,(0,0,.004))
        cyl('RotatingSpindle',.009,.060,'FConsoleNickel',moving,(0,0,.020))
        cyl('KnurledBody',.083,.026,'FConsoleNickel',moving,(0,0,.034))
        cyl('PreloadFace',.072,.010,'FConsolePorcelain',moving,(0,0,.052))
        sleeve('DialFaceLip',.076,.071,.008,'FConsoleBrass',moving,(0,0,.054))
        for j in range(48):
            a=j*math.tau/48
            o=cube('MachinedKnurl',(.0032,.006,.022),'FConsoleInk',moving,(.083*math.cos(a),.083*math.sin(a),.034),.0007)
            o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion((0,-1,0),a)
        for j in range(17):
            a=(-1+j/8)*math.pi*.8
            r0=.052 if j in [0,8,16] else .058
            beam('PreloadEtchedTick',(r0*math.sin(a),r0*math.cos(a),.058),(.066*math.sin(a),.066*math.cos(a),.058),.0011,'FConsoleInk',moving)
        cube('MovingCenterMark',(.005,.026,.001),'FConsoleRuby',moving,(0,.034,.058),.0006)
        beam('FixedDatum',(-.006,.110,.050),(0,.101,.055),.002,'FConsoleRuby',static)
        beam('FixedDatum',(0,.101,.055),(.006,.110,.050),.002,'FConsoleRuby',static)
        text('−',.030,static,(-.073,-.069,.027));text('+',.030,static,(.073,-.069,.027));legend(static,'预载')
    elif kind=='hold':
        cube('BrakeWell',(.163,.111,.008),'FConsoleInk',static,(0,0,.022),.015)
        for x in [-.052,.052]:
            sleeve('PlungerBush',.009,.0054,.020,'FConsoleBrass',static,(x,0,.024))
            cyl('PressureGuidePin',.005,.027,'FConsoleNickel',moving,(x,0,.035))
        cube('RigidPressureCarrier',(.156,.099,.012),'FConsoleNickel',moving,(0,0,.051),.013)
        for side in [-1,1]:cube('IvoryThumbPlate',(.072,.087,.018),'FConsolePorcelain',moving,(side*.0385,0,.065),.016)
        cube('RubyDivide',(.004,.073,.0015),'FConsoleRuby',moving,(0,0,.075),.0005)
        for side in [-1,1]:
            for yy in [-.018,.018]:beam('ClampGlyph',(side*.048,yy,.075),(side*.025,yy,.075),.0016,'FConsoleInk',moving)
            beam('ClampGlyph',(side*.025,-.018,.075),(side*.025,.018,.075),.0016,'FConsoleInk',moving)
        legend(static,'制动')
    elif kind=='detent':
        cube('LeverRecess',(.091,.112,.008),'FConsoleInk',static,(0,0,.022),.016)
        for sign in [-1,1]:
            beam('TrunnionSupport',(sign*.025,-.035,.018),(sign*.025,-.013,.037),.005,'FConsoleNickel',static)
            sleeve('LeverBearing',.009,.0046,.008,'FConsoleBrass',static,(sign*.025,0,.037),(1,0,0))
        beam('LeverAxle',(-.030,0,.037),(.030,0,.037),.0042,'FConsoleNickel',moving)
        beam('BiasLeverStem',(0,0,.037),(0,.009,.116),.006,'FConsoleNickel',moving)
        b.sphere('RedLeverTip',.020,'FConsoleRuby',moving,g((0,.010,.127)),scale=(.82,1.05,1.22))
        for j,word in enumerate(['−','0','+']):text(word,.026,static,(-.070,(j-1)*.044,.019))
        legend(static,'磁偏')
    elif kind=='gauge':
        cyl('IvoryGaugeFace',.079,.008,'FConsolePorcelain',static,(0,0,.025))
        sleeve('GaugeBezel',.087,.077,.014,'FConsoleBrass',static,(0,0,.034))
        # Central neutral sector, with a signed needle. Neither endpoint means success.
        for j in range(9):
            a=-.14+j*.035
            beam('NeutralSector',(-math.sin(a)*.052,math.cos(a)*.052,.030),(-math.sin(a)*.068,math.cos(a)*.068,.030),.0014,'FConsoleZone',static)
        for j in range(17):
            a=-1.+j/8
            beam('GaugeEngraving',(-math.sin(a)*(.052 if j%4==0 else .059),math.cos(a)*(.052 if j%4==0 else .059),.031),(-math.sin(a)*.070,math.cos(a)*.070,.031),.001,'FConsoleInk',static)
        text('0',.020,static,(0,.043,.030));text('−',.024,static,(-.056,.012,.030));text('+',.024,static,(.056,.012,.030))
        beam('SignedNeedle',(0,-.012,.037),(0,.058,.037),.0018,'FConsoleRuby',moving)
        cyl('NeedleHub',.008,.009,'FConsoleNickel',moving,(0,0,.037))
        sleeve('LampSocket',.010,.0068,.006,'FConsoleNickel',static,(0,-.054,.032))
        lamp=b.empty('FCTRL_SettleLamp',static)
        cyl('AmberSettleLens',.0066,.004,'FConsoleGlass',lamp,(0,-.054,.034))
        legend(static,'合衡')
    else:
        cube('RockerWell',(.170,.102,.008),'FConsoleInk',static,(0,0,.025),.009)
        cube('ServiceRocker',(.145,.072,.030),'FConsolePorcelain',moving,(0,0,.043),.012)
        cube('ServiceDivider',(.003,.060,.001),'FConsoleRuby',moving,(0,0,.059),.0006)
        for sign in [-1,1]:
            beam('ServiceChevron',(sign*.034,-.012,.060),(sign*.047,0,.060),.0018,'FConsoleInk',moving)
            beam('ServiceChevron',(sign*.047,0,.060),(sign*.034,.012,.060),.0018,'FConsoleInk',moving)
        legend(static,'拆装')
        beam('RockerAxle',(0,-.047,.043),(0,.047,.043),.0035,'FConsoleNickel',moving)
        for side in [-1,1]:
            sleeve('RockerJournal',.008,.004,.008,'FConsoleBrass',static,(0,side*.041,.043),(0,1,0))
            beam('RockerJournalFoot',(0,side*.055,.012),(0,side*.041,.031),.004,'FConsoleNickel',static)
    if kind=='hold':
        for x in [-.052,.052]:
            cutter=cyl('ClearanceTool',.0056,.070,'FConsoleInk',static,(x,0,.020))
            for obj in list(static.children):
                if obj.type=='MESH' and any(k in obj.name for k in ['RecessedGasket','NickelEscutcheon','IvoryFace','BrakeWell']):subtract(obj,cutter)
            bpy.data.objects.remove(cutter,do_unlink=True)
    if kind=='service':
        cutter=cube('RockerClearance',(.158,.088,.080),'FConsoleInk',static,(0,0,.025),.009)
        bpy.context.view_layer.objects.active=cutter
        for mod in list(cutter.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        for obj in list(static.children):
            if obj.type=='MESH' and any(k in obj.name for k in ['RecessedGasket','NickelEscutcheon','IvoryFace','RockerWell']):subtract(obj,cutter)
        bpy.data.objects.remove(cutter,do_unlink=True)
    root.location=g((i*.32,0,0))
source=ROOT/'blender/collection/F_Refined_Controls.blend'
if source.exists():
    backup=ROOT/'blender/collection/checkpoints'/('F-console-'+hashlib.sha256(source.read_bytes()).hexdigest()[:12]+'.blend');backup.write_bytes(source.read_bytes())
for img in bpy.data.images:
    if img.source=='FILE' and not img.packed_file:img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(source))
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
out=ROOT/'app/assets/collection/f_refined_controls.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
root_names=[r.name for r in roots]
optimize(out)
(out.with_suffix('.json')).write_text(json.dumps({'source':str(source.relative_to(ROOT)),'reference':'production/F_complete/revision_20260911/lighting_and_controls.png','roots':root_names,'lever_pivot':[0,0,.037],'service_pivot':[0,0,.043],'brake_stroke':.010,'shared_base_modified':False,'status':'Independent F console WIP; no assembly/input clearance claim'},indent=2)+'\n')
print('F_REFINED_CONTROLS_SAVED',flush=True)
