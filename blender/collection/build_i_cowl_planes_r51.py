"""Area-and-angle weighted normals on current cowl skins; exact geometry preservation."""
import bpy,json,hashlib,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_planes_r51';ART=ROOT/'app/assets/collection/art/I/cowl_planes_r51'
for p in [OUT,ART]:p.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/scan_caps_runtime_r43/readable/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def signature(o,normal=False):
 h=hashlib.sha256();m=o.data;m.calc_loop_triangles()
 for v in m.vertices:h.update(struct.pack('<3f',*v.co))
 for t in m.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
 for uv in m.uv_layers:
  for x in uv.data:h.update(struct.pack('<2f',*x.uv))
 if m.shape_keys:
  for key in m.shape_keys.key_blocks:
   h.update(key.name.encode())
   for v in key.data:h.update(struct.pack('<3f',*v.co))
 if normal:
  for n in m.corner_normals:h.update(struct.pack('<3f',*n.vector))
 return [h.hexdigest(),[list(r)for r in o.matrix_world],[x.name if x else None for x in m.materials],[f.material_index for f in m.polygons]]
names=['IN1_PorcelainPanel_01','IN1_PorcelainPanel_05','IN1_PorcelainPanel_06','IN1_FixedMouthCheek05'];before={o.name:signature(o,normal=o.name not in names)for o in bpy.data.objects if o.type=='MESH'};rows=[]
for name in names:
 o=bpy.data.objects[name];old=[n.vector.copy()for n in o.data.corner_normals];bpy.context.view_layer.objects.active=o
 mesh=o.data;world=o.matrix_world;mouth=bpy.data.objects['IAM_MODULE'].matrix_world;back=mouth.to_3x3().col[2].normalized();center=mouth.translation;coords=[world@v.co for v in mesh.vertices];depths=[(p-center).dot(back)for p in coords];flat_planes={}
 for face in mesh.polygons:
  if all(abs(depths[i]+.035)<2e-7 for i in face.vertices):flat_planes[face.index]=-back
  elif name=='IN1_FixedMouthCheek05' and all(abs(coords[i].z-1.698)<2e-7 for i in face.vertices):flat_planes[face.index]=__import__('mathutils').Vector((0,0,1))
  elif name=='IN1_PorcelainPanel_05' and all(abs(coords[i].z-1.702)<2e-7 for i in face.vertices):flat_planes[face.index]=__import__('mathutils').Vector((0,0,-1))
 edge_counts=[0]*len(mesh.edges);cap_counts=[0]*len(mesh.edges)
 for face in mesh.polygons:
  if face.index in flat_planes:face.use_smooth=False
  for li in face.loop_indices:
   ei=mesh.loops[li].edge_index;edge_counts[ei]+=1
   if face.index in flat_planes:cap_counts[ei]+=1
 sharp=mesh.attributes.get('sharp_edge')or mesh.attributes.new('sharp_edge','BOOLEAN','EDGE');separated=0
 for i,count in enumerate(cap_counts):
  if 0<count<edge_counts[i]:sharp.data[i].value=True;separated+=1
 mesh.update()
 m=o.modifiers.new('Cowl planar-boundary normals R51','WEIGHTED_NORMAL');m.mode='FACE_AREA_WITH_ANGLE';m.weight=50;m.keep_sharp=True;m.thresh=.01;bpy.ops.object.modifier_apply(modifier=m.name);o.data.update()
 authored=[n.vector.copy()for n in o.data.corner_normals]
 for face in o.data.polygons:
  if face.index not in flat_planes:continue
  normal=(world.to_3x3().transposed()@flat_planes[face.index]).normalized()
  for li in face.loop_indices:authored[li]=normal
 o.data.normals_split_custom_set(authored);o.data.update()
 changes=[a.angle(b.vector,0.)for a,b in zip(old,o.data.corner_normals)];rows.append({'mesh':name,'planar_faces':len(flat_planes),'hard_cap_boundary_edges':separated,'corners':len(changes),'changed_corners':sum(x>1e-5 for x in changes),'max_angle_degrees':math.degrees(max(changes)),'mean_angle_degrees':math.degrees(sum(changes)/len(changes))})
assert all(signature(bpy.data.objects[n],normal=n not in names)==v for n,v in before.items()),'Geometry, morph, UV, material or protected normals changed'
source=ROOT/'blender/collection/I_nautilus_cowl_planes_r51.blend';component=ROOT/'app/assets/collection/components/I_nautilus_cowl_planes_r51.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
l=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());assert l['source_sha256']==s['source_sha256'];l.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(l,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/cowl_planes_r51/chamber_layout.json','cowl_normal_finish':rows,'status':'weighted_corner_normal_candidate_visual_review_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'geometry_preservation.json').write_text(json.dumps({'passed':True,'source_sha256':d['source_sha256'],'protected_mesh_count':len(before),'normal_changes':rows,'scope':'Exact source positions, actual triangle indices, UVs, morph coordinates, transforms and material assignments on all meshes. Four cowl normal fields, planar cap shading and cap hard edges authored; no source triangle position changes. Visual acceptance pending.'},indent=2)+'\n');print('R51_PLANAR_NORMAL_SOURCE',d['source_sha256'],rows,flush=True)
