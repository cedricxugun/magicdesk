"""Surgical R3 lower drive replacement; preserves saved R2 boat/sail meshes and actions."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
from ship_wave_kinematics import *
b=Builder('GS3','Connected tide engine')
b.material('Porcelain',(.78,.74,.66),0,.27,normal='ceramic_glaze_normal.png',coat=.38)
b.material('Brass',(.52,.32,.12),1,.28,normal='metal_normal.png')
b.material('Nickel',(.45,.50,.53),1,.27,normal='metal_normal.png')
b.material('Dark',(.08,.10,.11),.85,.34)
b.material('Enamel',(.16,.007,.012),0,.25,coat=.5)
source=ROOT/'blender/collection/G_ship_r2.blend';source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=list(src.objects)
for obj in dst.objects:
    if obj and not obj.users_collection:b.col.objects.link(obj)
root=bpy.data.objects['GS2_Ship'];root.parent=None
keep={root,*root.children_recursive}
for obj in list(bpy.data.objects):
    if obj not in keep:bpy.data.objects.remove(obj,do_unlink=True)
b.upper=root
# Keep only installed foot/gimbal supports and upper hull. Preserve ribbon geometry independently.
ribbons=[]
for i in range(3):
    wave=bpy.data.objects['GS2_Wave'+str(i)];wave.animation_data_clear()
    for child in list(wave.children):
        if any(k in child.name for k in ['ShapedTidalRibbon','RibbonRolledEdge']):
            child.location.z-=[.015,.033,.033][i]
            if i==1:
                points=child.data.vertices if child.type=='MESH' else child.data.splines[0].points
                for p in points:p.co.z-=.012*math.sin(3*math.pi*(p.co.x+.33)/.66+math.tau/3)
        else:bpy.data.objects.remove(child,do_unlink=True)
    ribbons.append(wave)
retain=['BlindMount','MountRim','CaptiveBolt','BoltSlot','FixedPitchFork','PitchBearing','PitchYoke','GS2_Wave']
for child in list(root.children):
    if any(k in child.name for k in retain):continue
    for obj in list(child.children_recursive)+[child]:bpy.data.objects.remove(obj,do_unlink=True)

def ring(name,r,inside,depth,material,parent,loc,axis=(0,1,0)):
    obj=b.sleeve(name,r,inside,depth,material,parent,loc,64)
    obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();obj.modifiers[0].width=.00045
    return obj

def fastener(parent,loc,r=.003,axis=(0,-1,0)):
    q=Vector(axis).to_track_quat('Z','Y');p=Vector(loc)
    b.cyl('RecessedCapScrew',r,.002,'Nickel',parent,p,q,12)
    b.cube('ScrewSlot',(r*1.2,.0007,.0003),'Dark',parent,p+Vector(axis)*.00105,.0001,q)

def pipe(name,pts,r,mat,parent):return b.tube(name,pts,r,mat,parent,2)

def plate(name,outline,depth,mat,parent,loc=(0,0,0)):
    # Polygon in X/Z extruded along Y. Concave caps are triangulated by Blender/glTF.
    n=len(outline);verts=[(x,y,z) for y in [-depth/2,depth/2] for x,z in outline]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    obj=b.fast['fast_instance'](b.name(name),verts,faces,mat,parent,loc,smooth_faces=False)
    bevel=obj.modifiers.new('Machined edge break','BEVEL');bevel.width=.00045;bevel.segments=3
    return obj

def bore(obj,center,radius,depth):
    if obj.data.users>1:obj.data=obj.data.copy()
    cutter=b.cyl('CutTool',radius,depth,'Dark',obj.parent,center,(math.pi/2,0,0),48)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Machined through bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.ops.object.modifier_move_up(modifier=mod.name) if len(obj.modifiers)>1 else None
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)

def wheel(teeth,parent,y,name):
    obj=plate(name,gear_outline(teeth),.007,'Brass',parent,(0,y,0))
    bore(obj,(0,y,0),.0056,.025)
    if teeth==36:
        for i in range(6):
            a=i*math.tau/6;center=(.032*math.cos(a),y,.032*math.sin(a))
            bore(obj,center,.012,.025)
    else:
        for i in range(3):
            a=i*math.tau/3;bore(obj,(.016*math.cos(a),y,.016*math.sin(a)),.004,.025)
    ring(name+'Hub',.010,.0056,.012,'Nickel',parent,(0,y,0))
    # Visible key joins hub and axle. No independent floating rotor.
    b.cube(name+'Key',(.003,.010,.002),'Dark',parent,(0,y,.0055),.0002)
    return obj

shaft=b.empty('GS3_CommonShaft',root,(A[0],0,A[1]))
b.cyl('GroundCamshaft',.0055,.328,'Nickel',shaft,(0,-.012,0),(math.pi/2,0,0),64)
b.cube('AxleWitnessStripe',(.001,.298,.0003),'Enamel',shaft,(0,-.01,.0055),.0001)
main=b.empty('GS3_DrivenGear',shaft,(0,-.170,0));main.rotation_euler.y=-GEAR_ANGLE
wheel(36,main,0,'Driven36Involute')
pinion=b.empty('GS3_Pinion',root,(PINION[0],-.170,PINION[1]));wheel(18,pinion,0,'Input18Involute')
b.cyl('InputSpindle',.0055,.060,'Nickel',pinion,(0,.019,0),(math.pi/2,0,0),48)
# Continuous stationary pivot axle for the three independently rocking arms.
b.cyl('RockerPivotAxle',.004,.284,'Nickel',root,(P[0],.012,P[1]),(math.pi/2,0,0),48)
# Open triangulated bearing cheeks connect both axles to the existing small foot.
for side in [-1,1]:
    y=side*.137
    pipe('FrameHeel',[(.040,side*.044,.039),(-.050,y,.054),(-.059,y,.093),(A[0],y,A[1]-.013)],.007,'Nickel',root)
    pipe('FrameUpperFork',[(-.050,y,.054),(.037,y,.133),(P[0]+.010,y,P[1])],.0055,'Porcelain',root)
    ring('ShaftBearingHousing',.013,.009,.012,'Porcelain',root,(A[0],y,A[1]))
    ring('ShaftBronzeBush',.0088,.0058,.0125,'Brass',root,(A[0],y,A[1]))
    ring('PivotBearingHousing',.010,.0044,.010,'Brass',root,(P[0],y,P[1]))
    for x,z in [(A[0],A[1]),(P[0],P[1])]:
        ring('BearingRetainer',.011 if x==A[0] else .008,.006 if x==A[0] else .0044,.002,'Dark',root,(x,y+side*.008,z))
    pipe('OpenFrameBrace',[(.040,side*.044,.039),(-.047,side*.052,.041),(-.080,side*.115,.081),(A[0]-.013,y,A[1])],.004,'Brass',root)
# Pinion bearing stays behind gear plane, supported by the open front cheek.
ring('InputBronzeBearing',.009,.0058,.018,'Brass',root,(PINION[0],-.139,PINION[1]))
pipe('InputBearingLeg',[(PINION[0],-.139,PINION[1]-.015),(-.050,-.137,.054)],.006,'Porcelain',root)
for y in [-.153,.153]:ring('ShaftThrustCollar',.008,.00555,.005,'Dark',shaft,(0,y,0))

cams=[];rockers=[];rollers=[];rods=[];springs=[]
for i,y in enumerate([-.10,0,.10]):
    phase=i*math.tau/3
    cam=b.empty('GS3_Cam'+str(i),shaft,(0,y,0));cam.rotation_euler.y=-phase;cams.append(cam)
    disk=b.cyl('EccentricGroundLobe',CAM_RADIUS,.009,'Brass',cam,(ECCENTRIC,0,0),(math.pi/2,0,0),96)
    bore(disk,(0,0,0),.0056,.028)
    ring('CamHub',.009,.0056,.014,'Dark',cam,(0,0,0))
    for side in [-1,1]:
        fastener(cam,(ECCENTRIC+.011,side*.005,0),.002,(0,side,0))
    rocker=b.empty('GS3_Rocker'+str(i),root,(P[0],y+.010,P[1]));rockers.append(rocker)
    # Narrow tapered arm, collars with genuine pivot bores, and a roller on the inboard face.
    arm=plate('ForgedRocker',[(-OUTPUT,.004),(-.006,.007),(0,.008),(INPUT,.0035),(INPUT,-.0035),(0,-.008),(-.006,-.007),(-OUTPUT,-.004)],.004,'Nickel',rocker)
    bore(arm,(0,0,0),.0044,.020)
    bore(arm,(-OUTPUT,0,0),.0031,.020)
    ring('RockerOutputBush',.005,.0031,.004,'Brass',rocker,(-OUTPUT,0,0))
    ring('RockerBush',.0085,.0044,.006,'Brass',rocker,(0,0,0))
    spring_root=b.empty('GS3_ReturnSpring'+str(i),root,(P[0],y+.020,P[1]))
    ring('FixedSpringCollar',.008,.0043,.004,'Dark',root,(P[0],y+.017,P[1]))
    rest=solve(phase)['theta']+math.pi-math.pi/2
    point=Vector((.018*math.cos(rest),-.003,.018*math.sin(rest)))
    b.cyl('SpringFixedAnchor',.0014,.006,'Nickel',spring_root,point+Vector((0,.001,0)),(math.pi/2,0,0),24)
    b.beam('SpringAnchorSupport',(.0075*math.cos(rest),-.005,.0075*math.sin(rest)),point+Vector((0,-.002,0)),.001,'Dark',spring_root)
    spring=pipe('AnchoredTorsionSpring',spring_points(solve(phase)['theta'],i),.00065,'Nickel',spring_root);springs.append(spring)
    b.cyl('SpringMovingAnchor',.0014,.017,'Nickel',rocker,(-.018,.008,0),(math.pi/2,0,0),24)
    b.cyl('FollowerAxle',.0024,.017,'Nickel',rocker,(INPUT,-.006,0),(math.pi/2,0,0),32)
    roller=b.empty('GS3_Roller'+str(i),rocker,(INPUT,-.010,0));rollers.append(roller)
    ring('HardenedRoller',ROLLER_RADIUS,.0026,.008,'Dark',roller,(0,0,0))
    ring('RollerChromeLip',.0058,.0026,.001,'Nickel',roller,(0,-.0045,0))
    for x in [INPUT]:fastener(rocker,(x,.003,0),.003)
    # Separate rigid connecting rod with eye bearings at its exact analytic endpoints.
    rod=b.empty('GS3_LinkRod'+str(i),root);rods.append(rod)
    b.beam('PolishedLink',(.005,0,0),(ROD_LENGTH-.005,0,0),.0023,'Nickel',rod)
    for x in [0,ROD_LENGTH]:
        ring('RodEndEye',.005,.0031,.004,'Brass',rod,(x,0,0))
        b.cyl('RodEndPin',.0028,.024,'Nickel',rod,(x,-.003,0),(math.pi/2,0,0),32)
        fastener(rod,(x,.003,0),.003)
    wave=ribbons[i]
    for x in [.070,.106]:
        b.cyl('GroundLinearGuide',.0025,.074,'Nickel',root,(x,y+.020,.185),n=32)
        ring('SliderBronzeSleeve',.0046,.0028,.012,'Brass',wave,(x,.020,-.005),(0,0,1))
        pipe('GuideMount',[(x,y+.020,.145),(x,y+.045,.132),(x,y+.045,.090),(.042,y+.045,.060)],.0023,'Dark',root)
        ring('GuideEndStop',.0042,.0026,.003,'Dark',root,(x,y+.020,.223),(0,0,1))
    b.beam('Crosshead',(.0746,.020,-.005),(.1014,.020,-.005),.0033,'Nickel',wave)
    for ear_y in [.014,.026]:
        ring('SliderClevisEar',.005,.0031,.003,'Nickel',wave,(.088,ear_y,-.015))
        b.beam('SliderClevisWeb',(.088,ear_y,-.010),(.088,.020,-.005),.002,'Dark',wave)
    t=(SLIDER_X+.33)/.66;blade=.054-[.015,.033,.033][i]+(.010 if i==1 else .022)*math.sin(3*math.pi*t+phase)+.027*abs(2*t-1)**3
    pipe('WaveAttachment',[(SLIDER_X,.020,-.005),(SLIDER_X,.020,blade),(SLIDER_X,0,blade)],.003,'Brass',wave)
    b.cyl('RibbonClamp',.004,.010,'Nickel',wave,(SLIDER_X,0,blade),(math.pi/2,0,0),32)

scene=bpy.context.scene;scene.render.fps=30;scene.frame_end=451
phase_clock=0.0
for frame in range(1,452):
    t=(frame-1)/30
    def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
    energy=smooth((t-4)/1.3)*(1-smooth((t-10)/2.3))
    if frame>1:phase_clock+=(.9+.9*energy)/30
    shaft.rotation_euler.y=-phase_clock;shaft.keyframe_insert('rotation_euler',frame=frame)
    pinion.rotation_euler.y=-(GEAR_ANGLE+math.pi+math.pi/18-2*phase_clock);pinion.keyframe_insert('rotation_euler',frame=frame)
    for i,(rocker,rod,wave) in enumerate(zip(rockers,rods,ribbons)):
        phase=phase_clock+i*math.tau/3;s=solve(phase);y=[-.10,0,.10][i]
        for point,coords in zip(springs[i].data.splines[0].points,spring_points(s['theta'],i)):
            point.co=(*coords,1);point.keyframe_insert('co',frame=frame)
        rocker.rotation_euler.y=-s['theta'];rocker.keyframe_insert('rotation_euler',frame=frame)
        rod.location=(s['output'][0],y+.020,s['output'][1]);rod.rotation_euler.y=-s['rod_angle']
        rod.keyframe_insert('location',frame=frame);rod.keyframe_insert('rotation_euler',frame=frame)
        wave.location=(0,y,s['wave_z']);wave.keyframe_insert('location',frame=frame)
        # Rolling surface velocity around the eccentric lobe, visual axle drive.
        rollers[i].rotation_euler.y=phase*CAM_RADIUS/ROLLER_RADIUS;rollers[i].keyframe_insert('rotation_euler',frame=frame)
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(1);bpy.context.view_layer.update()
meta=json.loads((ROOT/'app/assets/collection/components/G_ship_r2.json').read_text())
meta.update({'source_blend':'blender/collection/G_ship_r3.blend','status':'R3 connected wave engine WIP; independent component only','reference':'production/G_optical_curator/ship_r3/wave_drive_design.png','preserved_r2_sha256':source_hash})
meta['rig'].update({'cams':[o.name for o in cams],'shaft':shaft.name,'pinion':pinion.name,'rockers':[o.name for o in rockers],'rollers':[o.name for o in rollers],'rods':[o.name for o in rods]})
meta['wave_drive_version']=3
meta['springs']=[{'node':o.name,'root':o.parent.name,'channel':i} for i,o in enumerate(springs)]
out=ROOT/'app/assets/collection/components';(out/'G_ship_r3.json').write_text(json.dumps(meta,indent=2)+'\n')
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(out/'G_ship_r3.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
# Studio is not exported into the component.
reference=b.empty('R3_Reference')
b.cyl('ReferenceOriginalDisc',.42,.02352,'Black',reference,(0,0,-.005),n=128)
world=bpy.data.worlds.new('R3Studio');world.use_nodes=True;scene.world=world
tex=world.node_tree.nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(ROOT/'app/assets/studio_small_09_4k.exr'),check_existing=True)
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Strength'].default_value=.25;world.node_tree.links.new(tex.outputs['Color'],bg.inputs['Color'])
for i,(loc,power) in enumerate([((-2,-3,3),150),((2,1,3),180)]):
    light=bpy.data.lights.new('R3Studio'+str(i),'AREA');light.energy=power;light.shape='DISK';light.size=2
    obj=bpy.data.objects.new(light.name,light);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,.46))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('R3Camera');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);scene.camera=camera
camera.location=(1.5,-3.5,1.4);camera.rotation_euler=(Vector((0,0,.46))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=1.22
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.film_transparent=True
source_out=ROOT/'blender/collection/G_ship_r3.blend'
if source_out.exists():
    backup=ROOT/'blender/collection/checkpoints'/('G_ship_r3-'+hashlib.sha256(source_out.read_bytes()).hexdigest()[:12]+'.blend');backup.write_bytes(source_out.read_bytes())
bpy.ops.wm.save_as_mainfile(filepath=str(source_out));bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(source_out))
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print('SHIP_R3_SAVED',str(source_out),flush=True)
