"""Promote reviewed F gear geometry and one disassembly route, with exact bindings."""
from pathlib import Path
import json,hashlib,shutil,os
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/F_complete/revision_20260911/gears'
MODELS=ROOT/'app/assets/collection/models';live=MODELS/'F_complete.glb';candidate=MODELS/'F_gears_candidate.glb'
source=ROOT/'blender/collection/F_gear_refinement.blend';target=ROOT/'blender/collection/F_refinement_candidate.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
build=read(OUT/'build.json');patch=read(OUT/'glb_patch.json')
assert sha(source)==build['source_candidate_sha256'] and sha(target)==build['source_input_sha256']
assert sha(live)==patch['input_sha256'] and sha(candidate)==patch['candidate_sha256']
for name in ['mesh_check','neighbor_check','dense_service_check']:
    report=read(OUT/(name+'.json'));assert report['passed'] and report['source_sha256']==sha(source),name
gpu=next(o for o in read(OUT/'render/review.json')['observations'] if o['candidate'])
assert gpu['glb_sha256']==sha(candidate) and gpu['one_base'] and gpu['source_root_bounds_error']<.000005 and gpu['source_route_error']<.000002
old_data=read(live.with_suffix('.json'));new_data=read(candidate.with_suffix('.json'))
comparison=json.loads(json.dumps(new_data));comparison['source_blend']=old_data['source_blend']
next(p for p in comparison['parts'] if p['name']=='F2_P_Differential').pop('route')
assert comparison==old_data,'Unexpected unrelated metadata change'
backup=ROOT/'blender/collection/checkpoints'/('F-before-gears-'+sha(live)[:12]);backup.mkdir(exist_ok=True)
originals={}
for path in [live,live.with_suffix('.json'),target,OUT.parent/'full_take/candidate_bake.json']:
    dest=backup/path.name
    if dest.exists():assert sha(dest)==sha(path),'Backup already exists for different input'
    else:shutil.copy2(path,dest)
    originals[str(path.relative_to(ROOT))]=sha(path)
for a,b in [(candidate,live),(source,target)]:
    temporary=b.with_suffix(b.suffix+'.tmp');shutil.copy2(a,temporary);os.replace(temporary,b)
new_data['source_blend']='blender/collection/F_refinement_candidate.blend'
live.with_suffix('.json').write_text(json.dumps(new_data,separators=(',',':'))+'\n')
bake_path=OUT.parent/'full_take/candidate_bake.json';bake=read(bake_path);bake['source_sha256']=sha(target);bake['gear_patch']='review/F_complete/revision_20260911/gears/promotion.json';bake_path.write_text(json.dumps(bake,indent=2)+'\n')
result={'promoted':True,'model_sha256':sha(live),'metadata_sha256':sha(live.with_suffix('.json')),'source_sha256':sha(target),'backup':str(backup.relative_to(ROOT)),'originals':originals,'scope':'Two gear meshes and differential route only. Existing take hashes remain historical; separate source/GPU/clearance reports bind this patch. No native or AAA acceptance implied.'}
(OUT/'promotion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
