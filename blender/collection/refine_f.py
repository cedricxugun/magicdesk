"""Refine the existing authored F source in a new sibling file.

No factory reset, no early build_models rerun, no write to F.blend or HELIOS.
Adds an exposed differential, curved vernier carriage, physical brake caliper,
machined bearing stacks and a shaped metal plumb. Runtime and Blender retain
separate movable nodes for the real gestures.
"""
import bpy, bmesh, json, math, pathlib, sys
from mathutils import Vector, Matrix, Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder, C, pose

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/F.blend'))
scene=bpy.context.scene
scene.frame_set(1)
data=json.loads((ROOT/'app/assets/collection/models/F.json').read_text(encoding='utf-8'))
b=Builder.__new__(Builder)
b.id='F2';b.title='F — differential refinement';b.scene=scene
b.col=bpy.data.collections['MODULE_F'];b.root=bpy.data.objects['F_MODULE'];b.upper=bpy.data.objects['F_UPPER']
b.serial=10000;b.parts=[];b.controls=[];b.motions=[];b.sockets={};b.qa_shells=[];b.extra={}
b.mats={m.name.removeprefix('Collection_'):m for m in bpy.data.materials if m.name.startswith('Collection_')}
namespace={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),namespace)
b.fast=namespace
front=(math.pi/2,0,0)
spine=bpy.data.objects['F_P_ContinuousSpine']

# The ivory shell gets a wider rolled shoulder instead of a flat strip.
for j in range(6):
    parent=bpy.data.objects['F_P_SpineCover'+str(j)]
    old=next(o for o in parent.children if 'CeramicSpine' in o.name)
    angles=[math.radians(60+240*i/120) for i in range(j*20+1,j*20+20)]
    made=b.ribbon('RolledPorcelain', [(-.1+math.cos(a),-.054,1.8+math.sin(a)) for a in angles],.111,.044,'Ivory',parent)
    old.data=made.data
    bpy.data.objects.remove(made,do_unlink=True)
    for a in [angles[2],angles[-3]]:
        b.screw(parent,(-.1+math.cos(a),-.103,1.8+math.sin(a)),(0,-1,0),.014)
    for edge in [-1,1]:
        b.tube('RolledChromeLip',[(-.1+(1+edge*.114)*math.cos(a),-.048,1.8+(1+edge*.114)*math.sin(a)) for a in angles],.007,'Chrome',parent)

# Two open rails and a toothed inner arc give the moving carriage a readable path.
arc=[math.radians(102+i*1.1) for i in range(81)]
for radius in [.805,.868]:
    b.tube('VernierGuide',[(-.1+radius*math.cos(a),-.128,1.8+radius*math.sin(a)) for a in arc],.011,'Chrome',spine)
for i,a in enumerate(arc):
    radius=.836
    b.cube('VernierEtching',(.007,.005,.033 if i%5==0 else .016),'Black',spine,(-.1+radius*math.cos(a),-.144,1.8+radius*math.sin(a)),.0006,(0,-a,0))
for i in range(32):
    a=math.radians(102+i*2.55)
    b.cube('CurvedRackTooth',(.014,.035,.019),'Chrome',spine,(-.1+.785*math.cos(a),-.075,1.8+.785*math.sin(a)),.002,(0,-a,0))

parts=[];rig=[]
def part(name,offset):
    p=b.empty('F2_P_'+name,b.upper)
    parts.append({'name':p.name,'home':pose(p.matrix_basis),'offset':list((C@Vector(offset).to_4d()).xyz),'stage':.42})
    return p
def moving(name,parent,location,kind):
    o=b.empty('F2_'+name,parent,location)
    rig.append({'name':o.name,'kind':kind,'home':pose(o.matrix_basis)})
    return o
def gear(name,parent,location,radius,teeth,kind):
    rotor=moving(name,parent,location,kind)
    ring=b.sleeve('GearWeb',radius*.80,radius*.40,.027,'Steel',rotor,n=64);ring.rotation_euler=front
    b.cyl('Hub',radius*.26,.060,'Chrome',rotor,(0,-.008,0),front)
    b.torus('GearRim',radius*.72,.004,'Chrome',rotor,(0,-.019,0),front)
    for i in range(6):
        a=i*math.tau/6
        b.beam('GearSpoke',(radius*.18*math.cos(a),0,radius*.18*math.sin(a)),(radius*.59*math.cos(a),0,radius*.59*math.sin(a)),radius*.050,'Chrome',rotor)
    for i in range(teeth):
        a=i*math.tau/teeth
        b.cube('MachinedTooth',(radius*.15,.032,radius*.14),'Chrome',rotor,(radius*.88*math.cos(a),0,radius*.88*math.sin(a)),.0015,(0,-a,0))
    b.screw(rotor,(0,-.043,0),(0,-1,0),radius*.12)
    return rotor

drive=part('Differential',(-.22,-.44,.35))
b.ribbon('DifferentialBack',[(-.49,-.028,2.33),(-.40,-.028,2.47),(-.20,-.028,2.65),(.12,-.028,2.72)],.060,.045,'Steel',drive)
gear('MainGear',drive,(-.13,-.13,2.61),.146,36,'trim_gear')
gear('CounterGear',drive,(-.311,-.13,2.48),.090,22,'counter_gear')
for x,z,r in [(-.13,2.61,.053),(-.311,2.48,.038)]:
    b.cyl('RearBearing',r,.086,'Chrome',drive,(x,-.062,z),front)
    b.torus('RedOilSeal',r*.85,.004,'Red',drive,(x,-.11,z),front)
    b.beam('BearingBridge',(x-.055,-.18,z+.067),(x+.055,-.18,z+.067),.014,'Steel',drive)
    for side in [-1,1]:b.screw(drive,(x+side*.055,-.196,z+.067),(0,-1,0),.009)

carriage_parent=part('VernierCarriage',(-.38,-.43,.13))
carriage=moving('TrimCarriage',carriage_parent,(0,0,0),'trim_carriage')
b.cube('Saddle',(.106,.090,.175),'Steel',carriage,(0,0,0),.018)
b.cube('VernierFace',(.086,.022,.142),'Ivory',carriage,(0,-.054,0),.018)
b.cube('IndexTongue',(.042,.024,.017),'Red',carriage,(0,-.070,0),.004)
for side in [-1,1]:
    b.cyl('GuideRoller',.021,.070,'Chrome',carriage,(side*.052,-.004,.045),front)
    b.cyl('GuideRoller',.021,.070,'Chrome',carriage,(side*.052,-.004,-.045),front)
    b.screw(carriage,(side*.027,-.070,.051),(0,-1,0),.008)

# A brake disc and two actual sliding pads have visible clearance at rest.
brake_parent=part('FrictionBrake',(.23,-.42,.30))
center=Vector((.4,-.055,2.64))
b.cyl('BrakeDisc',.096,.012,'Steel',brake_parent,center+Vector((0,-.100,0)),front,80)
b.torus('DiscPolishedTrack',.075,.005,'Chrome',brake_parent,center+Vector((0,-.111,0)),front)
b.beam('CaliperUpright',center+Vector((-.124,-.10,-.025)),center+Vector((-.124,-.10,.112)),.018,'Chrome',brake_parent)
b.beam('CaliperBridge',center+Vector((-.124,-.10,.112)),center+Vector((.124,-.10,.112)),.018,'Chrome',brake_parent)
for side in [-1,1]:
    jaw=moving('BrakePad'+str(side),brake_parent,center+Vector((side*.131,-.102,.020)),'brake_left' if side<0 else 'brake_right')
    b.cube('CaliperBlock',(.027,.062,.089),'Steel',jaw,bevel=.008)
    b.cube('FrictionPad',(.009,.039,.064),'Black',jaw,(-side*.017,0,0),.003)
    b.cyl('RedPiston',.018,.017,'Red',jaw,(0,-.042,0),front)
    b.screw(jaw,(0,-.055,0),(0,-1,0),.009)
b.coil(brake_parent,center+Vector((0,-.065,.102)),.019,.155,10,(1,0,0))

# Concentric machined bearing stacks, oil ports and clevises support the rods.
for parent in list(b.col.objects):
    if parent.type!='EMPTY' or '_C_' not in parent.name or not ('FourBar_end' in parent.name or 'Coupler_end' in parent.name):continue
    for y in [-.028,.028]:
        b.cyl('BearingStack',.054,.014,'Chrome',parent,(0,y,0),front)
        b.torus('BearingGasket',.046,.004,'Black',parent,(0,y-.009,0),front)
    b.cyl('AxleCap',.031,.009,'Ivory',parent,(0,-.046,0),front)
    b.screw(parent,(0,-.054,0),(0,-1,0),.012)

# A lathed plumb replaces the plain ellipsoid while retaining the same pivot.
pearl=next(o for o in b.col.objects if o.type=='MESH' and o.name.startswith('F_Pearl_'))
verts=[];uv=[];faces=[];rows=48;columns=64
for j in range(rows+1):
    t=j/rows;radius=.166*math.sin(math.pi*t)**.72*(1.30-.60*t)
    for i in range(columns+1):
        a=i*math.tau/columns;verts.append((radius*math.cos(a),radius*math.sin(a),-.26+.52*t));uv.append((i/columns,t))
for j in range(rows):
    for i in range(columns):
        a=j*(columns+1)+i;faces.append((a,a+1,a+columns+2,a+columns+1))
replacement=b.fast['fast_instance']('F2_PlumForm',verts,faces,'Chrome',pearl.parent,pearl.location,smooth_faces=True,uv=uv)
pearl.data=replacement.data;bpy.data.objects.remove(replacement,do_unlink=True)
for o in b.col.objects:
    if o.type=='CURVE' and 'PearlRib' in o.name:
        spline=o.data.splines[0];count=len(spline.points)
        direction=Vector(spline.points[count//2].co[:2]).normalized()
        for j,p in enumerate(spline.points):
            t=j/(count-1);rr=.185*math.sin(math.pi*t)**.72*(.70+.60*t)
            p.co=(rr*direction.x,rr*direction.y,-.52*t,1)

data['parts']+=parts;data['part_count']=len(data['parts']);data['interactive_rig']=rig
data['source_blend']='blender/collection/F_refined.blend'
data['refinement']={'version':1,'reference':'production/interaction_refinement/images/F_structure_controls.png','original_preserved':True,'status':'Differential, vernier, brake and weight form refinement; further visual review required.'}

def interactive(trim,brake):
    for item in rig:
        node=bpy.data.objects[item['name']];kind=item['kind']
        if kind in ['trim_gear','counter_gear']:node.rotation_euler.y=trim*(2.2 if kind=='trim_gear' else -3.6)
        elif kind=='trim_carriage':
            a=math.radians(141-trim*28)
            node.location=(-.1+.836*math.cos(a),-.147,1.8+.836*math.sin(a));node.rotation_euler.y=-a
        else:
            home=C.inverted()@Vector((*item['home']['p'],1))
            node.location=home.xyz+Vector(((.014 if kind=='brake_left' else -.014)*brake,0,0))

# Add a readable control demonstration after the preserved opening/explosion take.
for frame,trim,brake in [(1,.25,0),(361,.25,0),(385,-.75,0),(421,.80,0),(439,.80,1),(473,0,1),(497,0,0),(529,.25,0),(553,.25,0)]:
    interactive(trim,brake)
    for item in rig:
        obj=bpy.data.objects[item['name']];obj.keyframe_insert('location',frame=frame);obj.keyframe_insert('rotation_euler',frame=frame)
for frame,amount in [(361,0),(385,1),(529,1),(553,0)]:
    for control in data['controls']:
        obj=bpy.data.objects[control['name']];p=control['samples'][round(amount*100)]
        imported=Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))
        obj.matrix_basis=C.inverted()@imported@C
        obj.keyframe_insert('location',frame=frame)
        obj.keyframe_insert('rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_euler',frame=frame)
        obj.keyframe_insert('scale',frame=frame)
scene.frame_end=553
scene.timeline_markers.new('DIFFERENTIAL — bias',frame=385)
scene.timeline_markers.new('BRAKE — catch',frame=439)
scene.timeline_markers.new('EQUILIBRIUM — release',frame=497)
scene.frame_set(1);interactive(.25,0)
for item in rig:item['home']=pose(bpy.data.objects[item['name']].matrix_basis)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:
        absolute=pathlib.Path(bpy.path.abspath(image.filepath))
        if not absolute.exists():
            candidate=ROOT/'app/assets'/absolute.name
            if candidate.exists():image.filepath=str(candidate)
        image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))

target=ROOT/'app/assets/collection/models/F_refined.glb'
(target.with_suffix('.json')).write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/data['source_blend']))
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
from optimize_runtime_meshes import optimize
optimize(target)
print('F_REFINED_EXPORTED',len(rig),'interactive nodes;',len(data['parts']),'parts',flush=True)
