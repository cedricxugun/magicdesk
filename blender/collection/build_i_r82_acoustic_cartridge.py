"""Extract the functional A cartridge without the superseded white cowl.
All retained meshes, UVs, shape keys and local transforms are fingerprinted.
"""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1';OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_r82_acoustic_cartridge_r1.blend';COMP=R/'app/assets/collection/components/I_r82_acoustic_cartridge_r1.glb'
assert not SRC.exists() and not COMP.exists()
s=json.loads((R/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text());assert hashlib.sha256((R/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for uv in o.data.uv_layers:
  h.update(uv.name.encode())
  for p in uv.data:h.update(struct.pack('<2f',*p.uv))
 if o.data.shape_keys:
  for key in o.data.shape_keys.key_blocks:
   h.update(key.name.encode())
   for v in key.data:h.update(struct.pack('<3f',*v.co))
 for row in o.matrix_world:h.update(struct.pack('<4f',*row))
 return h.hexdigest()
removed=[o for o in bpy.data.objects if o.name.startswith('IAM_Collar') or 'PorcelainUpper'in o.name or 'PorcelainLower'in o.name]
names=[o.name for o in removed]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH' and o not in removed}
for o in removed:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
assert all(fingerprint(bpy.data.objects[n])==h for n,h in protected.items())
for name in [g for row in s['tongues']for g in row['mesh_names']]+s['diaphragm']['morphs']:
 assert name in bpy.data.objects
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
for group in s['tongues']:
 for n in group['mesh_names']:bpy.data.objects[n].shape_key_clear()
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_extras=True)
report={k:v for k,v in s.items()if k not in ['collar_clamps','removed_old_clamp_objects','modified_fixed_meshes','retained_geometry_fingerprints','scope']}
report.update({'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'component':COMP.relative_to(R).as_posix(),'component_sha256':hashlib.sha256(COMP.read_bytes()).hexdigest(),'parent_source':s['source'],'parent_source_sha256':s['source_sha256'],'parent_component_sha256':s['component_sha256'],'removed_outer_cowl':names,'retained_mesh_fingerprints':protected,'scope':'Functional cartridge extraction, retained mesh/UV/shape-key/local-world transforms unchanged. Superseded outer porcelain and its cam clamps removed. Not installed/clearance/art/runtime acceptance.'})
(OUT/'core_build.json').write_text(json.dumps(report,indent=2)+'\n')
print('R82_CORE_EXTRACTED',len(protected),'retained meshes',len(names),'outer objects removed',report['source_sha256'],flush=True)
