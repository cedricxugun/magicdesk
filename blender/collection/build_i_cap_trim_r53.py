"""Install a closed rounded metal trim on the actual lower face of cover05."""
import bpy,bmesh,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cap_trim_r53';ART=ROOT/'app/assets/collection/art/I/cap_trim_r53'
for p in [OUT,ART]:p.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/cowl_planes_r51/build.json').read_text());g=json.loads((ROOT/'review/I_refinement/nautilus_r1/cap_profile_r52/trim_mesh.json').read_text());p=json.loads((ROOT/'review/I_refinement/nautilus_r1/cap_profile_r52/profile.json').read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']==g['source_sha256']==p['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
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
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'};hood=bpy.data.objects[g['target_mesh']];world=hood.matrix_world.copy();inverse=world.inverted();tv=[];tf=[]
for row in p['triangles']:
 base=len(tv);tv += [Vector(v)for v in row['world']];tf.append((base,base+1,base+2))
cap_tree=BVHTree.FromPolygons(tv,tf,all_triangles=True);points=[Vector(v)for v in g['vertices_world']];fit=[]
for i in range(g['front_vertex_count'],len(points)):
 query=points[i];hit=cap_tree.ray_cast(query-Vector((0,0,.01)),Vector((0,0,1)),.02)[0]
 if hit is None:
  hit,normal,index,distance=cap_tree.find_nearest(query);assert hit is not None and distance<5e-7
 delta=(hit-query).length;assert delta<5e-7;fit.append(delta);points[i]=hit
m=bpy.data.meshes.new('I53_CapMetal05Mesh');m.from_pydata([inverse@v for v in points],[],g['faces']);m.update();o=bpy.data.objects.new('I53_CapMetal_05',m);hood.users_collection[0].objects.link(o);o.parent=hood;m.materials.append(bpy.data.materials['IN1_Nickel']);bpy.context.view_layer.update()
assert all(abs(o.matrix_world[i][j]-world[i][j])<1e-8 for i in range(4)for j in range(4))
normals=[]
for face,values in zip(m.polygons,g['corner_normals_world']):
 face.use_smooth=True
 for n in values:normals.append((world.to_3x3().transposed()@Vector(n)).normalized())
assert len(normals)==len(m.loops);m.normals_split_custom_set(normals);m.update()
bm=bmesh.new();bm.from_mesh(m);assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts);volume=bm.calc_volume(signed=True);assert volume>0;bm.free()
m.calc_loop_triangles();v=[o.matrix_world@x.co for x in m.vertices];tri=[tuple(t.vertices)for t in m.loop_triangles];tree=BVHTree.FromPolygons(v,tri,all_triangles=True);pairs=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(tri[a])&set(tri[b])];assert not pairs,('New trim self contacts',len(pairs),pairs[:10])
hood_min=min((world@v.co).z for v in hood.data.vertices);trim_max=max(v.z for v in v);trim_min=min(v.z for v in v);cheek=bpy.data.objects['IN1_FixedMouthCheek05'];cheek_max=max((cheek.matrix_world@v.co).z for v in cheek.data.vertices)
assert hood_min>=g['plane_z']-3e-7 and trim_max<=g['plane_z']+3e-7;assert trim_min-cheek_max>.0029
assert all(fingerprint(bpy.data.objects[n])==old for n,old in protected.items())
source=ROOT/'blender/collection/I_nautilus_cap_trim_r53.blend';component=ROOT/'app/assets/collection/components/I_nautilus_cap_trim_r53.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for x in [root,*root.children_recursive]:x.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
proof={'new_mesh':o.name,'parent':hood.name,'source_sha256':sha(source),'self_contacts':len(pairs),'signed_volume':volume,'vertices':len(m.vertices),'triangles':len(tri),'maximum_back_fit_adjustment':max(fit),'interface_plane_numerical_overlap':max(0.,trim_max-hood_min),'closed_vertical_gap_to_cheek':trim_min-cheek_max,'protected_original_meshes':len(protected),'scope':'Closed new metal trim, rounded profile, actual fitted cap back; no new source self contacts. All old geometry/normals/UV/morph/material/transform fields preserved. Hood contact constrained to numerical uncertainty around shared plane; full neighboring/motion checks pending.'};(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/cap_trim_r53/chamber_layout.json','cap_trim':proof,'status':'rounded_horizontal_trim_candidate_visual_and_motion_pending'};d['cowl_finish']={**s['cowl_finish'],'modified_meshes':[o.name]};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('R53_CAP_TRIM',proof,flush=True)
