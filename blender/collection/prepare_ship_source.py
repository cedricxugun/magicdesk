"""Copy the animated main G into an isolated candidate and append the exact selected G2 candidate."""
import bpy,json,hashlib,shutil,sys
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
main=ROOT/'blender/collection/G_optical_curator.blend';candidate=ROOT/'blender/collection/G_ship_runtime_candidate.blend'
if candidate.exists():
    backup=ROOT/'blender/collection/checkpoints'/('ship-before-animation-'+hashlib.sha256(candidate.read_bytes()).hexdigest()[:12]+'.blend')
    if not backup.exists():shutil.copy2(candidate,backup)
bpy.ops.wm.open_mainfile(filepath=str(main));data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator.json').read_text())
old=bpy.data.objects[data['g_archive']['contents'][2]['root']];parent=old.parent
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
author=json.loads((ROOT/'app/assets/collection/models/G_optical_curator_ship_candidate.json').read_text())['g_archive']['contents'][2]
source=ROOT/author['source_blend']
revision='r3' if author['ship'].get('wave_drive_version',2)==3 else 'r2'
with bpy.data.libraries.load(str(source),link=False) as (available,loaded):loaded.objects=[n for n in available.objects if n.startswith(('GS2_','GS3_'))]
added={o for o in loaded.objects if o};root=next(o for o in added if o.name=='GS2_Ship');keep={root,*root.children_recursive}
collection=bpy.data.collections.new('Ship_runtime_source');bpy.context.scene.collection.children.link(collection)
for obj in keep:collection.objects.link(obj)
root.parent=parent;root.matrix_parent_inverse=Matrix.Identity(4);root.matrix_basis=Matrix.Translation((0,0,.00125))
for obj in added-keep:bpy.data.objects.remove(obj,do_unlink=True)
carrier=bpy.data.objects['GS2_HullCarrier']
fittings=bpy.data.objects.new('GS2_HullFittings',None);collection.objects.link(fittings);fittings.parent=carrier
for obj in list(carrier.children):
    if obj.type in ['MESH','CURVE'] and any(k in obj.name for k in ['Porthole','CaptiveBolt','BoltSlot']):
        local=obj.matrix_basis.copy();obj.parent=fittings;obj.matrix_basis=local
(ROOT/('review/G_optical_curator/ship_'+revision+'/full_take')).mkdir(parents=True,exist_ok=True)
bpy.context.scene['status']='Isolated copy of main G plus refined ship; awaiting exact candidate take bake'
bpy.ops.wm.save_as_mainfile(filepath=str(candidate));bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
report={'main_source_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),'ship_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate':str(candidate.relative_to(ROOT)),'main_overwritten':False}
(ROOT/('review/G_optical_curator/ship_'+revision+'/full_take/source_preparation.json')).write_text(json.dumps(report,indent=2)+'\n');print('SHIP_SOURCE_PREPARED',json.dumps(report),flush=True)
