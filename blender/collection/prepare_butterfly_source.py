"""Copy the animated main G into an isolated candidate and append finished G1."""
import bpy,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
main=ROOT/'blender/collection/G_optical_curator.blend';candidate=ROOT/'blender/collection/G_butterfly_runtime_candidate.blend'
if candidate.exists():
    backup=ROOT/'blender/collection/checkpoints'/('butterfly-before-animation-'+hashlib.sha256(candidate.read_bytes()).hexdigest()[:12]+'.blend')
    if not backup.exists():shutil.copy2(candidate,backup)
bpy.ops.wm.open_mainfile(filepath=str(main));data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator.json').read_text())
old=bpy.data.objects[data['g_archive']['contents'][1]['root']];parent=old.parent
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
source=ROOT/'blender/collection/G_butterfly_r2.blend'
with bpy.data.libraries.load(str(source),link=False) as (available,loaded):loaded.objects=[n for n in available.objects if n.startswith('GB2_')]
added={o for o in loaded.objects if o};root=next(o for o in added if o.name=='GB2_Butterfly');keep={root,*root.children_recursive}
collection=bpy.data.collections.new('Butterfly_runtime_source');bpy.context.scene.collection.children.link(collection)
for obj in keep:collection.objects.link(obj)
root.parent=parent;root.matrix_parent_inverse=Matrix.Identity(4);root.matrix_basis=Matrix.Translation((0,0,.00125))
for obj in added-keep:bpy.data.objects.remove(obj,do_unlink=True)
bpy.context.scene['status']='Isolated copy of main G plus finished butterfly; awaiting exact candidate take bake'
bpy.ops.wm.save_as_mainfile(filepath=str(candidate));bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
report={'main_source_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),'butterfly_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate':str(candidate.relative_to(ROOT)),'main_overwritten':False}
(ROOT/'review/G_optical_curator/butterfly_r2/materials/source_preparation.json').write_text(json.dumps(report,indent=2)+'\n');print('BUTTERFLY_SOURCE_PREPARED',json.dumps(report),flush=True)
