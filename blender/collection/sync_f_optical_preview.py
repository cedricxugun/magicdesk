"""Apply the verified unshaded-quad shader correction to the isolated F source only."""
import bpy,json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/F_complete/revision_20260911/full_take';source=ROOT/'blender/collection/F_refinement_candidate.blend'
original=ROOT/'blender/collection/F_complete.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(source);original_hash=sha(original);bake=json.loads((OUT/'candidate_bake.json').read_text());assert before==bake['source_sha256']
backup=ROOT/'blender/collection/checkpoints'/('F-before-optical-preview-'+before[:12]+'.blend')
if not backup.exists():shutil.copy2(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(source))
used={slot.material for obj in bpy.data.collections['F_REVISION_FIELD'].all_objects for slot in obj.material_slots if slot.material}
changed=[]
for mat in used:
    if not mat.name.startswith('FRevision_Atlas_'):continue
    emit=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
    for link in list(emit.inputs['Strength'].links):mat.node_tree.links.remove(link)
    emit.inputs['Strength'].default_value=1.
    tint=next(n for n in mat.node_tree.nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY')
    tint.inputs[2].default_value=(1,((.96+.055)/1.055)**2.4,((.86+.055)/1.055)**2.4,1)
    mat['preview_reference']='Actual Metal f_atlas probe: EMISSION=0 and6000 unchanged; use unshaded albedo with authored alpha.'
    changed.append(mat.name)
assert len(changed)==4
for obj in bpy.data.collections['F_REVISION_FIELD'].all_objects:
    if any(slot.material and slot.material.name.startswith('FRevision_Atlas_') for slot in obj.material_slots):
        # Godot unshaded overlays use separate explicit lights. They must not
        # become extra Cycles light emitters in reflections/indirect transport.
        obj.visible_diffuse=False;obj.visible_glossy=False;obj.visible_transmission=False;obj.visible_shadow=False
bpy.context.scene['effect_scope']='Mechanical/UI30Hz and field15Hz captured transforms. Atlas unshaded colour/alpha corrected against Metal probe. Point lights still use preview scale40; hardware UV chase and full post-processing not pixel-identical.'
bpy.ops.wm.save_as_mainfile(filepath=str(source));assert sha(original)==original_hash
report={'before_sha256':before,'after_sha256':sha(source),'materials':sorted(changed),'original_preserved':True,'probe':'review/F_complete/revision_20260911/optical_probe/','scope':'Quad material preview correction only; no transforms, meshes, keys or runtime application changes.'}
(OUT/'optical_preview_sync.json').write_text(json.dumps(report,indent=2)+'\n')
bake['source_sha256']=report['after_sha256'];bake['scope']=bpy.context.scene['effect_scope'];bake['optical_preview_patch']=str((OUT/'optical_preview_sync.json').relative_to(ROOT));(OUT/'candidate_bake.json').write_text(json.dumps(bake,indent=2)+'\n')
print('F_OPTICAL_PREVIEW_SYNC',json.dumps(report),flush=True)
