"""Area-and-angle weighted normals on current cowl skins; exact geometry preservation."""
import bpy,json,hashlib,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_weighted_r50';ART=ROOT/'app/assets/collection/art/I/cowl_weighted_r50'
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
 m=o.modifiers.new('Cowl area-angle corner normals R50','WEIGHTED_NORMAL');m.mode='FACE_AREA_WITH_ANGLE';m.weight=50;m.keep_sharp=True;m.thresh=.01;bpy.ops.object.modifier_apply(modifier=m.name);o.data.update()
 changes=[a.angle(b.vector,0.)for a,b in zip(old,o.data.corner_normals)];rows.append({'mesh':name,'corners':len(changes),'changed_corners':sum(x>1e-5 for x in changes),'max_angle_degrees':math.degrees(max(changes)),'mean_angle_degrees':math.degrees(sum(changes)/len(changes))})
assert all(signature(bpy.data.objects[n],normal=n not in names)==v for n,v in before.items()),'Geometry, morph, UV, material or protected normals changed'
source=ROOT/'blender/collection/I_nautilus_cowl_weighted_r50.blend';component=ROOT/'app/assets/collection/components/I_nautilus_cowl_weighted_r50.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
l=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());assert l['source_sha256']==s['source_sha256'];l.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(l,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/cowl_weighted_r50/chamber_layout.json','cowl_normal_finish':rows,'status':'weighted_corner_normal_candidate_visual_review_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'geometry_preservation.json').write_text(json.dumps({'passed':True,'source_sha256':d['source_sha256'],'protected_mesh_count':len(before),'normal_changes':rows,'scope':'Exact source positions, actual triangle indices, UVs, morph coordinates, transforms and material assignments on all meshes. Only four cowl corner-normal fields changed. Visual acceptance pending.'},indent=2)+'\n');print('R50_WEIGHTED_NORMAL_SOURCE',d['source_sha256'],rows,flush=True)
