"""Complete the floating spool supports on a copy of the checked three-tongue source.

No leaf, field, mouth silhouette or daily application assets are regenerated.
Dimensions are scene units, derived from the existing spindle positions/travel.
"""
import bpy, bmesh, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from i_tongue_path import TonguePath

OUT = ROOT / 'review/I_refinement/part_a_mouth/shutter_r2/cassettes'
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
seed = json.loads((OUT.parent / 'tongue_set/build.json').read_text())
source = ROOT / seed['source']
assert sha(source) == seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source))
target = ROOT / 'blender/collection/I_tongue_cassettes.blend'
if target.exists():
    old = json.loads((OUT / 'build.json').read_text())
    assert sha(target) == old['source_sha256'], 'Unrecorded cassette edits'
    (target.parent / 'checkpoints' / ('I-cassettes-' + sha(target)[:12] + '.blend')).write_bytes(target.read_bytes())
mouth = bpy.data.objects['IAM_Mouth']
col = bpy.data.collections['MODULE_IAM']
scene = bpy.context.scene
scene.frame_set(1)
serial = 0
parts = []
interfaces = []

def empty(name, parent, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    col.objects.link(o)
    o.parent = parent
    o.location = loc
    return o

def finish(o, name, parent, loc, material, bevel=0):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    col.objects.link(o)
    o.parent = parent
    o.location = loc
    o.data.materials.clear()
    o.data.materials.append(bpy.data.materials['Collection_' + material])
    if bevel:
        m = o.modifiers.new('Machined edge', 'BEVEL')
        m.width = bevel; m.segments = 3
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(o.data); bm.free()
    parts.append(o.name)
    return o

def box(name, dims, parent, loc, material='A_Dark', bevel=.0015):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, parent, loc, material, bevel)

def cylinder(name, radius, depth, parent, loc, material='A_Nickel', axis=(0,0,1), bevel=.0005):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth)
    o = finish(bpy.context.object, name, parent, loc, material, bevel)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector(axis).to_track_quat('Z','Y')
    for p in o.data.polygons: p.use_smooth = abs(p.normal.z) < .99
    return o

def drill(o, radius, depth, parent, loc, axis=(0,0,1)):
    tool = cylinder('CassetteDrill', radius, depth, parent, loc, axis=axis, bevel=0)
    bpy.context.view_layer.update(); bpy.context.view_layer.objects.active = o
    m = o.modifiers.new('Actual machined bore', 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name)
    parts.remove(tool.name); bpy.data.objects.remove(tool, do_unlink=True)

def sleeve(name, outer, inner, depth, parent, loc, material='A_Bronze', axis=(0,0,1)):
    # Explicit closed lathe profile avoids coincident Boolean seams in the bearing.
    n=64; verts=[]; faces=[]
    for r,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:
        verts.extend((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n))
    for k in range(4):
        for i in range(n): faces.append((k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i))
    mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    uv=mesh.uv_layers.new(name='MachinedCylindricalUV')
    for face in mesh.polygons:
        angles=[(mesh.loops[li].vertex_index%n)/n for li in face.loop_indices]
        seam=max(angles)-min(angles)>.5
        for li,u in zip(face.loop_indices,angles):
            vi=mesh.loops[li].vertex_index
            uv.data[li].uv=(u+1 if seam and u<.5 else u,verts[vi][2]/depth+.5)
    o=bpy.data.objects.new(name,mesh); col.objects.link(o)
    finish(o,name,parent,loc,material)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
    for p in mesh.polygons: p.use_smooth=p.index//n in [0,2]
    return o

def screw(name,parent,loc,r=.005,axis=(0,0,1)):
    head=cylinder(name,r,.004,parent,loc,'A_Nickel',axis)
    # Real hex socket recess; not a dark rectangle on a round head.
    bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=r*.49,depth=.003)
    tool=finish(bpy.context.object,'HexSocketTool',parent,Vector(loc)+Vector(axis)*.0016,'A_Dark')
    tool.rotation_mode='QUATERNION'; tool.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
    bpy.context.view_layer.update(); bpy.context.view_layer.objects.active=head
    m=head.modifiers.new('Recessed hex', 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name); parts.remove(tool.name); bpy.data.objects.remove(tool,do_unlink=True)
    return head

hardware=[]
for group in seed['tongues']:
    i=group['tongue_index']; prefix='IAM_Cassette%d_'%i
    path=TonguePath(i)
    spool=bpy.data.objects[group['spool']]; orient=spool.parent
    carriage=bpy.data.objects[group['carriage']]
    flanges=sorted([o for o in spool.children if 'SpoolFlange' in o.name],key=lambda o:o.location.z)
    half=abs(flanges[-1].location.z)
    # Existing axial end stubs had no bearings and did not rotate with the spool.
    for o in list(orient.children):
        if 'AxleEnd' in o.name: bpy.data.objects.remove(o,do_unlink=True)
    core=next(o for o in spool.children if 'SpoolCore' in o.name)
    core_name=core.name
    bpy.data.objects.remove(core,do_unlink=True)
    core=sleeve(core_name,.025,.0235,2*(half-.013),spool,(0,0,0),'A_Dark')
    for o in flanges: drill(o,.00625,half*2+.04,spool,(0,0,0))
    spindle=cylinder(prefix+'Spindle',.006,half*2+.016,spool,(0,0,0))
    sleeve(prefix+'DrumDriveWeb',.0243,.00625,.004,spool,(0,0,0),'A_Bronze')
    travel=group['states'][-1]['outer_radius']-group['states'][0]['outer_radius']
    fixed=empty(prefix+'FixedFrame',mouth,group['states'][0]['axis'])
    fixed.rotation_mode='QUATERNION'; fixed.rotation_quaternion=orient.rotation_euler.to_quaternion()
    # Copy the actual local orientation, without baking the carriage translation.
    fixed.matrix_basis=orient.matrix_basis.copy(); fixed.location=group['states'][0]['axis']
    rail_y=.088
    for side in [-1,1]:
        suffix='L' if side<0 else 'R'; z=side*(half-.008)
        bearing=sleeve(prefix+'Bearing'+suffix,.011,.0063,.008,orient,(0,0,z))
        body=box(prefix+'SlidingYoke'+suffix,(.044,.137,.008),orient,(0,.047,z),'A_Nickel',.004)
        drill(body,.0112,.025,orient,(0,0,z))
        drill(body,.0052,.075,orient,(0,rail_y,z),(1,0,0))
        liner=sleeve(prefix+'LinearBushing'+suffix,.005,.0045,.046,orient,(0,rail_y,z),'A_Bronze',(1,0,0))
        rail=cylinder(prefix+'GuideRail'+suffix,.0043,travel+.092,fixed,(-travel/2,rail_y,z),'A_Nickel',(1,0,0))
        # The outboard pillar reaches the existing rear carrier at z=.230.
        foot_y=.230-path.coil_z
        pillar_z=side*(half+.011)
        pillar=box(prefix+'CarrierPillar'+suffix,(.018,rail_y-foot_y,.010),fixed,(.045,(foot_y+rail_y)/2+.012,pillar_z),'A_Dark',.002)
        tab=box(prefix+'RailBridge'+suffix,(.018,.014,.038),fixed,(.045,rail_y,side*(half+.0015)),'A_Nickel',.001)
        drill(tab,.0046,.04,fixed,(.045,rail_y,z),(1,0,0))
        foot=box(prefix+'CarrierFoot'+suffix,(.030,.012,.020),fixed,(.040,foot_y+.006,pillar_z),'A_Bronze',.002)
        for dz in [-.005,.005]: screw(prefix+'MountScrew'+suffix+str(dz),fixed,(.040,foot_y+.014,pillar_z+dz),.003,(0,1,0))
        cylinder(prefix+'TravelStop'+suffix,.008,.007,fixed,(-travel-.043,rail_y,z),'A_Bronze',(1,0,0))
        for y in [.034,.112]:
            drill(body,.0042,.0045,orient,(0,y,z+side*.002),(0,0,side))
            screw(prefix+'YokeScrew'+suffix+str(y),orient,(0,y,z+side*.002),.004,(0,0,side))
        interfaces.append({'index':i,'bearing':bearing.name,'spindle':spindle.name,'radial_clearance':.0003,'slide':liner.name,'rail':rail.name,'rail_radial_clearance':.0002,'carrier_foot':foot.name,'carrier_contact_z':.230,'slide_travel':travel})
    box(prefix+'MovingCrossBrace',(.030,.014,2*half-.025),orient,(0,.108,0),'A_Dark',.002)
    # Compact coaxial drive travels with the supported spindle. The enclosed rotor
    # inherits the same physical spool node, so reversal cannot desynchronise it.
    # The first external motor trial collided with its neighbouring cassette.
    # Keep the checked coil envelope: fit the stator inside the hollow drum and
    # the two bearing yokes inside the flange spacing, beyond the foil width.
    motor_z=half-.050
    rotor=sleeve(prefix+'MotorRotor',.015,.00625,.024,spool,(0,0,motor_z),'A_Bronze')
    stator=sleeve(prefix+'MotorStator',.021,.016,.026,orient,(0,0,motor_z),'A_Dark')
    sleeve(prefix+'StatorSupport',.021,.016,.026,orient,(0,0,half-.025),'A_Nickel')
    sleeve(prefix+'StatorMount',.021,.0063,.004,orient,(0,0,half-.014),'A_Nickel')
    sleeve(prefix+'StatorMountBoss',.0108,.0063,.007,orient,(0,0,half-.0085),'A_Bronze')
    for j in range(8):
        a=j*math.tau/8
        cylinder(prefix+'StatorWinding%d'%j,.001,.022,orient,(.0185*math.cos(a),.0185*math.sin(a),motor_z),'A_Bronze',bevel=0)
    for flange in flanges:
        sign=1 if flange.location.z>0 else -1
        sleeve(prefix+'FlangeHub'+str(sign),.021,.00625,.006,spool,(0,0,flange.location.z+sign*.0055),'A_Bronze')
        for j in range(3):
            a=j*math.tau/3
            screw(prefix+'HubScrew%d_%d'%(sign,j),spool,(.017*math.cos(a),.017*math.sin(a),flange.location.z+sign*.0105),.003,(0,0,sign))
    hardware.append({'index':i,'fixed_frame':fixed.name,'orientation':orient.name,'carriage':carriage.name,'spool':spool.name,'spindle':spindle.name,'motor_rotor':rotor.name,'motor_stator':stator.name,'travel':travel,'flange_half_span':half})

# Retain evaluated animation and all six authored foils; export full rest topology.
scene.frame_set(1); bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT'); root=bpy.data.objects['IAM_MODULE']
for o in [root]+list(root.children_recursive): o.select_set(True)
bpy.context.view_layer.objects.active=root
component=ROOT/'app/assets/collection/components/I_tongue_cassettes.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True)
report={**seed,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'new_parts':parts,'hardware':hardware,'interfaces':interfaces,'scope':'Independent supported cassette candidate. Existing tongues/fields and front silhouette retained. New hardware collision, mount contact and actual render pending; not main App or art acceptance.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print('I_TONGUE_CASSETTES_BUILT',len(parts),flush=True)
