"""Keep the fitted rear hardware; machine and reinforce a source-matched cowl."""
import bpy,bmesh,json,hashlib,math,sys,struct,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];pocket_only='--pocket-only' in args
import i_fitted_surface as fitted
from i_nautilus_receiver_recess import exterior_signature
OUT=ROOT/('review/I_refinement/nautilus_r1/receiver_pocket_r8' if pocket_only else 'review/I_refinement/nautilus_r1/receiver_fit_r5');OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/('blender/collection/I_nautilus_receiver_pocket_r8.blend' if pocket_only else 'blender/collection/I_nautilus_receiver_fit_r5.blend');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/nautilus_r1/core_bridge_r4/build.json').read_text());base=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_relation_r3/build.json').read_text());thin=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_relation_r3/receiver_wall_exact.json').read_text())
metadata=json.loads((ROOT/'review/I_refinement/nautilus_r1/wall_metadata_r5/build.json').read_text());assert sha(ROOT/metadata['source'])==metadata['source_sha256']
assert seed['source_sha256']=='0e1193ca0b6e45d55cfbdebb07add0ceca4a3bdb2a681ea2bb723a5cfb5c6d8d'==sha(ROOT/seed['source'])
assert base['source_sha256']==thin['source_sha256']==sha(ROOT/base['source']) and not thin['intersection_pairs']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded receiver-fit edits'
    archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-nautilus-receiver-fit-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];cowl=bpy.data.objects['IN1_PorcelainPanel_02'];mouth=bpy.data.objects['IAM_MODULE'].matrix_world.copy()
def signature(o):
    digest=hashlib.sha256()
    for v in o.data.vertices:digest.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:digest.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [digest.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o!=cowl};outside_before=exterior_signature(cowl);cowl_transform=cowl.matrix_world.copy();cowl_materials=list(cowl.data.materials)
with bpy.data.libraries.load(str(ROOT/base['source']),link=False) as (src,dst):
    names=[name for name in src.meshes if name=='IN1_PorcelainPanel_02Mesh'];assert len(names)==1;dst.meshes=names
cowl.data=dst.meshes[0];cowl.data.materials.clear()
for mat in cowl_materials:cowl.data.materials.append(mat)
assert exterior_signature(cowl)==outside_before,'Source reset changed the cowl exterior'
geometry_before_metadata=signature(cowl)
with bpy.data.libraries.load(str(ROOT/metadata['source']),link=False) as (src,dst):dst.meshes=['IN1_PorcelainPanel_02Mesh']
labels=dst.meshes[0];tree=KDTree(len(labels.vertices))
for v in labels.vertices:tree.insert(v.co,v.index)
tree.balance();maximum_label_distance=0.
for name in ['formed_wall_fraction','formed_loft_t','formed_end_x','formed_end_y','formed_end_z']:
    if name not in cowl.data.attributes:cowl.data.attributes.new(name,'FLOAT','POINT')
for v in cowl.data.vertices:
    _,index,distance=tree.find(v.co);maximum_label_distance=max(maximum_label_distance,distance);assert distance<.000002,'Wall metadata does not match source geometry'
    for name in ['formed_wall_fraction','formed_loft_t','formed_end_x','formed_end_y','formed_end_z']:cowl.data.attributes[name].data[v.index].value=labels.attributes[name].data[index].value
assert signature(cowl)==geometry_before_metadata,'Metadata transfer changed geometry'
outside_before=exterior_signature(cowl)
cowl.data.calc_loop_triangles();original_vertices=[cowl.matrix_world@v.co for v in cowl.data.vertices];original_faces=[tuple(t.vertices) for t in cowl.data.loop_triangles];fractions=[a.value for a in cowl.data.attributes['formed_wall_fraction'].data]
col=bpy.data.collections.new('I_RECEIVER_FIT_R5');scene.collection.children.link(col)
def mesh(name,vs,fs,matrix,closed=True):
    data=bpy.data.meshes.new(name+'Mesh');data.from_pydata(vs,[],fs);data.update();o=bpy.data.objects.new(name,data);col.objects.link(o);o.matrix_world=matrix;data.materials.append(cowl_materials[0])
    for attr_name in ['formed_wall_fraction','IN3_receiver_region']:
        attribute=data.attributes.new(attr_name,'FLOAT','POINT')
        for value in attribute.data:value.value=1.
    if closed:
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bad=[{'faces':len(e.link_faces),'length':e.calc_length(),'coordinates':[list(v.co) for v in e.verts]} for e in bm.edges if not e.is_manifold]
        assert not bad,(name,bad[:8])
        bm.to_mesh(data);bm.free()
    return o
def boolean(tool,operation):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=cowl
    mod=cowl.modifiers.new('Receiver '+operation,'BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=tool
    if hasattr(mod,'material_mode'):mod.material_mode='TRANSFER'
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
    assert len(cowl.data.vertices)>500 and len(cowl.data.polygons)>500,'Receiver operation removed the cowl'
# Persist the source-defined review region; all tool faces are also reviewed.
region=cowl.data.attributes.new('IN3_receiver_region','FLOAT','POINT');to_mouth=mouth.inverted()
for index,v in enumerate(cowl.data.vertices):region.data[index].value=float(.53<(to_mouth@cowl.matrix_world@v.co).z<.72)
profile=[(.560,.560),(.572,.610),(.578,.622),(.608,.622),(.614,.617),(.620,.606),(.6265,.594),(.638,.574),(.643,.558),(.650,.490)]
N=192;vs=[];fs=[]
for z,r in profile:
    vs.extend((r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),z) for i in range(N))
for j in range(len(profile)-1):
    for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs.extend([tuple(range(N-1,-1,-1)),tuple((len(profile)-1)*N+i for i in range(N))])
boolean(mesh('IR5_ReceiverCutter',vs,fs,mouth),'DIFFERENCE')
# The prior offset trial made crossing chords. Reinforce only the measured
# thin areas, using actual outer triangles translated into the part interior.
outer_faces=[f for f in original_faces if max(fractions[i] for i in f)<.001]
outer=mesh('IR5_OriginalOuterSurface',[tuple(p) for p in original_vertices],outer_faces,Matrix.Identity(4),False)
samples=[]
for row in thin['below_minimum']:
    f=original_faces[row['inner_triangle']];g=original_faces[row['outer_triangle']];pts=[original_vertices[i] for i in f];q=[original_vertices[i] for i in g];normal=(q[1]-q[0]).cross(q[2]-q[0]).normalized()
    samples.append({'triangle':row['inner_triangle'],'points':pts,'center':sum(pts,Vector())/3.,'normal':normal})
samples.sort(key=lambda r:r['triangle']);groups=[]
while samples:
    anchor=samples.pop(0);group=[anchor];remaining=[]
    for row in samples:
        if (row['center']-anchor['center']).length<.055 and row['normal'].dot(anchor['normal'])>.85:group.append(row)
        else:remaining.append(row)
    samples=remaining;groups.append(group)
patches=[]
if pocket_only:groups=[]
def split_touching_fans(points,polygons):
    points=[p.copy() for p in points];polygons=[list(p) for p in polygons];original_count=len(points)
    for vertex in range(original_count):
        incident=[i for i,f in enumerate(polygons) if vertex in f]
        if len(incident)<2:continue
        neighbors={}
        for i in incident:
            f=polygons[i];k=f.index(vertex)
            for other in [f[k-1],f[(k+1)%len(f)]]:neighbors.setdefault(other,[]).append(i)
        adjacency={i:set() for i in incident}
        for faces in neighbors.values():
            for i in faces:adjacency[i].update(j for j in faces if j!=i)
        unseen=set(incident);fans=[]
        while unseen:
            stack=[unseen.pop()];fan=[]
            while stack:
                i=stack.pop();fan.append(i)
                for j in adjacency[i]:
                    if j in unseen:unseen.remove(j);stack.append(j)
            fans.append(fan)
        for fan in fans[1:]:
            replacement=len(points);points.append(points[vertex].copy())
            for i in fan:polygons[i]=[replacement if v==vertex else v for v in polygons[i]]
    edges={}
    for f in polygons:
        for i,a in enumerate(f):
            b=f[(i+1)%len(f)];edges.setdefault(tuple(sorted([a,b])),[]).append((a,b))
    assert all(len(e)<=2 for e in edges.values()),'Overlapping source patch edges'
    return points,polygons,[e[0] for e in edges.values() if len(e)==1],len(points)-original_count
for number,group in enumerate(groups):
    center=sum([r['center'] for r in group],Vector())/len(group);normal=sum([r['normal'] for r in group],Vector()).normalized();x=Vector((0,0,1))-normal*normal.z
    if x.length<.1:x=Vector((1,0,0))-normal*normal.x
    x.normalize();y=normal.cross(x);frame=Matrix((x,y,normal)).transposed().to_4x4();frame.translation=center;inverse=frame.inverted();cloud=[]
    for row in group:
        for p in row['points']:
            local=inverse@p
            for k in range(12):
                a=k*math.tau/12;cloud.append(Vector((local.x+.020*math.cos(a),local.y+.020*math.sin(a))))
    hull=convex_hull_2d(cloud);outline=[tuple(cloud[i]) for i in hull]
    area=sum(a[0]*outline[(i+1)%len(outline)][1]-a[1]*outline[(i+1)%len(outline)][0] for i,a in enumerate(outline))
    if area<0:outline.reverse()
    points,polygons,edges=fitted.clipped_surface([outer],outline,frame=frame,from_positive=True,allow_partial=True)
    points,polygons,edges,split_vertices=split_touching_fans(points,polygons)
    vv,ff=fitted.extruded_patch(points,polygons,edges,-.00015,bottom_offset=-.0105)
    tool=mesh('IR5_InnerReinforcement_%02d'%number,vv,ff,frame);boolean(tool,'UNION')
    patches.append({'index':number,'source_inner_triangles':[r['triangle'] for r in group],'frame':[list(r) for r in frame],'outline':outline,'actual_patch_vertices':len(points),'split_point_touching_fans':split_vertices,'outer_inset':.00015,'inner_offset':.0105,'partial_boundary_allowed':True})
    print('RECEIVER_REAL_PATCH',number+1,len(groups),len(cowl.data.vertices),flush=True)
bpy.data.objects.remove(outer,do_unlink=True)
bm=bmesh.new();bm.from_mesh(cowl.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cowl.data);bm.free();cowl.data.update();cowl.data.calc_loop_triangles()
reference_outer=BVHTree.FromPolygons(original_vertices,outer_faces,all_triangles=True)
current_vertices=[cowl.matrix_world@v.co for v in cowl.data.vertices];tolerance=.000002
outer_match=[reference_outer.find_nearest(p)[3]<=tolerance for p in current_vertices]
label=cowl.data.attributes['formed_wall_fraction'];relabeled=0
for i,match in enumerate(outer_match):
    value=0. if match else 1.
    if abs(label.data[i].value-value)>1e-6:relabeled+=1
    label.data[i].value=value
current_outer=[tuple(t.vertices) for t in cowl.data.loop_triangles if all(outer_match[i] for i in t.vertices)]
assert current_outer,'Receiver lost the exterior surface'
current_tree=BVHTree.FromPolygons(current_vertices,current_outer,all_triangles=True)
def surface_metrics(points,faces,other):
    maximum=0.;area=0.
    for f in faces:
        a,b,c=[points[i] for i in f];area+=(b-a).cross(c-a).length/2.
        for p in [a,b,c,(a+b+c)/3.,(a+b)/2.,(b+c)/2.,(c+a)/2.]:maximum=max(maximum,other.find_nearest(p)[3])
    return maximum,area
old_error,old_area=surface_metrics(original_vertices,outer_faces,current_tree);new_error,new_area=surface_metrics(current_vertices,current_outer,reference_outer)
outside_after=exterior_signature(cowl);surface_check={'signature_exact':outside_after==outside_before,'old_to_new_maximum':old_error,'new_to_old_maximum':new_error,'old_area':old_area,'new_area':new_area,'area_ratio':new_area/old_area,'labels_restored_after_boolean':relabeled,'tolerance':tolerance}
surface_check['passed']=max(old_error,new_error)<tolerance and abs(new_area/old_area-1.)<.00001
(OUT/'exterior_surface_diagnostic.json').write_text(json.dumps(surface_check,indent=2)+'\n')
if not surface_check['passed']:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'diagnostic_rejected_source.blend'),compress=True)
assert surface_check['passed'],('Receiver changed exterior geometry',surface_check)
bpy.context.view_layer.update();changed=[name for name,value in protected.items() if signature(bpy.data.objects[name])!=value];assert not changed,changed
assert cowl.matrix_world==cowl_transform
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/('app/assets/collection/components/I_nautilus_receiver_pocket_r8.glb' if pocket_only else 'app/assets/collection/components/I_nautilus_receiver_fit_r5.glb')
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':seed['source_sha256'],'receiver_fit':{'base_cowl_source_sha256':base['source_sha256'],'reset_rejected_inner_projection':True,'pocket_profile':profile,'reinforcement_patches':patches,'exterior_surface_sha256':outside_after,'protected_other_meshes':len(protected)},'status':'triangle_matched_receiver_candidate_checks_pending','review_scope':'Rear hardware frozen from 0e1193ca; original d84b7d87 outer cowl retained. 02 interior restored, machined with a real receiver solid and reinforced using actual outer triangle patches. Source outer faces and every other mesh/pose are protected. Receiver wall, fits, chamber seats and native/art acceptance remain under review.'}
result['core_bridge'].pop('receiver_recess',None)
result['receiver_fit']['wall_metadata']={'source_sha256':metadata['source_sha256'],'maximum_vertex_match_distance':maximum_label_distance,'geometry_unchanged_by_metadata':True}
result['receiver_fit']['exterior_surface_check']=surface_check
result['receiver_fit']['pocket_only']=pocket_only
if pocket_only:
    result['status']='receiver_pocket_candidate_checks_pending'
    result['review_scope']='Rear hardware frozen from 0e1193ca; d84b7d87 cowl restored with only the required internal receiver pocket. No failed projection or reinforcement geometry retained. Original thin regions remain an explicit refinement item; check real intersections, joints and whole-scene behavior before promotion.'
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed and surface_check['passed'],'other_meshes':len(protected),'changed':changed,'exterior_surface_sha256':outside_after,'exterior_surface_check':surface_check},indent=2)+'\n')
print('RECEIVER_REAL_TRIANGLE_FIT_BUILT',flush=True)
