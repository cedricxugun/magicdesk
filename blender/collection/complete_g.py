"""G's second source: real bored laminae, indexing shoes and optical carriages.
Builds a sibling source; never opens or overwrites G.blend or the HELIOS source.
Dimensions are metres, Blender Z up; metadata converted to Godot Y up.
"""
import bpy, math, json, pathlib, sys, bmesh
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder, C, pose, window
from optimize_runtime_meshes import optimize
b=Builder('G3','Palimpsest / optical archive')
b.material('Signal',(1,.57,.19),.25,.19,emission=2)
b.material('Porcelain',(.86,.83,.75),0,.19,coat=.55)
b.material('Nickel',(.60,.64,.66),.98,.23)
b.material('Satin',(.34,.38,.39),.94,.29)
front=(math.pi/2,0,0)
def legend(parent,text,loc,side=1,size=.035):
    data=bpy.data.curves.new(b.name('EngravedLegend'),'FONT');data.body=text;data.align_x='CENTER';data.size=size;data.extrude=.00035;data.bevel_depth=.00010
    obj=bpy.data.objects.new(data.name,data);b.col.objects.link(obj);obj.parent=parent;obj.location=loc;obj.rotation_euler=front;obj.scale.x=side;data.materials.append(b.mats['Black']);return obj
b.pedestal_mount(.30)
spine=b.part('Spine',(0,.85,.70),.75)
b.cyl('GroundedSpindle',.083,1.99,'Satin',spine,(0,0,1.67))
for z in [.82,1.04,1.42,1.88,2.24,2.62,2.70]:
    b.cyl('SpineBearing',.146,.071,'Nickel',spine,(0,0,z))
    b.torus('BearingGroove',.147,.004,'Black',spine,(0,0,z+.020))
    for i in range(6):
        a=i*math.tau/6;b.screw(spine,(.127*math.cos(a),.127*math.sin(a),z+.038),r=.010)
for a in [0,math.pi/2,math.pi,math.pi*1.5]:
    x=.116*math.cos(a);y=.116*math.sin(a)
    b.beam('SpineTieRod',(x,y,.89),(x,y,2.66),.012,'Nickel',spine)
    b.beam('SpineSignal',(x*.82,y*.82,1.05),(x*.82,y*.82,2.56),.008,'Signal',spine)
b.cyl('Cap',.16,.05,'Black',spine,(0,0,2.75))
b.torus('CapRim',.153,.012,'Nickel',spine,(0,0,2.776))

def bored_plate(name,parent,width,height,depth,center,hole_radius=.134):
    obj=b.cube(name,(width,depth,height),'Porcelain',parent,center,.041)
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    # Cylinder is an actual through bore, not a dark disk over an opaque plate.
    hole=b.cyl('TEMP_BORE',hole_radius,depth+.20,'Black',parent,(center[0],0,-.09),front,96)
    bpy.context.view_layer.update()
    modifier=obj.modifiers.new('Actual optical aperture','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=hole
    bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(hole,do_unlink=True)
    bevel=obj.modifiers.new('Glazed bore lip','BEVEL');bevel.width=.003;bevel.segments=3
    b.qa_shells.append(obj.name)
    return obj

leaf_meta=[]
for side in [-1,1]:
    for layer in range(3):
        index=(0 if side==-1 else 3)+layer
        part=b.part('Leaf'+str(index),(side*(.20+layer*.24),(layer-1)*.85,.12+layer*.15),.16+layer*.07)
        # Extract into separate depth bays before wider lateral spread.
        b.extraction_route(part,[(0,(0,0,0)),(.38,(0,(layer-1)*.80,.0)),(1,(side*(.22+layer*.25),(layer-1)*.90,.12+layer*.15))])
        def leaf_pose(o,t,s=side,k=layer):
            u=window(t,.32,1);o.location=(s*(.22+.14*u),(k-1)*(.205+.135*u),1.79)
        node=b.control('Leaf'+str(index),part,leaf_pose)
        # Local pages extend toward +X on both banks; mirror by 180 degrees,
        # keeping positive scales for the exported normal and tangent frames.
        face=b.empty('G3_Face'+str(index),node);face.rotation_euler.z=0 if side==1 else math.pi
        bored_plate('GlazedLamina',face,.72,1.34,.050,(.47,0,0))
        for y in [-.039,.039]:
            barrel=b.sleeve('ApertureBarrel',.153,.120,.048,'Nickel',face,(.47,y,-.09));barrel.rotation_euler=front
            b.torus('OpticalBaffle',.126,.005,'Black',face,(.47,y*1.60,-.09),front)
            b.torus('BoreConductor',.133,.003,'Signal',face,(.47,y*1.68,-.09),front)
            for x in [.15,.79]:
                b.beam('PageEdgeRail',(x,y,-.57),(x,y,.57),.009,'Nickel',face)
                for z in [-.57,.57]:b.screw(face,(x,y*1.16,z),(0,1 if y>0 else -1,0),.013)
            for radius in [.192,.211]:
                for begin in [12,112,222]:
                    pts=[(.47+radius*math.cos(math.radians(a)),y*.73,-.09+radius*math.sin(math.radians(a))) for a in range(begin,begin+62,2)]
                    b.tube('EngravedOpticalScale',pts,.0018,'Copper',face,1)
            for k in range(12):
                z=-.49+k*.086;b.beam('Graduation',(.71,y*.77,z),(.74 if k%3 else .76,y*.77,z),.0015,'Satin',face)
        b.cyl('LeafHinge',.030,1.40,'Satin',face,(.06,0,0),n=32)
        for z in [-.61,.61]:
            b.cube('HingeClevis',(.15,.10,.075),'Nickel',face,(.08,0,z),.013)
            b.cyl('ClevisBearing',.046,.045,'Satin',face,(.07,0,z+.028),n=32)
        # Front writing rail: a transverse carriage moves down both guide rods.
        for x in [.235,.705]:
            b.beam('WritingRail',(x,-side*.101,-.51),(x,-side*.101,.51),.010,'Nickel',face)
            for z in [-.54,.54]:b.cube('RailShoe',(.068,.077,.068),'Satin',face,(x,-side*.070,z),.010)
        carriage=b.empty('G3_Writer'+str(index),face,(0,0,.50))
        b.cube('WritingBridge',(.55,.058,.050),'Satin',carriage,(.47,-side*.105,0),.009)
        b.cube('WritingGlass',(.38,.013,.018),'Signal',carriage,(.47,-side*.138,0),.004)
        for x in [.235,.705]:
            b.cyl('LinearBearing',.022,.067,'Nickel',carriage,(x,-side*.102,0),n=24)
            b.screw(carriage,(x,-side*.138,0),(0,-side,0),.009)
        pin=b.empty('G3_Register'+str(index),face)
        for z in [-.46,.46]:
            b.cyl('RegistrationPin',.012,.072,'Nickel',pin,(.13,-side*.069,z),front,24)
            b.cube('PawlHousing',(.09,.042,.086),'Satin',face,(.13,-side*.036,z),.010)
        b.cube('IndexTab',(.10,.071,.14),'Porcelain',face,(.835,0,.40-layer*.10),.013)
        for k in range(index+1):b.cyl('IndexMark',.006,.003,'Red',face,(.813+(k%2)*.032,-.038,.429-layer*.10-(k//2)*.022),front,16)
        # One radial transport rail per depth bay; guide + telescopic rod.
        supports=[]
        for z in [1.19,2.38]:
            b.beam('FixedRadialRail',(side*.06,(layer-1)*.205,z),(side*.33,(layer-1)*.205,z),.018,'Satin',spine)
            support=b.empty('G3_Support%d_%d'%(index,round(z*100)),part)
            b.cyl('TelescopicRod',.014,1.0,'Nickel',support,n=24)
            supports.append({'node':support.name,'anchor':[side*.065,z,-(layer-1)*.205],'height':z-1.79})
        b.socket('page_'+str(index),face,(.47,0,-.09))
        leaf_meta.append({'index':index,'side':side,'layer':layer,'node':node.name,'face':face.name,'writer':carriage.name,'register':pin.name,'aperture':b.sockets['page_'+str(index)],'radius':.120,'supports':supports})

cover_meta=[]
for side in [-1,1]:
    cover=b.part('Cover'+str(side),(side*.76,-.93,.08),.03)
    def cover_pose(o,t,s=side):
        u=window(t,0,.32);o.location=(s*(.185+.67*window(t,.09,.32)),-.465-.14*window(t,0,.09),1.79);o.rotation_euler.z=-s*math.radians(52)*window(t,.10,.32)
    hinge=b.control('Cover'+str(side),cover,cover_pose)
    face=b.empty('G3_CoverFace'+str(side),hinge);face.rotation_euler.z=math.pi if side==-1 else 0
    bored_plate('CoverPorcelain',face,.88,1.64,.073,(.47,0,0))
    barrel=b.sleeve('CoverBore',.165,.12,.092,'Nickel',face,(.47,0,-.09));barrel.rotation_euler=front
    for y in [-.049,.049]:
        b.torus('CoverBoreStep',.159,.007,'Satin',face,(.47,y,-.09),front)
        b.torus('CoverBorePolish',.143,.004,'Nickel',face,(.47,y*1.10,-.09),front)
        for r in [.196,.227]:
            for begin in [15,115,225]:b.tube('CoverEtchedScale',[(.47+r*math.cos(math.radians(a)),y*.78,-.09+r*math.sin(math.radians(a))) for a in range(begin,begin+74,2)],.0015,'Copper',face,1)
        for a in range(0,360,30):
            a=math.radians(a);b.beam('CoverOpticalTick',(.47+.231*math.cos(a),y*.79,-.09+.231*math.sin(a)),(.47+.251*math.cos(a),y*.79,-.09+.251*math.sin(a)),.0013,'Satin',face)
    legend(face,'PALIMPSEST',(.47,-side*.040,.49),side,.047)
    legend(face,'OPTICAL MEMORY',(.47,-side*.040,.42),side,.024)
    legend(face,'G / 06',(.47,-side*.040,-.61),side,.041)
    for z in [-.66,.69]:b.cube('InsetCeramicRim',(.63,.011,.018),'Nickel',face,(.47,-side*.043,z),.005)
    for y in [-.044,.044]:
        for x in [.095,.845]:b.beam('CoverBrightEdge',(x,y,-.72),(x,y,.72),.009,'Nickel',face)
        for x in [.11,.83]:
            for z in [-.73,.73]:b.screw(face,(x,y,z),(0,1 if y>0 else -1,0),.017)
    for z in [-.63,0,.63]:
        b.cyl('CoverHinge',.061,.12,'Satin',face,(.01,0,z))
        b.torus('HingeBrightLip',.062,.006,'Nickel',face,(.01,0,z+.058))
    latch=b.empty('G3_Latch'+str(side),face,(.79,-.069,.20))
    b.cube('ArchiveLatch',(.052,.030,.19),'Red',latch,bevel=.013)
    b.cube('LatchGuide',(.075,.027,.24),'Nickel',face,(.79,-.043,.20),.013)
    supports=[]
    for z in [1.16,2.42]:
        b.beam('CoverGroundYoke',(side*.055,0,z),(side*.15,-.46,z),.022,'Satin',spine)
        b.joint(spine,(side*.15,-.46,z),.041,(0,0,1))
        rod=b.empty('G3_CoverRod%d_%d'%(side,round(z*100)),cover)
        b.cyl('CoverTelescopicRod',.022,1.0,'Nickel',rod,n=32)
        supports.append({'node':rod.name,'anchor':[side*.15,z,.46],'height':z-1.79})
    cover_meta.append({'node':hinge.name,'side':side,'supports':supports})

# Memory drum and the two actual collimators are attached to the grounded spine.
drum=b.part('MemoryDrum',(0,.65,1.10),.66)
b.cyl('MemoryDrum',.175,.25,'Lens',drum,(0,0,2.46))
for z in [2.34,2.58]:b.torus('DrumRim',.18,.012,'Nickel',drum,(0,0,z))
for k in range(24):
    a=k*math.tau/24;b.beam('DrumEncodedTick',(.181*math.cos(a),.181*math.sin(a),2.39),(.181*math.cos(a),.181*math.sin(a),2.44+(k%3)*.035),.003,'Copper',drum)
for s in [-1,1]:
    rail=b.part('Collimator'+str(s),(s*.52,.65,.15),.50)
    b.beam('ProjectorYoke',(0,.49,1.05),(s*.83,.49,1.05),.022,'Satin',rail)
    b.beam('ProjectorUpright',(s*.83,.49,1.05),(s*.83,.49,1.70),.022,'Nickel',rail)
    b.cyl('OpticalProjector',.063,.135,'Satin',rail,(s*.83,.51,1.70),front)
    b.cyl('ProjectorLens',.044,.012,'Signal',rail,(s*.83,.435,1.70),front)
    b.socket('source_'+str(s),rail,(s*.83,.422,1.70))
b.socket('field',spine,(0,-.04,2.83))
# Authored volumetric contour architecture. Solid tiny ridges, never a flat card.
relief=b.empty('G3_Relief',b.upper,(0,-.02,2.87))
relief_names=[]
for layer in range(28):
    t=layer/27;z=t*.44
    width=.44*(1-.48*t)+.030*math.sin(t*math.tau*2)
    cut=.16+.035*math.sin(t*math.tau)
    pts=[(-width,-.22,z),(width,-.22,z),(width,.19,z),(cut,.19,z),(cut,.015,z),(-cut,.015,z),(-cut,.19,z),(-width,.19,z),(-width,-.22,z)]
    row=b.empty('G3_ReliefLayer'+str(layer),relief)
    if layer%9<2:b.tube('ArchiveBalcony',pts,.003,'Signal',row,1)
    for x,y in [(-.35,-.18),(.35,-.18),(-.35,.18),(.35,.18)]:
        b.tube('MemoryTower',[(x-.045,y-.045,z),(x+.045,y-.045,z),(x+.045,y+.045,z),(x-.045,y+.045,z),(x-.045,y-.045,z)],.0022,'Signal',row,1)
        for sx in [-1,1]:b.beam('TowerPost',(x+sx*.045,y-.045,z),(x+sx*.045,y-.045,z+.018),.0021,'Signal',row)
    for sign in [-1,1]:
        x=sign*(-.35+t*.70);y=sign*.09
        b.tube('FloatingStairTread',[(x,y-.068,z),(x,y+.068,z),(x+sign*.026,y+.068,z),(x+sign*.026,y+.068,z+.017)],.003,'Signal',row,1)
    if layer%9==0:
        b.tube('VaultedArchive',[(.35*math.cos(a),-.18,z+.10*math.sin(a)) for a in [k*math.pi/32 for k in range(33)]],.003,'Signal',row,1)
    relief_names.append(row.name)
b.extra['g_mechanism']={'leaves':leaf_meta,'covers':cover_meta,'relief':relief.name,'relief_layers':relief_names,'aperture_radius':.120,'collimator_angle_deg':3.0,'fold_degrees':4.0,'source_x':.83,'reference':'production/G_complete/MECHANISM.md'}
b.extra['g_fx']={'atlas':'res://assets/collection/art/G/optical_atlas.png','motion_board':'production/G_complete/images/G_motion_vfx.png'}
# Export ourselves to avoid Builder.export's legacy G file paths and scaling.
b.apply_pose(0);samples={o.name:[] for o,_ in b.controls}
for i in range(101):
    b.apply_pose(i/100)
    for obj,_ in b.controls:samples[obj.name].append(pose(obj.matrix_basis))
b.apply_pose(0)
for row in relief.children:row.hide_render=True
meta={'id':'G','title':'折维书匣','root':b.root.name,'upper':b.upper.name,'parts':[{'name':p['obj'].name,'home':pose(p['obj'].matrix_basis),'offset':p['offset'],'stage':p['stage'],**({'route':p['route']} if 'route' in p else {})} for p in b.parts],'controls':[{'name':n,'samples':v} for n,v in samples.items()],'motions':[],'sockets':b.sockets,'qa_shells':b.qa_shells,'part_count':len(b.parts),'base_diameter':2.74,'includes_base':False,'source_blend':'blender/collection/G_complete.blend','display_calibration':{'scale':1.0,'fixed_mount_height':.615,'base_scaled':False},**b.extra}
out=ROOT/'app/assets/collection/models/G_complete.glb';out.with_suffix('.json').write_text(json.dumps(meta,separators=(',',':')),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
b.reference_scene()
# Correct shared operation cassette, preserved exact base body.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/frame_shared.glb'))
added=set(bpy.data.objects)-before;frame=next(o for o in added if o.type=='MESH')
base=bpy.data.objects.get('BASE_FIXED_DisplayMesh')
if base:base.data=frame.data.copy();base.matrix_world=frame.matrix_world
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
for index in range(1,6):
    mount=bpy.data.objects.get('BUTTON_%02d_MOUNT'%index)
    if mount:
        for obj in [mount]+list(mount.children_recursive):obj.hide_render=True;obj.hide_set(True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/control_library.glb'))
added=set(bpy.data.objects)-before
for slot,kind in enumerate(['rotary','slider_x','hold','gauge','service'],1):
    root=next(o for o in added if o.name=='CTRL_'+kind);mount=bpy.data.objects['BUTTON_%02d_MOUNT'%slot]
    root.parent=None;root.location=mount.matrix_world.translation;root.rotation_euler=(0,0,math.atan2(root.location.y,root.location.x)+math.pi/2)
    for obj in [root]+list(root.children_recursive):added.discard(obj)
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
b.scene.render.fps=30;b.scene.frame_end=1200;b.scene.cycles.samples=64
b.scene.timeline_markers.new('Await G runtime take',frame=1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/meta['source_blend']))
optimize(out)
print('G_COMPLETE_SOURCE',len(b.parts),'parts;',len(leaf_meta),'bored leaves',flush=True)
