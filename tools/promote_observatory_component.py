"""Promote the checked observatory working asset while preserving the prior G."""
import json,hashlib,shutil,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
models=ROOT/'app/assets/collection/models';candidate=models/'G_optical_curator_observatory_candidate';live=models/'G_optical_curator'
report_dir=ROOT/'review/G_optical_curator/observatory_r2'
model_hash=hashlib.sha256(candidate.with_suffix('.glb').read_bytes()).hexdigest();metadata_hash=hashlib.sha256(candidate.with_suffix('.json').read_bytes()).hexdigest()
for name in ['external_clearance.json','source_animation_report.json']:
    r=json.loads((report_dir/name).read_text());assert r['passed'] and r['model_sha256']==model_hash and r['metadata_sha256']==metadata_hash,name
for name in ['gear_clearance.json','mount_clearance.json']:assert json.loads((report_dir/name).read_text())['passed'],name
take=json.loads((report_dir/'app/take_report.json').read_text());assert take['all_played'] and take['settled'] and take['wait_errors']==0 and len(take['visited'])==6
old_hash=hashlib.sha256(live.with_suffix('.glb').read_bytes()).hexdigest()
backup=ROOT/'blender/collection/checkpoints'/('before-observatory-'+old_hash[:12]);backup.mkdir(parents=True,exist_ok=True)
source=ROOT/'blender/collection/G_optical_curator.blend';candidate_source=ROOT/'blender/collection/G_optical_curator_observatory_candidate.blend'
for path in [live.with_suffix('.glb'),live.with_suffix('.json'),source]:
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
data=json.loads(candidate.with_suffix('.json').read_text());data['source_blend']='blender/collection/G_optical_curator.blend'
data['development_status']='Observatory geometry pass integrated; complete G material, choreography and native review remain in progress'
for original,target in [(candidate.with_suffix('.glb'),live.with_suffix('.glb')),(candidate_source,source)]:
    temporary=target.with_suffix(target.suffix+'.tmp');shutil.copy2(original,temporary);os.replace(temporary,target)
temporary=live.with_suffix('.json.tmp');temporary.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8');os.replace(temporary,live.with_suffix('.json'))
result={'promoted':True,'model_sha256':model_hash,'candidate_metadata_sha256':metadata_hash,'live_metadata_sha256':hashlib.sha256(live.with_suffix('.json').read_bytes()).hexdigest(),'backup':str(backup.relative_to(ROOT)),'status':'Working geometry update, not AAA or native-app acceptance'}
(report_dir/'promotion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
