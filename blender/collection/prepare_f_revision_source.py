"""Preserve F_complete, copy its authored upper, replace only the control reference assembly."""
import bpy,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
original=ROOT/'blender/collection/F_complete.blend';target=ROOT/'blender/collection/F_refinement_candidate.blend'
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()
if target.exists():
    backup=ROOT/'blender/collection/checkpoints'/('F-revision-'+hashlib.sha256(target.read_bytes()).hexdigest()[:12]+'.blend')
    if not backup.exists():shutil.copy2(target,backup)
bpy.ops.wm.open_mainfile(filepath=str(original));scene=bpy.context.scene;scene.frame_set(1)
# The source was saved with Blender 5.2; keep it byte-for-byte unchanged.
# This 5.1 candidate must pass pose/geometry/source checks before any promotion.
for kind in ['rotary','hold','detent','gauge','service']:
    node=bpy.data.objects.get('CTRL_'+kind)
    if node:
        for o in list(node.children_recursive)+[node]:bpy.data.objects.remove(o,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/f_refined_controls.glb'))
added=set(bpy.data.objects)-before;keep=set()
for kind in ['rotary','hold','detent','gauge','service']:
    node=next(o for o in added if o.name=='FCTRL_'+kind);node.parent=None;node.matrix_parent_inverse=Matrix.Identity(4);keep.add(node);keep.update(node.children_recursive)
for o in added-keep:bpy.data.objects.remove(o,do_unlink=True)
scene['status']='F runtime refinement candidate. Original newer-format source preserved; new controls awaiting take/projection bake.'
scene['preserved_source_sha256']=original_hash
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(target))
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
out=ROOT/'review/F_complete/revision_20260911/full_take';out.mkdir(parents=True,exist_ok=True)
report={'original_source_sha256':original_hash,'candidate_source':str(target.relative_to(ROOT)),'controls_sha256':hashlib.sha256((ROOT/'app/assets/collection/f_refined_controls.glb').read_bytes()).hexdigest(),'original_unchanged':True,'format_note':'F original is a Blender 5.2 file, current tool is 5.1.2. Isolated copy only; verification required before promotion.'}
(out/'source_preparation.json').write_text(json.dumps(report,indent=2)+'\n');print('F_REVISION_SOURCE_PREPARED',json.dumps(report),flush=True)
