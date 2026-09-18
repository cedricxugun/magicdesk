"""Reverse one entire stud/socket pair to use the clear extraction side."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/seam_fasteners_r64/oriented_r2';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((OUT.parent/'build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
allowed={'IC1_SeamCrossBolt_1','IC64_SeamSocket_1'};before={o.name:[list(r)for r in o.matrix_world]for o in bpy.data.objects if o.type=='MESH'and o.name not in allowed}
center=Vector((.601,0,.590));change=Matrix.Translation(center)@Matrix.Rotation(math.pi,4,'X')@Matrix.Translation(-center)
for name in allowed:bpy.data.objects[name].matrix_local=change@bpy.data.objects[name].matrix_local
bpy.context.view_layer.update();assert all([list(r)for r in bpy.data.objects[n].matrix_world]==m for n,m in before.items())
source=ROOT/'blender/collection/I_nautilus_seam_fasteners_r64b.blend';component=ROOT/'app/assets/collection/components/I_nautilus_seam_fasteners_r64b.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/seam_fasteners_r64b';ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/seam_fasteners_r64b/chamber_layout.json','status':'oriented_fastener_release_candidate'}
for row in d['seam_fasteners']['pairs']:row['cap_side']=1 if row['sign']==1 else -1
d['seam_fasteners']['orientation_revision']={'changed_nodes':sorted(allowed),'rotation_parent_axis':'X','radians':math.pi,'all_mesh_geometry_unchanged':True,'other_mesh_world_transforms_preserved':len(before),'scope':'Rigid orientation only; closed seating and release must be checked on this new export.'}
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('R64B_ORIENTED',d['source_sha256'],flush=True)
