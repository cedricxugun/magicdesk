"""Sealed linear pressure actuators between the existing cassette guides."""
import bpy,bmesh,json,hashlib,sys,struct,shutil,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_machined_geometry as h;import i_render_triangle_cleanup as tri
OUT=ROOT/'review/I_refinement/nautilus_r1/linear_drives_r20';OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/'blender/collection/I_nautilus_linear_drives_r20.blend';COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_linear_drives_r20.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=ROOT/'review/I_refinement/nautilus_r1/upper_cassettes_r19/build.json';seed=json.loads(parent.read_text());assert sha(ROOT/seed['source'])==seed['source_sha256'];assert json.loads((parent.parent/'checkpoint.json').read_text())['source_sha256']==seed['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-linear-drive-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];allowed={'IN2_Cassette%02d%s'%(m['panel_number'],suffix) for m in seed['real_cassettes'] for suffix in ['BackBlock','Crosshead']}
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return d.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed}
col=bpy.data.collections.new('I_LINEAR_PRESSURE_DRIVES_R20');scene.collection.children.link(col);h.configure(col)
def solid_profile(name,profile,parent,y):
    n=64;v=[(r*math.cos(k*math.tau/n),y+r*math.sin(k*math.tau/n),z) for z,r in profile for k in range(n)];f=[]
    for j in range(len(profile)-1):f.extend((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k) for k in range(n))
    f.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+k for k in range(n))]);mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(v,[],f);mesh.update();o=bpy.data.objects.new(name,mesh);col.objects.link(o);h.finish(o,name,parent,(0,0,0),'A_Nickel')
    for p in mesh.polygons:p.use_smooth=p.index<len(f)-2
    return o
def merge(a,b):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=a;mod=a.modifiers.new('Joined pressure hardware','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=b;bpy.ops.object.modifier_apply(modifier=mod.name);h.parts.remove(b.name);bpy.data.objects.remove(b,do_unlink=True)
drives=[]
for mechanism in seed['real_cassettes']:
    number=mechanism['panel_number'];prefix='IN2_Cassette%02dPressure'%number;frame=bpy.data.objects[mechanism['frame']];carriage=bpy.data.objects[mechanism['carriage']];back=bpy.data.objects['IN2_Cassette%02dBackBlock'%number];head=bpy.data.objects['IN2_Cassette%02dCrosshead'%number];stroke=mechanism['stroke'];y=.070;back_front=-stroke-.086;rear=back_front-.0002;front=-.040;inner_rear=back_front+.009;inner_front=-.050
    # Real seat and blind mounting holes in the existing back block.
    h.drill(back,.0285,.012,frame,(0,y,back_front+.0057))
    # The fitted back spine curves above the nominal block face. Give the
    # cylinder an actual through-channel while retaining the two side webs.
    channel_start=back_front+.008
    h.drill(back,.0185,front+.004-channel_start,frame,(0,y,(front+.004+channel_start)/2))
    housing=solid_profile(prefix+'Housing',[(rear,.028),(rear+.006,.028),(rear+.009,.0168),(front-.011,.0168),(front-.008,.018),(front,.018)],frame,y)
    h.drill(housing,.0115,inner_front-inner_rear,frame,(0,y,(inner_front+inner_rear)/2))
    h.drill(housing,.0054,.021,frame,(0,y,-.0455));h.drill(housing,.0082,.005,frame,(0,y,front-.002))
    gland=h.sleeve(prefix+'GlandSeal',.0080,.0052,.0038,frame,(0,y,front-.0023),'A_Rubber')
    piston_z=back_front+.016
    piston=solid_profile(prefix+'PistonRod',[(piston_z-.003,.0111),(piston_z-.0013,.0111),(piston_z-.0013,.0107),(piston_z+.0013,.0107),(piston_z+.0013,.0111),(piston_z+.003,.0111)],carriage,y)
    rod=h.cylinder(prefix+'RodUnion',.005,.010-piston_z,carriage,(0,y,(.010+piston_z)/2),'A_Nickel',bevel=.0001);merge(piston,rod)
    shoulder=h.cylinder(prefix+'ShoulderUnion',.0085,.003,carriage,(0,y,-.0101),'A_Nickel',bevel=.0001);merge(piston,shoulder)
    seal=h.sleeve(prefix+'PistonSeal',.0113,.0109,.0022,carriage,(0,y,piston_z),'A_Rubber')
    h.drill(head,.0052,.026,carriage,(0,y,.001));h.drill(head,.0102,.020,carriage,(0,y,-.0172));washer=h.sleeve(prefix+'RodThrust',.010,.0052,.0012,carriage,(0,y,-.0079),'A_Bronze')
    for sign in [-1,1]:
        x=sign*.023;h.drill(housing,.0022,.013,frame,(x,y,rear+.003))
        h.drill(housing,.0050,front+.001-(rear+.006),frame,(x,y,(front+.001+rear+.006)/2))
        h.drill(back,.0021,.019,frame,(x,y,back_front-.0085));h.sleeve(prefix+'MountWasher'+str(sign),.0048,.0022,.0010,frame,(x,y,rear+.0066),'A_Bronze')
        center_z=rear+.0092;start_z=back_front-.012;bolt=h.cylinder(prefix+'MountBolt'+str(sign),.0018,center_z-start_z,frame,(x,y,(center_z+start_z)/2),'A_Nickel',bevel=.0001);cap=h.screw(prefix+'MountHead'+str(sign),frame,(x,y,center_z),.0045);merge(bolt,cap)
    row={'panel_number':number,'frame':frame.name,'carriage':carriage.name,'housing':housing.name,'piston':piston.name,'piston_seal':seal.name,'gland_seal':gland.name,'rod_thrust':washer.name,'axis_local_blender':[0,0,1],'center_y':y,'stroke':stroke,'inner_axial_bounds':[inner_rear,inner_front],'piston_rest_center':piston_z,'piston_half_depth':.003,'housing_inner_radius':.0115,'piston_seal_outer_radius':.0113,'rod_radius':.005,'gland_inner_radius':.0052,'rod_tip_z':.010,'crosshead_blind_floor_z':.014}
    mechanism.setdefault('power',{})['linear']=row;drives.append(row);print('LINEAR_DRIVE_BUILT',number,flush=True)
repairs=[]
for name in list(h.parts)+sorted(allowed):
    o=bpy.data.objects[name];r=tri.repair(o,connected_fins=True)
    if r['removed_opposed_triangles']:repairs.append({'mesh':name,**r})
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
r={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':seed['source_sha256'],'linear_drives':{'drives':drives,'new_meshes':list(h.parts),'modified_meshes':sorted(allowed),'render_repairs':repairs,'art':'production/I_refinement/nautilus_r1/power_r1/pressure_and_sector_drive_r1.png'},'status':'linear_pressure_drive_candidate_checks_pending','review_scope':'Three sealed housing/piston/rod/gland assemblies drive the already guided translation. Original cover/body geometry preserved; only back blocks and crossheads receive real mounts. Stroke, contacts, supply details, rotary drive, final housings/materials and full music/native remain pending.'}
(OUT/'build.json').write_text(json.dumps(r,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'modified_meshes':sorted(allowed)},indent=2)+'\n');print('LINEAR_DRIVE_SOURCE',r['source_sha256'],flush=True)
