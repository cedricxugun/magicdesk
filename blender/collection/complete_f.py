"""Finish F's physical rig and emitter hardware as a NEW editable source.
Reads F_refined.blend; preserves all prior revisions and the authoritative base.
The runtime solves the same closed four-bar geometry used by these samples.
"""
import bpy, bmesh, math, json, pathlib, sys
from mathutils import Vector, Matrix, Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder, C, pose, smooth
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/F_refined.blend'))
scene=bpy.context.scene;scene.frame_set(1)
data=json.loads((ROOT/'app/assets/collection/models/F_refined.json').read_text(encoding='utf-8'))
b=Builder.__new__(Builder);b.id='F3';b.title='Lagrange — physical instrument';b.scene=scene
b.col=bpy.data.collections['MODULE_F'];b.root=bpy.data.objects['F_MODULE'];b.upper=bpy.data.objects['F_UPPER']
b.serial=20000;b.parts=[];b.controls=[];b.motions=[];b.sockets={};b.qa_shells=[];b.extra={}
b.mats={m.name.removeprefix('Collection_'):m for m in bpy.data.materials if m.name.startswith('Collection_')}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
for obj in b.col.all_objects:obj.animation_data_clear()
b.material('FieldMetal',(.69,.49,.20),.95,.24)
b.material('Signal',(1,.60,.20),.65,.22,emission=3)
front=(math.pi/2,0,0)
H=Vector((.4,-.055,2.64));Q=Vector((.4,-.055,.934))
spine=bpy.data.objects['F_P_ContinuousSpine']
b.beam('CoaxialCounterAxle',H,H+Vector((0,-.18,0)),.027,'Chrome',spine)
brake_parent=bpy.data.objects['F2_P_FrictionBrake']
rotor=b.empty('F3_BrakeRotor',brake_parent,H)
for obj in list(brake_parent.children):
    if 'BrakeDisc' in obj.name or 'DiscPolishedTrack' in obj.name:
        obj.parent=rotor;obj.location-=H
for i in range(3):
    a=i*math.tau/3
    b.cube('BrakeRotorIndex',(.003,.003,.020),'Black',rotor,(.066*math.cos(a),-.114,.066*math.sin(a)),.0006,(0,-a,0))

# The C-frame itself is the grounded link. Move the lower fixed bearing to its
# real foot; remove the old short vertical placeholder yoke near the upper axle.
for obj in list(spine.children):
    if 'FixedPivotYoke' in obj.name:bpy.data.objects.remove(obj,do_unlink=True);continue
    if (obj.location-Vector((.4,-.055,2.32))).length<.001:obj.location+=Q-Vector((.4,-.055,2.32))

# Each shared pivot gets one bearing stack and one open clevis eye, not two
# overlapping solid bearings from separate link parts.
for name in ['F_C_Coupler_end0','F_C_Coupler_end1']:
    parent=bpy.data.objects[name]
    for child in list(parent.children_recursive):bpy.data.objects.remove(child,do_unlink=True)
    eye=b.sleeve('CouplerEye',.052,.027,.035,'Steel',parent);eye.rotation_euler=front
    b.torus('ClevisPolishedLip',.047,.004,'Chrome',parent,(0,-.023,0),front)
    b.torus('ClevisPolishedLip',.047,.004,'Chrome',parent,(0,.023,0),front)

# Whole suspended assemblies pivot at their attachment, including their neck.
guides=[]
for label,hanger_name in [('Plumb','F_C_PearlHanger'),('Prism','F_C_PrismHanger')]:
    hanger=bpy.data.objects[hanger_name]
    children=list(hanger.children)
    pivot=b.empty('F3_'+label+'Pendulum',hanger)
    for obj in children:obj.parent=pivot
    for side in [-1,1]:
        b.beam('SuspensionYoke',(side*.075,0,.035),(side*.075,0,-.055),.012,'Chrome',hanger)
        b.cyl('GimbalTrunnion',.029,.022,'Chrome',hanger,(side*.071,0,-.012),(0,math.pi/2,0))
        guide=b.empty('F3_'+label+'TransportGuide'+str(side),hanger,(side*.044,0,-.155))
        b.cube('TransportJaw',(.027,.047,.080),'Steel',guide,bevel=.008)
        b.cube('CeramicJawPad',(.009,.038,.056),'Ivory',guide,(-side*.018,0,0),.004)
        guides.append({'name':guide.name,'home':list((C@guide.location.to_4d()).xyz),'sign':side})
    b.torus('SuspensionSeal',.031,.006,'Red',hanger,(0,0,-.016))
old_swing=bpy.data.objects['F_R_PearlSwing'];old_swing.rotation_euler=(0,0,0)
data['motions']=[m for m in data['motions'] if m['name']!='F_R_PearlSwing']

# A visible torsion spring, shaft coupling, cable housing and travel stops make
# the preload control a plausible actuator rather than a mysteriously moved mass.
spring_parent=b.empty('F3_SpringPreload',bpy.data.objects['F2_P_Differential'],H)
b.coil(spring_parent,(0,.13,0),.079,.16,9,(0,1,0))
for y in [.035,.225]:
    b.cyl('SpringEndBearing',.066,.027,'Chrome',spring_parent,(0,y,0),front)
    b.torus('SpringBearingSeal',.058,.005,'Red',spring_parent,(0,y-.019,0),front)
b.beam('FixedSpringArm',H+Vector((0,.22,0)),H+Vector((-.10,.22,.095)),.019,'Steel',spine)
b.beam('PreloadArm',(0,.03,0),(.098,.03,.018),.016,'Chrome',spring_parent)
b.tube('BowdenHousing',[(-.1+.90*math.cos(math.radians(a)),.055,1.8+.90*math.sin(math.radians(a))) for a in range(69,174)],.014,'Black',spine)
for a in [75,100,125,150,170]:
    p=(-.1+.90*math.cos(math.radians(a)),.052,1.8+.90*math.sin(math.radians(a)))
    b.cyl('CableClamp',.021,.042,'Chrome',spine,p,front,24)

# Recessed conductors and contacts follow the real crescent surface.
emitters=[]
for segment in range(5):
    start=90+segment*30;angles=[math.radians(start+i*.9) for i in range(30)]
    points=[(-.1+.887*math.cos(a),-.083,1.8+.887*math.sin(a)) for a in angles]
    b.tube('ConductorRecess',points,.015,'Black',spine)
    b.tube('ConductorGlass',[(x,y-.014,z) for x,y,z in points],.006,'Signal',spine)
    for endpoint in [points[0],points[-1]]:
        contact=b.empty('F3_FieldContact_'+str(len(emitters)),spine,Vector(endpoint)+Vector((0,-.028,0)))
        b.cyl('ContactHousing',.026,.020,'Chrome',contact,(0,0,0),front,32)
        b.cyl('ContactLens',.015,.006,'Signal',contact,(0,-.014,0),front,32)
        emitters.append(contact.name)

receiver=b.empty('F3_P_Receiver',b.upper)
data['parts'].append({'name':receiver.name,'home':pose(receiver.matrix_basis),'offset':[0,.12,.38],'stage':.52})
lift=b.empty('F3_ReceiverLift',receiver)
slide=b.empty('F3_ReceiverSlide',lift)
dish=b.empty('F3_ReceiverDish',slide,(-.228,-.48,.812))
for side in [-1,1]:
    x=-.228+side*.15
    b.beam('ReceiverSlideRail',(x,-.62,.78),(x,-.18,.78),.012,'Chrome',lift)
    b.cube('ReceiverSlideShoe',(.045,.12,.030),'Steel',slide,(x,-.48,.785),.008)
    for y in [-.60,-.20]:b.screw(lift,(x,y,.791),(0,0,1),.009)
for degrees in [90,210,330]:
    a=math.radians(degrees);x=-.228+.15*math.cos(a);y=-.48+.15*math.sin(a)
    b.cyl('ReceiverPistonHousing',.026,.21,'Steel',receiver,(x,y,.713),n=32)
    b.torus('ReceiverPistonWiper',.026,.004,'Red',receiver,(x,y,.816))
    b.cyl('ReceiverLiftRod',.015,.255,'Chrome',lift,(x,y,.690),n=32)
b.cyl('ReceiverWell',.33,.031,'Steel',dish)
b.cyl('ReceiverMachinedFace',.29,.010,'Chrome',dish,(0,0,.024))
for r in [.115,.18,.245,.292,.327]:b.torus('ReceiverGroove',r,.004,'Black',dish,(0,0,.032))
for i in range(48):
    a=i*math.tau/48
    b.beam('ReceiverGraduation',(.267*math.cos(a),.267*math.sin(a),.033),((.288 if i%4==0 else .278)*math.cos(a),(.288 if i%4==0 else .278)*math.sin(a),.033),.0015,'FieldMetal',dish)
b.torus('ReceiverContact',.115,.006,'Signal',dish,(0,0,.038))
b.cyl('ReceiverCenter',.043,.010,'Black',dish,(0,0,.034),n=48)
b.cyl('ReceiverOptic',.018,.004,'Signal',dish,(0,0,.041),n=32)
for a in [0,120,240]:
    a=math.radians(a);b.screw(dish,(.309*math.cos(a),.309*math.sin(a),.027),(0,0,1),.010)

prism=bpy.data.objects['F3_PrismPendulum']
for x in [-.115,.115]:
    for y in [-.09,.09]:
        b.screw(prism,(x,y,-.143),(0,0,1),.010)
        b.cyl('WeightServicePlug',.013,.015,'Red',prism,(x,y,-.591),n=24)
b.torus('PrismFieldCollar',.028,.006,'Signal',prism,(0,0,-.11))
prism_tip=b.empty('F3_PrismTip',prism,(0,0,-.603))

# Authored metal swarf mesh used by the runtime's actual 3D instances.
prototype=b.empty('F3_FX_Prototypes',b.upper,(0,0,1.25))
foil=b.ribbon('Swarf',[(0,0,-.036),(.005,.003,-.014),(-.003,.006,.012),(0,0,.036)],[.002,.006,.006,.001],.0015,'FieldMetal',prototype)
foil.name='F3_SwarfPrototype'
tick_root=b.empty('F3_TickPrototypeRoot',prototype)
tick=b.cube('VernierTick',(.007,.005,.060),'FieldMetal',tick_root,bevel=.002)
tick.name='F3_VernierTickPrototype'

def kinematics(angle):
    upper=H+Vector((.82*math.cos(angle),0,.82*math.sin(angle)))
    d=upper-Q;length=d.length;e=d/length
    a=(1.01**2-.50**2+length*length)/(2*length)
    h=math.sqrt(max(.000001,1.01**2-a*a))
    lower=Q+e*a+Vector((e.z,0,-e.x))*h
    return upper,lower

def set_pose(amount):
    angle=math.radians(-80+30*smooth(amount))
    offset=math.radians(-65-55*smooth(amount))
    top,lower=kinematics(angle)
    left=H+Vector((0,-.18,0));left_end=left+Vector((.66*math.cos(angle+offset),0,.66*math.sin(angle+offset)))
    links={'UpperFourBar':(H,top),'LowerFourBar':(Q,lower),'Coupler':(top,lower),'CounterArm':(left,left_end)}
    for name,(a,c) in links.items():
        obj=bpy.data.objects['F_C_'+name];d=c-a
        obj.location=(a+c)*.5;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=d.to_track_quat('Z','Y');obj.scale=(1,1,d.length)
        for i,p in enumerate([a,c]):bpy.data.objects['F_C_'+name+'_end'+str(i)].location=p
    bpy.data.objects['F_C_PrismHanger'].location=lower;bpy.data.objects['F_C_PearlHanger'].location=left_end
    bpy.context.view_layer.update()

samples={c['name']:[] for c in data['controls']}
for i in range(101):
    set_pose(i/100)
    for name in samples:samples[name].append(pose(bpy.data.objects[name].matrix_basis))
for c in data['controls']:c['samples']=samples[c['name']]
set_pose(0)
data['f_physics']={'plumb_pivot':'F3_PlumbPendulum','prism_pivot':'F3_PrismPendulum','transport_guides':guides,'spring_preload':spring_parent.name,'brake_rotor':rotor.name,'receiver_lift':lift.name,'receiver_slide':slide.name,'upper_length':.82,'lower_length':1.01,'coupler_length':.50,'ground_height':1.706,'counter_depth':.18,'gravity':9.81,'reference':'production/F_complete/PHYSICS.md'}
data['f_fx']={'contacts':emitters,'receiver':dish.name,'prism_tip':prism_tip.name,'prototype':foil.name,'tick_prototype':tick.name,'atlas':'res://assets/collection/art/F/field_atlas.png'}
data['part_count']=len(data['parts']);data['source_blend']='blender/collection/F_complete.blend'
data['refinement']={'version':2,'motion_board':'production/F_complete/images/F_motion_vfx.png','signature_board':'production/F_complete/images/F_calibration_signature.png','physical_model':'Analytic closed four-bar, two spherical mass hangers, torsion preload, friction brake. Actuated transport clutch.'}

# Use the real shared base and control cassette in the Blender reference too.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/frame_shared.glb'))
added=set(bpy.data.objects)-before
frame=next(o for o in added if o.type=='MESH')
base=bpy.data.objects.get('BASE_FIXED_DisplayMesh')
if base:base.data=frame.data.copy();base.matrix_world=frame.matrix_world
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
for index in range(1,6):
    mount=bpy.data.objects.get('BUTTON_%02d_MOUNT'%index)
    if mount:
        for obj in [mount]+list(mount.children_recursive):obj.hide_render=True;obj.hide_set(True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/models/S.glb'))
selector_added=set(bpy.data.objects)-before
for obj in selector_added:
    if obj.name.startswith('S_WIDGET_LIBRARY'):
        for child in [obj]+list(obj.children_recursive):child.hide_render=True;child.hide_set(True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/control_library.glb'))
library_added=set(bpy.data.objects)-before
for slot,kind in enumerate(['rotary','hold','detent','gauge','service'],1):
    root=next(o for o in library_added if o.name=='CTRL_'+kind)
    mount=bpy.data.objects.get('BUTTON_%02d_MOUNT'%slot)
    root.parent=None;root.location=mount.matrix_world.translation
    root.rotation_euler=(0,0,math.atan2(root.location.y,root.location.x)+math.pi/2)
    for obj in [root]+list(root.children_recursive):library_added.discard(obj)
for obj in library_added:bpy.data.objects.remove(obj,do_unlink=True)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:
        absolute=pathlib.Path(bpy.path.abspath(image.filepath))
        if not absolute.exists():
            candidate=ROOT/'app/assets'/absolute.name
            if candidate.exists():image.filepath=str(candidate)
        image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
scene.frame_end=720;scene.render.engine='CYCLES';scene.cycles.samples=64
scene.timeline_markers.clear();scene.timeline_markers.new('Await physical take bake',frame=1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/data['source_blend']))
out=ROOT/'app/assets/collection/models/F_complete.glb'
out.with_suffix('.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
from optimize_runtime_meshes import optimize
optimize(out)
print('F_COMPLETE_GEOMETRY',data['part_count'],'parts, grounded four-bar, two gimbals, authored emitter hardware',flush=True)
