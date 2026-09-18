"""Authored diaphragm suspension; retains the checked mouth and tongue mechanisms."""
import bpy,bmesh,math,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as P
from geometry import reparent_preserving_world
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/diaphragm';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((OUT.parent/'metal_finish/build.json').read_text());source=ROOT/seed['source'];assert sha(source)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
target=ROOT/'blender/collection/I_diaphragm_response.blend'
if target.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(target)==old['source_sha256'],'Unrecorded suspension edits'
    (target.parent/'checkpoints'/('I-diaphragm-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
mouth=bpy.data.objects['IAM_Mouth'];moving=bpy.data.objects['IAM_DiaphragmMotion'];col=bpy.data.collections['MODULE_IAM'];P.configure(col)
# The fixed neck previously started flush against the moving cap shoulder.
# Recess only its front lip so the full inward stroke clears the shoulder.
neck=bpy.data.objects['IAM_HeadAcousticNeck']
for vertex in neck.data.vertices:
    if vertex.co.z<0.:vertex.co.z+=.013
moving['stroke']=0.;stroke=.006
driver=moving.driver_add('location',2).driver;driver.type='SCRIPTED'
v=driver.variables.new();v.name='stroke';v.type='SINGLE_PROP';v.targets[0].id=moving;v.targets[0].data_path='["stroke"]';driver.expression='stroke'
diaphragm=next(o for o in bpy.data.objects if 'DomedDiaphragm' in o.name);inv=mouth.matrix_world.inverted();deps=bpy.context.evaluated_depsgraph_get()
e=diaphragm.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();surface=BVHTree.FromPolygons([inv@e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear()
deform=[];connections=[]

def keys(o,positive,negative):
    o.shape_key_add(name='Basis')
    for name,positions,sign in [('Pressure',positive,1),('Rebound',negative,-1)]:
        key=o.shape_key_add(name=name);key.data.foreach_set('co',np.asarray(positions,dtype=np.float32).ravel())
        d=key.driver_add('value').driver;d.type='SCRIPTED';v=d.variables.new();v.name='stroke';v.type='SINGLE_PROP';v.targets[0].id=moving;v.targets[0].data_path='["stroke"]';d.expression='max(0,%s*stroke/%s)'%(sign,stroke)
    deform.append(o.name)

def spring_vertices(x,y,displacement):
    verts=[];turns=6;segments=288;sides=12;coil_radius=.025;wire=.0035
    front=.428+displacement;rear=.563
    for j in range(segments+1):
        t=j/segments;angle=t*math.tau*turns
        # Flatten pitch toward the two seated end turns, keeping wire radius.
        zt=t*t*(3-2*t);dz=6*t*(1-t)*(rear-front)
        center=Vector((x+coil_radius*math.cos(angle),y+coil_radius*math.sin(angle),front+(rear-front)*zt))
        tangent=Vector((-coil_radius*math.sin(angle)*math.tau*turns,coil_radius*math.cos(angle)*math.tau*turns,dz)).normalized()
        radial=Vector((math.cos(angle),math.sin(angle),0));binormal=tangent.cross(radial).normalized()
        for k in range(sides):
            a=k*math.tau/sides;verts.append(tuple(center+wire*(radial*math.cos(a)+binormal*math.sin(a))))
    return verts

for index in range(3):
    prefix='IAM_Response%d_'%index;a=index*math.tau/3;x=.405*math.cos(a);y=.405*math.sin(a)
    old_spring=next(o for o in bpy.data.objects if 'MembraneReturnSpring' in o.name and abs(o.data.splines[0].points[0].co.x-(x+.025))<.001 and abs(o.data.splines[0].points[0].co.y-y)<.001)
    bpy.data.objects.remove(old_spring,do_unlink=True)
    seats=sorted([o for o in bpy.data.objects if 'SpringSeat' in o.name and abs(o.location.x-x)<.001 and abs(o.location.y-y)<.001],key=lambda o:o.location.z)
    front,rear=seats;reparent_preserving_world(front,moving)
    hit=surface.ray_cast(Vector((x,y,.43)),Vector((0,0,-1)),.2);assert hit[0] is not None
    top=front.location.z-.0075;contact=hit[0].z
    boss=P.cylinder(prefix+'PressureBoss',.015,top-contact+.0004,moving,(x,y,(top+contact)/2),'A_Nickel',bevel=.0004)
    P.cylinder(prefix+'PressureFoot',.027,.004,moving,(x,y,contact+.0017),'A_Bronze',bevel=.0005)
    P.sleeve(prefix+'FrontCupRim',.033,.029,.009,moving,(x,y,.429),'A_Nickel')
    P.sleeve(prefix+'RearCupRim',.033,.029,.009,mouth,(x,y,.562),'A_Nickel')
    # Rear seat is joined to the rear flange instead of ending short of it.
    P.cylinder(prefix+'RearSeatBoss',.020,.008,mouth,(x,y,.584),'A_Bronze',bevel=.0004)
    verts=spring_vertices(x,y,0);faces=[];segments=288;sides=12
    for j in range(segments):
        for k in range(sides):faces.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple(segments*sides+k for k in range(sides))])
    mesh=bpy.data.meshes.new(prefix+'SpringMesh');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(prefix+'ReturnSpring',mesh);col.objects.link(o)
    P.finish(o,o.name,mouth,(0,0,0),'A_Bronze')
    for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
    keys(o,spring_vertices(x,y,stroke),spring_vertices(x,y,-stroke))
    connections.append({'index':index,'spring':o.name,'front_seat':front.name,'rear_seat':rear.name,'boss':boss.name,'diaphragm_contact_z':contact,'front_wire_min_z':.4245,'rear_wire_max_z':.5665,'xy':[x,y]})

surround=next(o for o in bpy.data.objects if 'DiaphragmRubberSurround' in o.name)
base=np.array([tuple(v.co) for v in surround.data.vertices]);radii=np.linalg.norm(base[:,:2],axis=1);t=np.clip((radii-.49)/(.520-.49),0,1);weights=1-t*t*(3-2*t)
positive=base.copy();negative=base.copy();positive[:,2]+=weights*stroke;negative[:,2]-=weights*stroke;keys(surround,positive,negative)

# An independent motion study on the existing 433-frame range. Tongue tracks
# remain intact; this source demonstrates the connected suspension range.
samples=[]
for frame in range(1,434):
    t=(frame-1)/60
    value=stroke*math.sin(math.pi*(t-3.)/1.2) if 3.<t<4.2 else -.003*math.sin(math.pi*(t-4.2)/.6)*math.exp(-2*(t-4.2)) if 4.2<=t<4.8 else 0.
    moving['stroke']=float(value);moving.keyframe_insert(data_path='["stroke"]',frame=frame)
    if frame%12==1:samples.append({'frame':frame,'stroke':value})
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)

# Export suspension morphs, but retain field-driven foils without hundreds of
# duplicate runtime morph targets. This removal is in-memory AFTER source save.
for group in seed['tongues']:
    for name in group['mesh_names']:bpy.data.objects[name].shape_key_clear()
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_diaphragm_response.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_extras=True)
report={**seed,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'diaphragm':{'moving':moving.name,'max_stroke':stroke,'morphs':deform,'pressure_key':'Pressure','rebound_key':'Rebound','connections':connections,'source_samples':samples},'scope':'Connected suspension response candidate: moving front seats/bosses, fixed rear seats, authored spring and surround morphs. Contact/normal/native/visual review pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_DIAPHRAGM_RESPONSE_BUILT',flush=True)
