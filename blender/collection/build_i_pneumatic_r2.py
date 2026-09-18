"""Fork R1; replace the intersecting pneumatic path with an aligned pressure assembly."""
import bpy,bmesh,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
SOURCE=ROOT/'blender/collection/I_helix_r1.blend';TARGET=ROOT/'blender/collection/I_pneumatic_r2.blend'
OUT=ROOT/'review/I_refinement/r2';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==json.loads((ROOT/'review/I_refinement/r1/build.json').read_text())['source_sha256']
if TARGET.exists() and (OUT/'build.json').exists():assert sha(TARGET)==json.loads((OUT/'build.json').read_text())['source_sha256'],'Unrecorded R2 source edits; preserve before rebuilding'
original_hash=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
upper=bpy.data.objects['IH1_UPPER'];fixed=bpy.data.objects['IH1_FixedChamber'];mouth=bpy.data.objects['IH1_Mouth'];bell=bpy.data.objects['IH1_Bellows'];dia=bpy.data.objects['IH1_Diaphragm'];apex=bpy.data.objects['IH1_Apex']
# The reservoir belongs in the wider middle chamber, before the narrow tail.
control=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
t=.57
bell.location=control[0]*(1-t)**3+control[1]*3*(1-t)**2*t+control[2]*3*(1-t)*t*t+control[3]*t**3
axis=((control[1]-control[0])*(1-t)**2+(control[2]-control[1])*2*(1-t)*t+(control[3]-control[2])*t*t).normalized()
bell.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
b=Builder.__new__(Builder);b.id='IP2';b.serial=0;b.upper=upper;b.root=bpy.data.objects['IH1_MODULE']
b.col=bpy.data.collections.new('I_PNEUMATIC_R2');scene.collection.children.link(b.col)
b.mats={key:bpy.data.materials['Collection_'+key] for key in ['HelixNickel','HelixBrass','HelixRubber','HelixRed','HelixInk']}
b.mats.update({'Chrome':b.mats['HelixNickel'],'Copper':b.mats['HelixBrass'],'Black':b.mats['HelixInk'],'Red':b.mats['HelixRed']})
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
def normalize(mesh):
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
def lathe(name,profile,key,parent,n=96):
    vs=[(r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),z) for r,z in profile for k in range(n)]
    fs=[(j*n+k,j*n+(k+1)%n,((j+1)%len(profile))*n+(k+1)%n,((j+1)%len(profile))*n+k) for j in range(len(profile)) for k in range(n)]
    smooth=[abs(profile[j][1]-profile[(j+1)%len(profile)][1])>1e-8 for j in range(len(profile)) for _ in range(n)]
    obj=b.fast['fast_instance'](b.name(name),vs,fs,key,parent,(0,0,0),smooth_faces=smooth);normalize(obj.data);return obj
def convert(obj):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');return bpy.context.view_layer.objects.active
def curve(points,name,r,parent):
    obj=b.tube(name,points,r,'HelixNickel',parent,3);obj.data.use_fill_caps=True;return obj

# Remove only the known intersecting path and pneumatic/end-cap pieces.
removed=[]
for obj in list(upper.children_recursive):
    if 'HollowAcousticDuct' in obj.name or (obj.parent==bell and 'BellowsFlange' in obj.name) or (obj.parent==dia and obj.type=='CURVE') or (obj.parent==apex and obj.type=='MESH'):
        removed.append(obj.name);bpy.data.objects.remove(obj,do_unlink=True)
assert len(removed)==8,removed

# Smaller inner collar keeps the moving tail shell clear.
collar=b.sleeve('ApexInnerCollar',.040,.020,.030,'HelixNickel',apex)
collar.modifiers[0].width=.001
b.sphere('ApexRuby',.028,'HelixRed',apex,(0,0,.075))

STROKE=.132;DMAX=.014
front=b.empty('IP2_MovingBellowsFace',bell,(0,0,-.23))
front_plate=lathe('FrontBellowsPlate',[(.275,-.019),(.275,.0175),(.079,.0175),(.079,-.007),(.084,-.007),(.084,-.019)],'HelixNickel',front)
seal=b.torus('SlidingSeal',.0785,.0035,'HelixRubber',front,(0,0,-.0135))
b.sleeve('SealRetainer',.116,.076,.005,'HelixNickel',front,(0,0,-.0215),64)
rear=b.sleeve('RearBellowsPlate',.275,.0755,.035,'HelixNickel',bell,(0,0,.23),96)
tube=lathe('StationaryPortTube',[(.075,-.37),(.075,.24),(.058,.24),(.058,-.37)],'HelixNickel',bell)
b.cyl('RearTubeClosure',.0745,.018,'HelixNickel',bell,(0,0,.237),None,64)
for i in range(3):
    a=i*math.tau/3;axis=Vector((math.cos(a),math.sin(a),0));cutter=b.cyl('AirPortTool',.020,.080,'HelixNickel',bell,axis*.066+Vector((0,0,.10)),axis.to_track_quat('Z','Y'),48)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=tube;mod=tube.modifiers.new('Reservoir side port','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)

wall=next(o for o in bell.children if 'BellowsFoldedWall' in o.name)
wall=convert(wall);basis=wall.shape_key_add(name='Basis');compressed=wall.shape_key_add(name='Compression')
for vertex in compressed.data:vertex.co.z=.22+(vertex.co.z-.22)*.70
moving_parts=[front]
for i in range(3):
    a=i*math.tau/3+.4;xy=Vector((.285*math.cos(a),.285*math.sin(a),0))
    guide=b.sleeve('BellowsGuideBush',.018,.0115,.055,'HelixNickel',front,xy,48);guide.modifiers[0].width=.0005
    b.beam('GuideRearEar',Vector((.25*math.cos(a),.25*math.sin(a),.23)),xy+Vector((0,0,.23)),.016,'HelixNickel',bell)
    b.cyl('BellowsGuidePin',.0105,.55,'HelixNickel',bell,xy+Vector((0,0,-.025)),None,32)
    b.cyl('BellowsGuideEndStop',.017,.020,'HelixNickel',bell,xy+Vector((0,0,-.285)),None,32)
    b.beam('GuideFrontEar',Vector((.25*math.cos(a),.25*math.sin(a),0)),xy,.016,'HelixNickel',front)

# Three fixed saddle links seat the reservoir on the existing chamber ribs.
bpy.context.view_layer.update()
rear_center=bell.matrix_local@Vector((0,0,.23))
ribs=[o for o in fixed.children if o.type=='CURVE' and 'AcousticChamberRib' in o.name]
def rib_points(obj):return [(obj.matrix_local@Vector(p.co[:3])) for p in obj.data.splines[0].points[:-1]]
rib=min(ribs,key=lambda o:(sum(rib_points(o),Vector())/len(rib_points(o))-rear_center).length)
saddle_links=[]
for i in range(3):
    a=i*math.tau/3+.4;start=bell.matrix_local@Vector((.26*math.cos(a),.26*math.sin(a),.23));end=min(rib_points(rib),key=lambda p:(p-start).length)
    support=b.beam('ReservoirSaddleLink',start,end,.014,'HelixNickel',fixed);saddle_links.append({'name':support.name,'rib':rib.name,'start':list(start),'end':list(end)})

# A separate refill/quiet-relief poppet vents without kicking the diaphragm.
cutter=b.cyl('ReliefPortTool',.015,.080,'HelixNickel',bell,(.15,0,.23),None,48)
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rear
for modifier in list(rear.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
mod=rear.modifiers.new('Relief port bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
valve=b.sleeve('ReliefValveHousing',.035,.015,.050,'HelixNickel',bell,(.15,0,.265),64);valve.modifiers[0].width=.001
poppet=b.empty('IP2_ReliefPoppet',bell,(.15,0,.293))
b.cyl('ReliefPoppetHead',.022,.006,'HelixNickel',poppet,(0,0,0),None,48)
b.cyl('ReliefPoppetStem',.005,.050,'HelixNickel',poppet,(0,0,-.022),None,32)
for i in range(3):
    angle=i*math.tau/3;b.cyl('ReliefGuidePost',.003,.050,'HelixNickel',bell,(.15+.029*math.cos(angle),.029*math.sin(angle),.297),None,24)
b.sleeve('ReliefTopStop',.035,.014,.005,'HelixNickel',bell,(.15,0,.320),64)

# A rear pressure cup stops behind the diaphragm instead of piercing it.
outer=[(.49,.260),(.47,.340),(.44,.370),(.20,.460),(.09,.560),(.075,.610)]
inner=[(.058,.610),(.078,.560),(.184,.460),(.424,.370),(.454,.340),(.475,.260)]
cup=lathe('DiaphragmPressureCup',outer+inner,'HelixNickel',mouth,128)
b.sleeve('CupMountFlange',.505,.475,.020,'HelixNickel',mouth,(0,0,.2525),96)

# Fixed, hollow connector joins the cup and the straight reservoir core tube.
bpy.context.view_layer.update()
M=mouth.matrix_local;B=bell.matrix_local
p0=M@Vector((0,0,.610));p3=B@Vector((0,0,-.37))
p1=p0+(M.to_3x3()@Vector((0,0,1)))*.28;p2=p3-(B.to_3x3()@Vector((0,0,1)))*.25
def point(t):return p0*(1-t)**3+p1*3*(1-t)**2*t+p2*3*(1-t)*t*t+p3*t**3
def direction(t):return ((p1-p0)*(1-t)**2+(p2-p1)*2*(1-t)*t+(p3-p2)*t*t).normalized()
vs=[];faces=[];count=96;sides=48;previous=direction(0);n=(M.to_3x3()@Vector((1,0,0))).normalized();frames=[]
for j in range(count+1):
    t=j/count;axis=direction(t);n=previous.rotation_difference(axis)@n;n=(n-axis*n.dot(axis)).normalized();frames.append((point(t),n.copy(),axis.cross(n).normalized()));previous=axis
for radius in [.075,.058]:
    for c,n,v in frames:
        for k in range(sides):vs.append(c+(n*math.cos(k*math.tau/sides)+v*math.sin(k*math.tau/sides))*radius)
size=(count+1)*sides
for layer in [0,1]:
    for j in range(count):
        for k in range(sides):
            a=layer*size+j*sides+k;c=layer*size+j*sides+(k+1)%sides;face=(a,c,c+sides,a+sides);faces.append(face if layer==0 else face[::-1])
for j in [0,count]:
    for k in range(sides):a=j*sides+k;c=j*sides+(k+1)%sides;faces.append((a,c,c+size,a+size))
hose=b.fast['fast_instance'](b.name('HollowPressureConnector'),vs,faces,'HelixInk',fixed,(0,0,0),smooth_faces=True);normalize(hose.data)
for parent,z in [(mouth,.610),(bell,-.37)]:
    union=b.sleeve('PressureUnion',.092,.0745,.040,'HelixNickel',parent,(0,0,z),64);union.modifiers[0].width=.001

# Rolled flexible surround holds its outer edge while the piston translates.
surround=b.torus('DiaphragmRolledSurround',.474,.021,'HelixRubber',mouth,(0,0,.235))
surround.shape_key_add(name='Basis');sk=surround.shape_key_add(name='Travel');sk.slider_min=-1
for v in sk.data:
    radius=math.hypot(v.co.x,v.co.y);weight=max(0.,min(1.,(.470-radius)/.009));v.co.z-=DMAX*weight
springs=[]
for i in range(3):
    angle=i*math.tau/3;cx=.35*math.cos(angle);cy=.35*math.sin(angle)
    b.sleeve('MovingSpringSeat',.038,.022,.008,'HelixNickel',dia,(cx,cy,.009),48)
    b.sleeve('FixedSpringSeat',.038,.022,.010,'HelixNickel',mouth,(cx,cy,.335),48)
    b.beam('SpringSeatSpoke',(.377*math.cos(angle),.377*math.sin(angle),.341),(.460*math.cos(angle),.460*math.sin(angle),.341),.008,'HelixNickel',mouth)
    def coil_mesh(front_plane,name):
        wire=.004;coil_r=.027;turns=7;length=.330-front_plane-2*wire
        for _ in range(8):
            cosine=coil_r/math.sqrt(coil_r*coil_r+(length/(math.tau*turns))**2);length=.330-front_plane-2*wire*cosine
        low=front_plane+wire*cosine;high=.330-wire*cosine;points=[];faces=[];sides=32;rows=168
        for j in range(rows+1):
            u=j/rows;angle=u*math.tau*turns;radial=Vector((math.cos(angle),math.sin(angle),0));axis=Vector((-coil_r*math.sin(angle)*math.tau*turns,coil_r*math.cos(angle)*math.tau*turns,high-low)).normalized();side=axis.cross(radial).normalized();center=Vector((cx+coil_r*math.cos(angle),cy+coil_r*math.sin(angle),low+(high-low)*u))
            for k in range(sides):points.append(center+wire*(radial*math.cos(k*math.tau/sides)+side*math.sin(k*math.tau/sides)))
        for j in range(rows):
            for k in range(sides):a=j*sides+k;c=j*sides+(k+1)%sides;faces.append((a,c,c+sides,a+sides))
        faces.extend([tuple(range(sides-1,-1,-1)),tuple(range(rows*sides,(rows+1)*sides))])
        obj=b.fast['fast_instance'](b.name(name),points,faces,'HelixNickel',mouth,(0,0,0),smooth_faces=True);normalize(obj.data);return obj
    base=coil_mesh(.248,'DiaphragmSpring');extended=coil_mesh(.248-DMAX,'SpringTravelTarget')
    assert len(base.data.vertices)==len(extended.data.vertices)
    base.shape_key_add(name='Basis');key=base.shape_key_add(name='Travel');key.slider_min=-1
    for a,c in zip(key.data,extended.data.vertices):a.co=c.co
    bpy.data.objects.remove(extended,do_unlink=True);springs.append(base)

# Apply static modifiers only in this fork so glTF can retain the new morph targets.
for obj in upper.children_recursive:
    if obj.type!='MESH' or obj.data.shape_keys:continue
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    normalize(obj.data)
panels=[bpy.data.objects['IH1_FrontPanel'+str(i)] for i in range(6)]
leaves=[bpy.data.objects['IH1_IrisLeaf'+str(i)] for i in range(6)];drive=bpy.data.objects['IH1_IrisCamDrive']
for obj in panels+leaves+[drive,dia]:obj.animation_data_clear()
take=json.loads((OUT/'pneumatic_take.json').read_text())
for sample in take['samples']:
    frame=sample['frame'];state=sample['state'];displacement=max(-DMAX,min(DMAX,state['diaphragm']*40.))
    for panel in panels:panel.location=Vector(panel['open_direction'])*panel['stroke']*sample['opening'];panel.keyframe_insert('location',frame=frame)
    for leaf in leaves:leaf.rotation_euler.z=leaf['home_angle']-1.05*state['iris'];leaf.keyframe_insert('rotation_euler',frame=frame)
    drive.rotation_euler.z=-.30*state['iris'];drive.keyframe_insert('rotation_euler',frame=frame)
    front.location.z=-.23+STROKE*state['compression'];front.keyframe_insert('location',frame=frame)
    dia.location.z=.235-displacement;dia.keyframe_insert('location',frame=frame)
    relief=1. if state['stage'] in ['rest','recover'] else max(0.,min(1.,(1.-state['pressure'])*12.))
    poppet.location.z=.293+.012*relief;poppet.keyframe_insert('location',frame=frame)
    wall.data.shape_keys.key_blocks['Compression'].value=state['compression'];wall.data.shape_keys.key_blocks['Compression'].keyframe_insert('value',frame=frame)
    for obj in [surround]+springs:obj.data.shape_keys.key_blocks['Travel'].value=displacement/DMAX;obj.data.shape_keys.key_blocks['Travel'].keyframe_insert('value',frame=frame)
scene.render.fps=30;scene.frame_end=361;scene.frame_set(1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));assert sha(SOURCE)==original_hash
bpy.ops.object.select_all(action='DESELECT')
for obj in [b.root]+list(b.root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
component=ROOT/'app/assets/collection/components/I_pneumatic_r2.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
report={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':original_hash,'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'removed':removed,'stroke':STROKE,'reservoir_curve_position':.57,'diaphragm_visual_amplification':40,'diaphragm_limit':DMAX,'front_group':front.name,'relief_poppet':poppet.name,'feed_tube':tube.name,'connector':hose.name,'cup':cup.name,'bellows_wall':wall.name,'surround':surround.name,'springs':[o.name for o in springs],'source_preserved':True,'saddle_links':saddle_links,'scope':'Isolated pneumatic geometry and simulation-driven source animation; collision, morph export and visual review still required. Main app unchanged.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_PNEUMATIC_R2',json.dumps(report),flush=True)
