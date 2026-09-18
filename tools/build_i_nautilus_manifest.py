# -*- coding: utf-8 -*-
"""Copy only live runtime bindings into a self-contained collection definition."""
import json
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report', default='review/I_refinement/nautilus_r1/port_edge_r68/build.json')
parser.add_argument('--output-dir', help='Write an isolated candidate manifest and registry here.')
args = parser.parse_args()
source = json.loads((root / args.report).read_text())
out = root / (args.output_dir or 'review/I_refinement/nautilus_r1/main_adapter_r59')
out.mkdir(parents=True, exist_ok=True)
manifest_path = out / 'I_nautilus_r59.json' if args.output_dir else root / 'app/assets/collection/models/I_nautilus_r59.json'
manifest_resource = 'res://' + str(manifest_path.relative_to(root / 'app')) if manifest_path.is_relative_to(root / 'app') else 'res://../' + str(manifest_path.relative_to(root))
keys = ['source_sha256', 'component', 'component_sha256', 'mouth_component', 'mouth_component_sha256', 'mouth_placement', 'form_panels', 'finish_profile', 'music_optics_layout', 'music_manifest', 'chamber_response_layout']
spec = {k: source[k] for k in keys}
spec['music_optics_layout'] = 'res://assets/collection/art/I/desktop_optics_r60/score_layout.json'
mouth = json.loads((root / source['mouth_report']).read_text())
spec['mouth_spec'] = {k: mouth[k] for k in ['component_sha256', 'tongues', 'diaphragm', 'aperture_profile']}
def profile(index, key, label, gesture, hint, default=0., **extra):
    return dict(index=index, key=key, label=label, gesture=gesture, hint=hint, min=0., max=1., default=default, **extra)
profiles = [
    profile(1, 'music', '月光 · 播放 / 暂停', 'detent', '轻点播放完整月光奏鸣曲；再次轻点暂停或继续。开口、展壳、出谱后自动开始。', axis='x', steps=2, tap_toggle=True),
    profile(2, 'bellows', '回声压板', 'hold', '按住蓄压，松手让声音从喉口发出并折返；会先停止月光。'),
    profile(3, 'gauge', '声学响应', 'gauge', '播放时跟随录音能量，回声时显示腔室压力。', readonly=True),
    profile(4, 'shell', '展壳 / 收拢', 'detent', '轻点展开或收拢；收拢先收谱，再合外壳和喉口。', axis='x', steps=2, tap_toggle=True),
    profile(5, 'volume', '月光音量', 'rotary', '拖动或滚轮调节月光音量；展示旋转使用底座右侧全息入口。', default=1.)]
manifest = dict(id='I', runtime='nautilus_r59', display_yaw=.45, assembly=spec, control_profiles=profiles, parts=[], controls=[], motions=[], sockets={}, includes_base=False, base_diameter=2.74, development_status='Current compound nautilus; exploded service view and final art still pending')
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
registry = json.loads((root / 'app/assets/collection/registry.json').read_text())
for row in registry['models']:
    if row['id'] == 'I':
        row.update(scene='res://'+source['component'].removeprefix('app/'), metadata=manifest_resource, actions=['唤醒 / 休眠', '月光 · 播放 / 暂停', '回声折返', '展开海螺', '收谱 / 合壳', '旋转 / 暂停', '收拢并退出'], development_status='Current compound nautilus development model; not final art acceptance')
(out / 'registry.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2)+'\n')
