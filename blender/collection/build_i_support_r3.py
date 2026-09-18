"""Fork the preserved pneumatic source and seat its three supports on the actual base."""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
SOURCE=ROOT/'blender/collection/I_pneumatic_r2.blend';TARGET=ROOT/'blender/collection/I_support_r3.blend'
OUT=ROOT/'review/I_refinement/support_r3';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==json.loads((ROOT/'review/I_refinement/r2/build.json').read_text())['source_sha256']
if TARGET.exists():
    previous=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==previous['source_sha256'],'Unrecorded support-source edits'
    backup=TARGET.parent/'checkpoints'/('I-support-'+sha(TARGET)[:12]+'.blend');backup.parent.mkdir(exist_ok=True);backup.write_bytes(TARGET.read_bytes())
base_probe=json.loads((OUT/'base_probe.json').read_text());ground=.5625
assert all(abs(p['height']-ground)<1e-6 for p in base_probe['rows'] if abs(p['x'])<.66)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE'];upper=bpy.data.objects['IH1_UPPER'];fixed=bpy.data.objects['IH1_FixedChamber']
original=set([root]+list(root.children_recursive))
def fingerprint(obj):
    h=hashlib.sha256();h.update(str(tuple(tuple(row) for row in obj.matrix_local)).encode())
    if obj.type=='MESH':
        for p in obj.data.vertices:h.update(str(tuple(p.co)).encode())
        for p in obj.data.polygons:h.update(str(tuple(p.vertices)).encode())
    return h.hexdigest()
before={o.name:fingerprint(o) for o in original}
b=Builder.__new__(Builder);b.id='IS3';b.serial=0;b.upper=upper;b.root=root
b.col=bpy.data.collections.new('I_SUPPORT_R3');scene.collection.children.link(b.col)
b.mats={key:bpy.data.materials['Collection_'+key] for key in ['HelixNickel','HelixBrass','HelixRubber','HelixRed','HelixInk']}
finish=b.mats['HelixNickel'].copy();finish.name='Collection_HelixSupportNickel'
principled=next(n for n in finish.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for key in ['Normal','Roughness']:
    for link in list(principled.inputs[key].links):finish.node_tree.links.remove(link)
principled.inputs['Roughness'].default_value=.31;b.mats['HelixNickel']=finish
b.mats.update({'Chrome':b.mats['HelixNickel'],'Copper':b.mats['HelixBrass'],'Black':b.mats['HelixInk'],'Red':b.mats['HelixRed']})
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
def normalize(obj):
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
def apply(obj):
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    normalize(obj)
def boolean(obj,cutter,operation='DIFFERENCE'):
    if obj.data.users>1:obj.data=obj.data.copy()
    apply(cutter);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Machined seat','BOOLEAN');mod.operation=operation;mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
def lathe(name,profile,mat,parent,n=128):
    vs=[(r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),z) for r,z in profile for k in range(n)]
    fs=[(j*n+k,j*n+(k+1)%n,((j+1)%len(profile))*n+(k+1)%n,((j+1)%len(profile))*n+k) for j in range(len(profile)) for k in range(n)]
    sm=[abs(profile[j][1]-profile[(j+1)%len(profile)][1])>1e-8 for j in range(len(profile)) for _ in range(n)]
    o=b.fast['fast_instance'](b.name(name),vs,fs,mat,parent,(0,0,0),smooth_faces=sm);normalize(o);return o
def screw(parent,p,r=.008):
    # Captive head with a real hex socket; the bolt shaft is part of the mating mount.
    o=b.cyl('CaptiveBolt',r,.007,'HelixNickel',parent,p,None,48);apply(o)
    cut=b.cyl('HexSocketTool',r*.48,.005,'HelixInk',parent,Vector(p)+Vector((0,0,.003)),None,6);boolean(o,cut);return o
mount=bpy.data.objects['IH1_P_Mount']
pad=b.cyl('PedestalGroundPad',.427,.025,'HelixRubber',mount,(0,0,ground+.0125),None,128);apply(pad)
# A blind, tilted socket supplies an actual stop plane under the existing column end.
origin=Vector((.05,.18,.80));axis=Vector((.04,0,.58)).normalized()
seat=b.empty('IS3_ColumnSocket',fixed,origin);seat.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
housing=lathe('BlindColumnSeat',[(0,-.060),(.140,-.060),(.140,-.025),(.143,0),(.153,.035),(.150,.090),(.145,.120),(.1312,.120),(.1312,0),(0,0)],'HelixNickel',seat)
cut=b.cube('GroundTrim',(2,2,1),'HelixInk',fixed,(0,0,.77-.5),0);boolean(housing,cut)
# Three inward-facing feet fit the existing pedestal and avoid its outer copper ring.
phi=math.atan2(origin.y,origin.x)
lug_names=[]
for a in [phi+math.pi-.85,phi+math.pi,phi+math.pi+.85]:
    p=Vector((origin.x+.166*math.cos(a),origin.y+.166*math.sin(a),.787))
    lug=b.cube('ColumnBoltFoot',(.065,.055,.034),'HelixNickel',fixed,p,.004,(0,0,a));apply(lug)
    # Join each foot to the housing as one stationary casting, then drill its fastener.
    boolean(housing,lug,'UNION')
    hole=b.cyl('ColumnBoltBore',.005,.055,'HelixInk',fixed,p,None,32);boolean(housing,hole)
    bolt=screw(fixed,p+Vector((0,0,.021)),.009);lug_names.append(bolt.name)
feet=[];changed=[]
for x in [-.576,.576]:
    foot=Vector((x,-.30,.73));group=b.empty('IS3_Clevis_'+('L' if x<0 else 'R'),fixed)
    top=Vector((x/2.4,.10,1.46));support_axis=(top-foot).normalized()
    barrel=min([o for o in fixed.children if 'LowerSupportBarrel' in o.name],key=lambda o:(o.location-foot).length)
    cut=b.cube('BarrelNeckTrim',(2,2,1),'HelixInk',fixed,foot+support_axis*(.15-.5),0);cut.rotation_euler=support_axis.to_track_quat('Z','Y').to_euler();boolean(barrel,cut)
    neck=b.beam('NarrowTrunnionNeck',foot+support_axis*.06,foot+support_axis*.18,.030,'HelixNickel',fixed);boolean(barrel,neck,'UNION');changed.append(barrel.name)
    edge=barrel.modifiers.new('Neck shoulder edge break','BEVEL');edge.width=.0015;edge.segments=3;apply(barrel)
    gasket=b.cube('ClevisGroundGasket',(.173,.158,.010),'HelixRubber',group,(x,-.30,ground+.005),.004)
    sole=b.cube('ClevisSole',(.169,.154,.019),'HelixNickel',group,(x,-.30,ground+.0195),.005)
    apply(gasket);apply(sole)
    cheeks=[]
    for side in [-1,1]:
        y=foot.y+side*.0575
        cheek=b.cyl('ClevisCheekCrown',.079,.027,'HelixNickel',group,(x,y,.73),Vector((0,1,0)).to_track_quat('Z','Y'),96);apply(cheek)
        leg=b.cube('ClevisCheekLeg',(.158,.027,.14),'HelixNickel',group,(x,y,.6615),.006);boolean(cheek,leg,'UNION')
        cut=b.cyl('ClevisAxleBore',.0305,.060,'HelixInk',group,(x,y,.73),Vector((0,1,0)).to_track_quat('Z','Y'),64);boolean(cheek,cut)
        cut=b.beam('NeckReliefTool',foot,foot+support_axis*.24,.034,'HelixInk',group);boolean(cheek,cut)
        cheeks.append(cheek.name)
        cap=b.cyl('AxleHexCap',.037,.012,'HelixNickel',group,(x,foot.y+side*.086,.73),Vector((0,1,0)).to_track_quat('Z','Y'),6);apply(cap)
        b.cyl('AxleRubyCenter',.015,.001,'HelixRed',group,(x,foot.y+side*.0925,.73),Vector((0,1,0)).to_track_quat('Z','Y'),48)
    # Extend only the existing lower pin to engage both new bored cheeks.
    pin=min([o for o in fixed.children if 'RedPin' in o.name],key=lambda o:(o.location-foot).length)
    assert (pin.location-foot).length<.001,pin.name
    pin.scale.z*=.172/.085;changed.append(pin.name)
    for side in [-1,1]:screw(group,(x+side*.052,-.30,ground+.033),.008)
    feet.append({'group':group.name,'center':list(foot),'gasket':gasket.name,'sole':sole.name,'cheeks':cheeks,'pin':pin.name})
for o in list(b.col.objects):
    if o.type=='MESH':
        apply(o)
        if 'ClevisCheek' in o.name:
            for polygon in o.data.polygons:
                if abs(polygon.normal.z)>.999:polygon.use_smooth=False
after={o.name:fingerprint(o) for o in original};unexpected=[name for name in before if before[name]!=after[name] and name not in changed]
assert not unexpected,unexpected
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root;glb=ROOT/'app/assets/collection/components/I_support_r3.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':sha(SOURCE),'component':str(glb.relative_to(ROOT)),'component_sha256':sha(glb),'ground':ground,'base_mesh_sha256':base_probe['base_sha256'],'column_socket':housing.name,'pedestal_pad':pad.name,'feet':feet,'changed_original_objects':changed,'unexpected_original_changes':unexpected,'original_object_count':len(original),'scope':'Independent support geometry; input pneumatic source preserved; two lower pins extended and two lower barrels given narrow necks. Contact/clearance and actual GPU reports are separate.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_SUPPORT_R3',json.dumps(result),flush=True)
