"""Derive one complete receiver wall with Blender's constrained shell solver."""
import bpy,bmesh,json,hashlib,struct,sys,shutil
from pathlib import Path
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/receiver_shell_r6';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_nautilus_receiver_shell_r6.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/nautilus_r1/core_bridge_r4/build.json').read_text());labels=json.loads((ROOT/'review/I_refinement/nautilus_r1/wall_metadata_r5/build.json').read_text())
assert seed['source_sha256']=='0e1193ca0b6e45d55cfbdebb07add0ceca4a3bdb2a681ea2bb723a5cfb5c6d8d'==sha(ROOT/seed['source']);assert labels['source_sha256']==sha(ROOT/labels['source'])
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded constrained-shell edits'
    archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-nautilus-shell-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];cowl=bpy.data.objects['IN1_PorcelainPanel_02']
def fingerprint(o):
    digest=hashlib.sha256()
    for v in o.data.vertices:digest.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:digest.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [digest.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o!=cowl};original_materials=list(cowl.data.materials);original_matrix=cowl.matrix_world.copy()
kd=KDTree(len(cowl.data.vertices))
for v in cowl.data.vertices:kd.insert(v.co,v.index)
kd.balance()
with bpy.data.libraries.load(str(ROOT/labels['source']),link=False) as (src,dst):dst.meshes=['IN1_PorcelainPanel_02Mesh']
source=dst.meshes[0];source.calc_loop_triangles();fraction=[a.value for a in source.attributes['formed_wall_fraction'].data];polygon_ids={p.index for p in source.polygons if max(fraction[k] for k in p.vertices)<.001};source_triangles=[t for t in source.loop_triangles if t.polygon_index in polygon_ids];used=sorted({k for t in source_triangles for k in t.vertices});remap={old:i for i,old in enumerate(used)}
maximum_match=max(kd.find(source.vertices[i].co)[2] for i in used);assert maximum_match<.000002,'Metadata exterior does not match the preserved source'
verts=[tuple(source.vertices[i].co) for i in used];faces=[tuple(remap[k] for k in t.vertices) for t in source_triangles];data=bpy.data.meshes.new('IR6_ReceiverSurfaceMesh');data.from_pydata(verts,[],faces);data.update()
for material in original_materials+original_materials+[original_materials[0]]:data.materials.append(material)
for p,t in zip(data.polygons,source_triangles):
    old=source.polygons[t.polygon_index];p.material_index=old.material_index;p.use_smooth=old.use_smooth
source_index=data.attributes.new('IR6_source_vertex','INT','POINT')
for v in data.vertices:source_index.data[v.index].value=v.index
cowl.data=data;cowl.data.calc_loop_triangles();reference_vertices=[cowl.matrix_world@v.co for v in data.vertices];reference_faces=[tuple(t.vertices) for t in data.loop_triangles];reference=BVHTree.FromPolygons(reference_vertices,reference_faces,all_triangles=True)
bpy.context.view_layer.objects.active=cowl;modifier=cowl.modifiers.new('Constrained inward receiver wall','SOLIDIFY');modifier.solidify_mode='NON_MANIFOLD';modifier.nonmanifold_thickness_mode='CONSTRAINTS';modifier.nonmanifold_boundary_mode='FLAT';modifier.nonmanifold_merge_threshold=.0000001;modifier.thickness=.0085;modifier.offset=-1.;modifier.use_rim=True;modifier.material_offset=len(original_materials);modifier.material_offset_rim=len(original_materials)*2
actual_settings={key:getattr(modifier,key) for key in ['solidify_mode','nonmanifold_thickness_mode','nonmanifold_boundary_mode','nonmanifold_merge_threshold','thickness','offset']}
bpy.ops.object.modifier_apply(modifier=modifier.name);cowl.data.update();cowl.data.calc_loop_triangles()
# Complex solidification may adjust the original side slightly at corners.
# Recover its one-to-one source provenance and restore only that side exactly;
# material offsets alone are not reliable provenance for the complex solver.
groups={i:[] for i in range(len(reference_vertices))}
for v in cowl.data.vertices:groups[cowl.data.attributes['IR6_source_vertex'].data[v.index].value].append(v.index)
assert all(len(group)==2 for group in groups.values()),('Lost source provenance',sorted({len(group) for group in groups.values()}))
correspondence=[]
source_ids=[a.value for a in cowl.data.attributes['IR6_source_vertex'].data];adjacency={i:set() for i in range(len(cowl.data.vertices))}
for face in cowl.data.polygons:
    ids=[source_ids[i] for i in face.vertices]
    if len(set(ids))!=len(ids):continue
    for i,a in enumerate(face.vertices):
        b=face.vertices[(i+1)%len(face.vertices)];adjacency[a].add(b);adjacency[b].add(a)
unseen=set(adjacency);sheets=[]
while unseen:
    todo=[unseen.pop()];sheet=[]
    while todo:
        i=todo.pop();sheet.append(i)
        for j in adjacency[i]:
            if j in unseen:unseen.remove(j);todo.append(j)
    sheets.append(sheet)
paired={}
for sheet in sheets:paired.setdefault(tuple(sorted(source_ids[i] for i in sheet)),[]).append(sheet)
outer_vertices=set()
for ids,pair in paired.items():
    assert len(pair)==2,('Unpaired shell sheets',[len(s) for s in sheets])
    distance=lambda sheet:sum(((cowl.matrix_world@cowl.data.vertices[i].co)-reference_vertices[source_ids[i]]).length_squared for i in sheet)
    outer_vertices.update(min(pair,key=distance))
for target in outer_vertices:
    i=source_ids[target];correspondence.append((None,target,((cowl.matrix_world@cowl.data.vertices[target].co)-reference_vertices[i]).length))
maximum_restore=max(row[2] for row in correspondence)
assert len(outer_vertices)==len(reference_vertices),('Non-unique original shell mapping',len(outer_vertices),len(reference_vertices))
assert maximum_restore<.0137,('Large solver displacement',maximum_restore)
for target in outer_vertices:cowl.data.vertices[target].co=verts[source_ids[target]]
cowl.data.update();cowl.data.calc_loop_triangles()
side=cowl.data.attributes.new('IR6_wall_side','INT','FACE');inner_vertices=set();outer_faces=[]
for face in cowl.data.polygons:
    flags=[i in outer_vertices for i in face.vertices];role=0 if all(flags) else 1 if not any(flags) else 2
    side.data[face.index].value=role
    if role==0:outer_vertices.update(face.vertices)
    elif role==1:inner_vertices.update(face.vertices)
for tri in cowl.data.loop_triangles:
    if side.data[tri.polygon_index].value==0:outer_faces.append(tuple(tri.vertices))
wall=cowl.data.attributes.new('formed_wall_fraction','FLOAT','POINT');region=cowl.data.attributes.new('IN3_receiver_region','FLOAT','POINT')
for v in cowl.data.vertices:
    wall.data[v.index].value=0. if v.index in outer_vertices and v.index not in inner_vertices else 1. if v.index in inner_vertices and v.index not in outer_vertices else .5
    region.data[v.index].value=float(v.index in inner_vertices)
points=[cowl.matrix_world@v.co for v in cowl.data.vertices];current=BVHTree.FromPolygons(points,outer_faces,all_triangles=True)
def compare(vv,ff,other):
    error=0.;area=0.
    for f in ff:
        a,b,c=[vv[k] for k in f];area+=(b-a).cross(c-a).length/2.
        for p in [a,b,c,(a+b+c)/3.,(a+b)/2.,(b+c)/2.,(c+a)/2.]:error=max(error,other.find_nearest(p)[3])
    return error,area
old_error,old_area=compare(reference_vertices,reference_faces,current);new_error,new_area=compare(points,outer_faces,reference)
surface={'old_to_new_maximum':old_error,'new_to_old_maximum':new_error,'area_ratio':new_area/old_area,'exact_tolerance':.000002,'exact_match':max(old_error,new_error)<.000002 and abs(new_area/old_area-1.)<.00001,'candidate_tolerance_over_base_d':.005,'maximum_deviation_over_base_d':max(old_error,new_error)/2.74,'passed':max(old_error,new_error)/2.74<.005 and abs(new_area/old_area-1.)<.02,'scope':'Bounded unlocked shape candidate, not exact exterior preservation. Requires same-view visual comparison and renewed neighbor/fit checks.'}
all_points=KDTree(len(points))
for i,p in enumerate(points):all_points.insert(p,i)
all_points.balance()
surface['reference_to_any_vertex_maximum']=max(all_points.find(p)[2] for p in reference_vertices)
surface['on_reference_vertices']=sum(reference.find_nearest(p)[3]<.000002 for p in points)
surface['reference_vertices']=len(reference_vertices);surface['result_vertices']=len(points)
(OUT/'solidify_diagnostic.json').write_text(json.dumps(surface,indent=2)+'\n')
if not surface['passed']:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'diagnostic_unaccepted.blend'),compress=True)
assert surface['passed'],surface
assert surface['exact_match'],('Triangulated exterior was not preserved',surface)
bpy.context.view_layer.update();changed=[name for name,value in protected.items() if fingerprint(bpy.data.objects[name])!=value];assert not changed,changed;assert cowl.matrix_world==original_matrix
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_nautilus_receiver_shell_r6.glb';bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':seed['source_sha256'],'receiver_shell':{'mode':'Blender SOLIDIFY NON_MANIFOLD CONSTRAINTS ROUND','actual_settings':actual_settings,'requested_thickness':.0085,'offset':-1.,'metadata_source_sha256':labels['source_sha256'],'maximum_exterior_vertex_match':maximum_match,'maximum_original_side_displacement':maximum_restore,'source_id_copies_per_vertex':2,'sheet_sizes':[len(s) for s in sheets],'outer_vertices':len(outer_vertices),'inner_vertices':len(inner_vertices),'shared_outer_inner_vertices':len(outer_vertices&inner_vertices),'exterior_surface':surface,'scope':'Connected shell-side provenance avoids swapping individual inner/outer corner vertices. Nominal thickness is not acceptance. Explicit face tags permit independent whole-inner-surface checks.'},'status':'receiver_shell_unlocked_shape_candidate_checks_pending','review_scope':'Rear hardware and every other mesh frozen from 0e1193ca. 02 receiver shell has bounded corner changes; the mouth placement and base remain fixed. Exact exterior preservation is not claimed. Same-view art comparison, actual wall distance, neighbor fits, chamber seats and native acceptance remain under review.'}
result['core_bridge'].pop('receiver_recess',None)
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed and surface['passed'],'other_meshes':len(protected),'changed':changed,'exterior_surface':surface},indent=2)+'\n');print('CONSTRAINED_RECEIVER_BUILT',flush=True)
