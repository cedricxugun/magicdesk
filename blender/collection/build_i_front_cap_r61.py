"""Fit a closed rounded nickel end trim to the current hood's measured plane."""
import bpy,bmesh,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61';ART=ROOT/'app/assets/collection/art/I/curved_returns_r61'
s=json.loads((OUT/'input.json').read_text());p=json.loads((OUT/'profile.json').read_text());g=json.loads((OUT/'trim_plane_mesh.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(ROOT/s['source'])==s['source_sha256']==p['source_sha256']==g['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
    h=hashlib.sha256();m=o.data;m.calc_loop_triangles()
    for v in m.vertices:h.update(struct.pack('<3f',*v.co))
    for t in m.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
    for n in m.corner_normals:h.update(struct.pack('<3f',*n.vector))
    for uv in m.uv_layers:
        for u in uv.data:h.update(struct.pack('<2f',*u.uv))
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            h.update(key.name.encode())
            for v in key.data:h.update(struct.pack('<3f',*v.co))
    return [h.hexdigest(),[list(r)for r in o.matrix_world],[x.name if x else None for x in m.materials],[f.material_index for f in m.polygons]]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'}
hood=bpy.data.objects[p['mesh']];world=hood.matrix_world.copy();inverse=world.inverted()
origin=Vector(p['frame_origin']);axes=[Vector(v)for v in p['frame_axes']]
def normal(v):return sum((axes[i]*v[i]for i in range(3)),Vector())
def point(v):return origin+normal(v)
vertices=[point(v)for v in g['vertices_world']];tv=[];tf=[]
for row in p['triangles']:
    offset=len(tv);tv.extend(Vector(v)for v in row['world']);tf.append((offset,offset+1,offset+2))
cap_tree=BVHTree.FromPolygons(tv,tf,all_triangles=True);fit=[]
for i in range(g['front_vertex_count'],len(vertices)):
    query=vertices[i];hit=cap_tree.ray_cast(query-axes[2]*.01,axes[2],.02)[0]
    if hit is None:hit,_,_,distance=cap_tree.find_nearest(query);assert hit is not None and distance<7e-7
    error=(hit-query).length;assert error<7e-7,(i,error);fit.append(error);vertices[i]=hit
m=bpy.data.meshes.new('I61_FrontReturn05Mesh');m.from_pydata([inverse@v for v in vertices],[],g['faces']);m.update()
o=bpy.data.objects.new('I61_FrontReturn_05',m);hood.users_collection[0].objects.link(o);o.parent=hood;m.materials.append(bpy.data.materials['IN1_Nickel']);bpy.context.view_layer.update()
assert all(abs(o.matrix_world[i][j]-world[i][j])<1e-8 for i in range(4)for j in range(4))
normals=[]
for face,values in zip(m.polygons,g['corner_normals_world']):
    face.use_smooth=True
    for v in values:normals.append((world.to_3x3().transposed()@normal(v)).normalized())
m.normals_split_custom_set(normals);m.update()
bm=bmesh.new();bm.from_mesh(m);assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts);volume=bm.calc_volume(signed=True);assert volume>0;bm.free()
m.calc_loop_triangles();v=[o.matrix_world@x.co for x in m.vertices];tri=[tuple(t.vertices)for t in m.loop_triangles]
tree=BVHTree.FromPolygons(v,tri,all_triangles=True);hits=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(tri[a])&set(tri[b])]
proof={'new_mesh':o.name,'parent':hood.name,'source_sha256':s['source_sha256'],'signed_volume':volume,'vertices':len(m.vertices),'triangles':len(tri),'self_contacts':len(hits),'self_pairs':hits[:30],'maximum_back_fit_adjustment':max(fit),'requested_depth':g['maximum_depth'],'rounded_radius':g['bevel_radius'],'front_plane':p['plane_z'],'coordinate_frame':{'origin':p['frame_origin'],'axes':p['frame_axes']},'scope':'New closed rounded end trim on exact measured hood cap; back fitted to source triangles. Not full hood side returns or final art.'}
(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n');assert not hits,proof
raw=(ROOT/s['component']).read_bytes();length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length]);rendered={n['name']for n in gltf['nodes']if 'mesh'in n}
minimum=[min(x[k]for x in v)for k in range(3)];maximum=[max(x[k]for x in v)for k in range(3)];contacts=[];deps=bpy.context.evaluated_depsgraph_get()
for name in sorted(rendered):
    if name==hood.name:continue
    other=bpy.data.objects[name];e=other.evaluated_get(deps);bb=[e.matrix_world@Vector(c)for c in e.bound_box]
    if any(max(c[k]for c in bb)<minimum[k]or min(c[k]for c in bb)>maximum[k]for k in range(3)):continue
    data=e.to_mesh();data.calc_loop_triangles();t=BVHTree.FromPolygons([e.matrix_world@x.co for x in data.vertices],[tuple(f.vertices)for f in data.loop_triangles],all_triangles=True);pairs=tree.overlap(t);e.to_mesh_clear()
    if pairs:contacts.append({'mesh':name,'pairs':len(pairs)})
(OUT/'static_neighbors.json').write_text(json.dumps({'passed':not contacts,'contacts':contacts,'excluded_bonded_parent':hood.name,'source_sha256':s['source_sha256']},indent=2)+'\n');assert not contacts,contacts
assert all(fingerprint(bpy.data.objects[n])==old for n,old in protected.items())
source=ROOT/'blender/collection/I_nautilus_front_return_r61.blend';component=ROOT/'app/assets/collection/components/I_nautilus_front_return_r61.glb';assert not source.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for x in [root,*root.children_recursive]:x.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
proof.update(candidate_source_sha256=sha(source),protected_original_meshes=len(protected));(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/curved_returns_r61/chamber_layout.json','music_optics_layout':'res://assets/collection/art/I/desktop_optics_r60/score_layout.json','front_return':proof,'status':'front_end_return_candidate_motion_and_visual_pending'}
d['runtime_pose_witnesses']=[o.name]
d['cowl_finish']={**s['cowl_finish'],'modified_meshes':[o.name]};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('R61_FRONT_RETURN',proof,flush=True)
