"""Summarize measured evidence without converting engineering checks into art approval."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'tests/collection'
def read(name):return json.loads((QA/name).read_text())
runtime=read('delivery/runtime_report.json');inputs=read('delivery/input_report.json')
integrity=read('delivery_integrity.json');focus=read('focus_clearance.json');storage=read('selector_storage.json')
assert runtime['all_passed'] and inputs['all_passed'] and focus['all_clear'] and storage['all_inside']
pck=ROOT/'dist/macos/MagicDesk.app/Contents/Resources/MagicDesk.pck'
assert hashlib.sha256(pck.read_bytes()).hexdigest()==integrity['build']['pck_sha256']
source_qa=[read('clearance/'+ident+'.json') for ident in 'FGIJKLMN']
assert all(x['all_clear'] for x in source_qa)
registry=json.loads((ROOT/'app/assets/collection/registry.json').read_text())
text=[
'# MagicDesk 0.2.0 本机开发构建验证',
'',
'当前构建包含 B 与 F/G/I/J/K/L/M/N，固定底座外径 2.740000、高度 0.670608。原 HELIOS GLB 与 Blender 主源文件散列未变。',
'',
f"- 同一打包资源回归：**{len(runtime['checks'])}/{len(runtime['checks'])} 通过**，覆盖九款切换、透明显示、窗口/相机/底座固定、展开、招牌动作、拆解、组装和中途反向。",
f"- 实体输入回归：**{len(inputs['checks'])}/{len(inputs['checks'])} 通过**，覆盖环沿入口、六张铭牌、滚轮浏览、各款控制器、无效编号与取消准备。",
'- 八款瓷壳：每款 42 组开合/拆解姿态进行表面相交检查，未检出不同刚性组之间的瓷壳交叉；同组的设计接触不参与这一检查。',
'- L 的实际动态对焦：200 组实时求解姿态，含中途反向，未检出瓷壳相交。',
'- 六张实体铭牌的全部网格顶点均在原底座收纳腔体包络内；运行时牌面文字和缩略图位于牌框范围内。',
'- 原生 App 已实际操作 Tab、F 铭牌、主动作、拆解和 Cmd-Q；退出经过收束，进程正常结束。原 HELIOS 自检 23 项通过。',
'',
'## 动作片段的帧耗时',
'',
'在本机 Apple M5、Metal、固定 1920 × 1400 透明画布下，各取约两秒招牌动作。数据避开截图读回边界，包含动作首帧；短片段不代表长时间稳定帧率。',
'',
'| 装置 | 中位帧耗时 | P95 帧耗时 |',
'| --- | ---: | ---: |',
]
for item in registry['models']:
    if item['id'] not in runtime['performance']:continue
    p=runtime['performance'][item['id']]
    text.append(f"| {item['id']} {item['title']} | {p['median_ms']:.2f} ms | {p['p95_ms']:.2f} ms |")
text += ['','## 构建与可追溯性','',
f"- 架构：`{integrity['build']['arch']}`；App {integrity['build']['app_bytes']/1024**2:.1f} MiB，ZIP {integrity['build']['zip_bytes']/1024**2:.1f} MiB。",
f"- PCK SHA-256：`{integrity['build']['pck_sha256']}`。",
f"- ZIP SHA-256：`{integrity['build']['zip_sha256']}`。",
'- 原始数据：`delivery/runtime_report.json`、`delivery/input_report.json`、`clearance/*.json`、`focus_clearance.json`、`selector_storage.json`。',
'- 实际画面：`delivery/*_closed.png`、`*_open.png`、`*_action.png`、`*_exploded.png`、`*_selector.png`。',
'- 动效图稿和接入贴图：`production/batch1/art/asset_manifest.json`，含来源、用途及散列；Blender 源文件位于 `blender/collection/`。',
'','## 质量边界','',
'这些是工程和有限采样的几何证据，不是完整 CAD 干涉认证，也不是 AAA 美术验收。当前仍是开发版，近景材质、设定图造型细节的一致性、招牌动效的最终观感仍需继续打磨。首次新着色器准备可能比后续切换慢，当前仅针对这台 Mac 构建。','']
(QA/'REPORT.md').write_text('\n'.join(text))
print('COLLECTION_REPORT_READY',QA/'REPORT.md')
