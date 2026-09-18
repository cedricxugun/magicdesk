"""Copy the current animated source and replace only its observatory component."""
import bpy,json,hashlib,shutil,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
component=ROOT/'blender/collection/G_observatory_r2.blend'
data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator_observatory_candidate.json').read_text());entry=data['g_archive']['contents'][0]
destination=ROOT/data['source_blend']
bpy.ops.wm.open_mainfile(filepath=str(component))
root=bpy.data.objects[entry['root']];names=[root.name]+[o.name for o in root.children_recursive]
if destination.exists():
    backup=ROOT/'blender/collection/checkpoints'/('observatory-candidate-'+hashlib.sha256(destination.read_bytes()).hexdigest()[:12]+'.blend');backup.parent.mkdir(exist_ok=True)
    if not backup.exists():shutil.copy2(destination,backup)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_optical_curator.blend'))
scene=bpy.context.scene;scene.frame_set(1)
old=bpy.data.objects[entry['root']];parent=old.parent
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
with bpy.data.libraries.load(str(component),link=False) as (available,loaded):
    assert all(name in available.objects for name in names)
    loaded.objects=names
collection=bpy.data.collections.new('G_OBSERVATORY_R2_SOURCE');scene.collection.children.link(collection)
for obj in loaded.objects:collection.objects.link(obj)
root=next(obj for obj in loaded.objects if obj.name==entry['root']);root.parent=parent
root.matrix_basis=Matrix.Translation((0,0,entry['mount_offset_y']))@Matrix.Rotation(entry.get('mount_yaw',0),4,'Z')
for obj in loaded.objects:obj.hide_render=True;obj.hide_set(True)
for rig in entry['rig']:assert bpy.data.objects.get(rig['name']),rig['name']
scene['observatory_integration_state']='Geometry replaced in this sibling source; new observatory tracks need baking from candidate take. Original animated source is untouched.'
scene['observatory_reference']=entry['reference']
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(destination))
report={'source':str(destination.relative_to(ROOT)),'original_preserved':'blender/collection/G_optical_curator.blend','new_component_objects':len(names),'rig_nodes':len(entry['rig']),'new_component_baked':False}
(ROOT/'review/G_optical_curator/observatory_r2/source_preparation.json').write_text(json.dumps(report,indent=2)+'\n');print('OBSERVATORY_SOURCE_PREPARED',json.dumps(report),flush=True)
