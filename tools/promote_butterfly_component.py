"""Promote the G1 development checkpoint with exact evidence and recoverable originals."""
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'app/assets/collection/models'
REVIEW = ROOT / 'review/G_optical_curator/butterfly_r2'
CANDIDATE = MODELS / 'G_optical_curator_butterfly_candidate'
LIVE = MODELS / 'G_optical_curator'
SOURCE = ROOT / 'blender/collection/G_butterfly_runtime_candidate.blend'
LIVE_SOURCE = ROOT / 'blender/collection/G_optical_curator.blend'

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def read(path):
    return json.loads(path.read_text())

model_hash = sha(CANDIDATE.with_suffix('.glb'))
metadata_hash = sha(CANDIDATE.with_suffix('.json'))
source_hash = sha(SOURCE)
source_check = read(REVIEW / 'full_take/source_animation_report.json')
assert source_check['passed'] and source_check['source_sha256'] == source_hash
for report in [source_check, read(REVIEW / 'full_take/take_report.json')]:
    assert report['model_sha256'] == model_hash
    assert report['metadata_sha256'] == metadata_hash
take = read(REVIEW / 'full_take/take_report.json')
assert take['all_played'] and take['settled'] and take['wait_errors'] == 0
for name in ['runtime/candidate_qa.json', 'native/packed_checks/candidate_qa.json',
             'hardware_clearance.json', 'player_clearance.json']:
    assert read(REVIEW / name)['passed'], name
native = read(REVIEW / 'native/native_input_report.json')
assert len(native['verified']) >= 5
build = native['build']
stage_model = Path(build['stage']) / 'app/assets/collection/models/G_optical_curator_butterfly_candidate.glb'
assert sha(stage_model) == model_hash
assert sha(stage_model.with_suffix('.json')) == metadata_hash
assert sha(ROOT / 'app/assets/collection/registry.json') == build['main_registry_sha256']
assert sha(Path(build['app']) / 'Contents/Resources/MagicDesk G1 Review.pck') == build['pack_sha256']
assert sha(Path(build['executable'])) == build['binary_sha256']
old_hash = sha(LIVE.with_suffix('.glb'))
backup = ROOT / 'blender/collection/checkpoints' / ('before-butterfly-' + old_hash[:12])
backup.mkdir(parents=True, exist_ok=True)
originals = {}
for path in [LIVE.with_suffix('.glb'), LIVE.with_suffix('.json'), LIVE_SOURCE]:
    target = backup / path.name
    if target.exists():
        assert sha(target) == sha(path), 'Existing backup differs; refuse to overwrite'
    else:
        shutil.copy2(path, target)
    originals[str(path.relative_to(ROOT))] = sha(target)
data = read(CANDIDATE.with_suffix('.json'))
data['source_blend'] = 'blender/collection/G_optical_curator.blend'
data['development_status'] = 'G0/G1 first development pass integrated; whole G and AAA acceptance pending'
normalized = dict(data)
original_metadata = read(CANDIDATE.with_suffix('.json'))
for key in ['source_blend', 'development_status']:
    normalized[key] = original_metadata[key]
assert normalized == original_metadata
for source, target in [(CANDIDATE.with_suffix('.glb'), LIVE.with_suffix('.glb')), (SOURCE, LIVE_SOURCE)]:
    temporary = target.with_suffix(target.suffix + '.tmp')
    shutil.copy2(source, temporary)
    os.replace(temporary, target)
temporary = LIVE.with_suffix('.json.tmp')
temporary.write_text(json.dumps(data, separators=(',', ':')))
os.replace(temporary, LIVE.with_suffix('.json'))
assert sha(LIVE.with_suffix('.glb')) == model_hash and sha(LIVE_SOURCE) == source_hash
result = {'promoted': True, 'scope': 'Development first-pass checkpoint, not completed G or AAA acceptance',
    'model_sha256': model_hash, 'candidate_metadata_sha256': metadata_hash,
    'live_metadata_sha256': sha(LIVE.with_suffix('.json')), 'source_sha256': source_hash,
    'metadata_changes': ['source_blend', 'development_status'],
    'runtime_metadata_equivalent': True, 'backup': str(backup.relative_to(ROOT)),
    'originals': originals, 'native_evidence': 'native/native_input_report.json',
    'remaining': native['limitations']}
(REVIEW / 'promotion.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
