"""A minimal, isolated Apple-Silicon inspection app for the current I mouth work."""
import hashlib,json,shutil,subprocess,tempfile,plistlib,datetime,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GODOT='/Applications/Godot.app/Contents/MacOS/Godot';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output([GODOT,'--version'],text=True).startswith('4.7.1.stable.')
parser=argparse.ArgumentParser();parser.add_argument('--report',default='review/I_refinement/part_a_mouth/shutter_r2/tongue_set/build.json');parser.add_argument('--body-report');args=parser.parse_args()
source_report=ROOT/args.report;spec=json.loads(source_report.read_text());geometry=json.loads(source_report.with_name('geometry_check.json').read_text());assert geometry['source_sha256']==spec['source_sha256'] and geometry['scoped_passed'],'Three-tongue checks not ready'
assert sha(ROOT/spec['source'])==spec['source_sha256'];assert sha(ROOT/spec['component'])==spec['component_sha256']
body_report=None;body_spec=None
if args.body_report:
 body_report=ROOT/args.body_report;body_spec=json.loads(body_report.read_text())
 assert body_spec['mouth_component_sha256']==spec['component_sha256'],'Body belongs to another A version'
 assert sha(ROOT/body_spec['source'])==body_spec['source_sha256'] and sha(ROOT/body_spec['component'])==body_spec['component_sha256']
 assert sha(ROOT/'app/assets/helios_model.glb')==body_spec['base_sha256']
 for name in ['core_fit_check.json','finite_geometry_check.json','coupling_fit_check.json','runtime_pose_check.json','base_fit_check.json','sequence_qa.json']:
  check=json.loads(body_report.with_name(name).read_text())
  assert check['passed'] and check['source_sha256']==body_spec['source_sha256'] and check['component_sha256']==body_spec['component_sha256'],name
  if 'mouth_component_sha256' in check:assert check['mouth_component_sha256']==spec['component_sha256'],name
  if name=='sequence_qa.json':
   for path,digest in check['scripts'].items():assert sha(ROOT/'app'/path.removeprefix('res://'))==digest,'Sequence code changed: '+path
 integrated=json.loads((body_report.parent/'viewer_integration/check.json').read_text())
 assert integrated['passed'] and integrated['source_sha256']==body_spec['source_sha256'] and integrated['component_sha256']==body_spec['component_sha256'] and integrated['mouth_component_sha256']==spec['component_sha256'],'Source viewer integration not ready'
checks=spec.get('preview_checks',{})
if 'preserve_authored_frame' in (ROOT/'app/collection/i_tongue_fields.gdshader').read_text():
 frame_check=json.loads((ROOT/checks.get('foil_frames','review/I_refinement/part_a_mouth/shutter_r2/foil_frame/attributes_qa.json')).read_text())
 assert frame_check['passed'] and frame_check['component_sha256']==spec['component_sha256'] and frame_check['binder_sha256']==sha(ROOT/'app/collection/i_tongue_fields.gd'),'Current foil rest-frame geometry check required'
registry=ROOT/'app/assets/collection/registry.json';registry_hash=sha(registry)
stage_parent=ROOT/'dist/staging';stage_parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='i_mouth_review_',dir=stage_parent));project=stage/'app';project.mkdir()
files=['review/i_mouth_viewer.gd','review/i_mouth_viewer.tscn','review/i_mouth_studio.gd','collection/i_tongue_fields.gd','collection/i_tongue_fields.gdshader','collection/i_tongue_set_driver.gd','assets/icon.png','assets/studio_small_09_4k.exr',str(Path(spec['component']).relative_to('app'))]
if body_spec:
 files+=['review/i_conch_sequence.gd','collection/i_shell_linkage_b3_driver.gd','assets/helios_model.glb',str(Path(body_spec['component']).relative_to('app'))]
 spec['conch_body_report']='res://assets/collection/i_conch_body_review.json'
if 'diaphragm' in spec:
 for check in ['combination_check.json','glb_geometry_check.json','rig_qa.json']:
  receipt=json.loads(source_report.with_name(check).read_text());assert receipt['source_sha256']==spec['source_sha256'] and receipt['passed'],check
  if 'component_sha256' in receipt:assert receipt['component_sha256']==spec['component_sha256'],check
 aperture_relative=spec.get('aperture_profile','res://assets/collection/art/I/diaphragm/aperture_profile.json').removeprefix('res://')
 files+=['collection/i_mouth_response_rig.gd','collection/i_acoustics.gd','collection/i_diaphragm_response.gd',aperture_relative]
 files+=['collection/i_echo_presentation.gd','collection/i_echo_wavefront.gdshader','assets/collection/art/I/echo_r2/wavefront.glb','assets/collection/art/I/echo_r2/crest_mask.png','assets/collection/art/I/echo_r2/send.wav','assets/collection/art/I/echo_r2/return.wav']
layout_relative=spec.get('music_optics_layout','res://assets/collection/art/I/moonlight_candidate/current_mouth/layout.json').removeprefix('res://')
if 'music_optics_layout' in spec:assert (ROOT/'app'/layout_relative).exists(),'Declared music layout missing'
if 'diaphragm' in spec and (ROOT/'app'/layout_relative).exists():
 layout=json.loads((ROOT/'app'/layout_relative).read_text())
 assert layout['mouth_component_sha256']==spec['component_sha256']
 if 'optics_mount' in checks:
  mount=json.loads((ROOT/checks['optics_mount']).read_text())
  assert mount['passed'] and mount['mouth_component_sha256']==spec['component_sha256'] and mount['optics_component_sha256']==layout['component_sha256']
 music_check=json.loads((ROOT/checks.get('music_controller','review/I_refinement/moonlight/current_mouth/controller_qa.json')).read_text())
 assert music_check['passed'] and music_check['component_sha256']==spec['component_sha256'] and music_check['optics_sha256']==layout['component_sha256']
 files+=['collection/i_moonlight_controller.gd','collection/i_moonlight_staff.gd','collection/i_moonlight_staff.gdshader','collection/i_music_transport.gd',str(Path(layout['component']).relative_to('app')),layout_relative,'assets/collection/art/I/moonlight_candidate/manifest.json','assets/collection/art/I/moonlight_candidate/score/manifest.json','assets/collection/art/I/moonlight_candidate/score/ATTRIBUTION.md']
 music_manifest=json.loads((ROOT/'app/assets/collection/art/I/moonlight_candidate/manifest.json').read_text())
 if 'response_envelope' in music_manifest:
  response_check=json.loads((ROOT/checks.get('music_response','review/I_refinement/moonlight/current_mouth/response/response_qa.json')).read_text())
  assert response_check['passed'] and response_check['component_sha256']==spec['component_sha256'] and response_check['envelope_sha256']==music_manifest['response_envelope_sha256']
  files.append(music_manifest['response_envelope'].removeprefix('res://'))
 for movement in music_manifest['movements']:files.extend([movement['audio'].removeprefix('res://'),movement['alignment'].removeprefix('res://')])
 score_manifest=json.loads((ROOT/'app/assets/collection/art/I/moonlight_candidate/score/manifest.json').read_text())
 for movement in score_manifest['movements']:files.extend(path.removeprefix('res://') for path in movement['tiles'])
for group in spec['tongues']:files.extend(str(Path(p).relative_to('app')) for p in group['motion_textures'].values())
for relative in sorted(set(files)):
 src=ROOT/'app'/relative;dest=project/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 for suffix in ['.import','.uid']:
  if Path(str(src)+suffix).exists():shutil.copy2(Path(str(src)+suffix),Path(str(dest)+suffix))
config=project/'assets/collection/i_tongue_set_review.json';config.parent.mkdir(parents=True,exist_ok=True);config.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
if body_spec:(project/'assets/collection/i_conch_body_review.json').write_text(json.dumps(body_spec,ensure_ascii=False,indent=2)+'\n')
(project/'project.godot').write_text('''config_version=5

[application]
config/name="MagicDesk I Preview"
run/main_scene="res://review/i_mouth_viewer.tscn"
config/icon="res://assets/icon.png"

[display]
window/size/viewport_width=980
window/size/viewport_height=840
window/size/window_width_override=980
window/size/window_height_override=840
window/size/borderless=false
window/size/transparent=false
window/per_pixel_transparency/allowed=false
window/vsync/vsync_mode=1

[rendering]
renderer/rendering_method="forward_plus"
renderer/rendering_method.mobile="forward_plus"
textures/vram_compression/import_etc2_astc=true
anti_aliasing/quality/msaa_3d=2
environment/defaults/default_clear_color=Color(0.028,0.030,0.029,1)
lights_and_shadows/directional_shadow/size=4096

[audio]
driver/enable_input=false
''')
preset=(ROOT/'app/export_presets.cfg').read_text();preset=preset[preset.index('[preset.1]'):].replace('[preset.1]','[preset.0]').replace('[preset.1.options]','[preset.0.options]');preset=preset.replace('com.cedricxugun.magicdesk','com.cedricxugun.magicdesk.ireview').replace('application/short_version="0.2.1"','application/short_version="0.4.1"').replace('application/version="0.2.1"','application/version="0.4.1"');
if 'diaphragm' in spec:
 preset=preset.replace('com.cedricxugun.magicdesk.ireview','com.cedricxugun.magicdesk.ireview.response')
 config_path=project/'project.godot';config_path.write_text(config_path.read_text().replace('MagicDesk I Preview','MagicDesk I Response Preview'))
if body_spec:
 preset=preset.replace('com.cedricxugun.magicdesk.ireview.response','com.cedricxugun.magicdesk.ireview.conch')
 config_path=project/'project.godot';config_path.write_text(config_path.read_text().replace('MagicDesk I Response Preview','MagicDesk I Conch Preview'))
(project/'export_presets.cfg').write_text(preset)
inputs=[]
for relative in sorted(set(files)):
 for suffix in ['', '.import']:
  file=project/(relative+suffix)
  if file.exists():inputs.append(relative+suffix+'\0'+sha(file))
for generated in ['project.godot','export_presets.cfg','assets/collection/i_tongue_set_review.json']:
 inputs.append(generated+'\0'+sha(project/generated))
if body_spec:inputs.append('assets/collection/i_conch_body_review.json\0'+sha(project/'assets/collection/i_conch_body_review.json'))
code_hash=hashlib.sha256('\n'.join(inputs).encode()).hexdigest()
stem=('MagicDesk-I-Conch-'+body_spec['source_sha256'][:8]) if body_spec else ('MagicDesk-I-Preview-'+spec['source_sha256'][:8])
dest=ROOT/'dist/macos-review'/(stem+'-'+code_hash[:8]+'.app');dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists(),'Refuse to overwrite a review bundle'
subprocess.run([GODOT,'--headless','--editor','--path',str(project),'--import','--quit'],check=True)
subprocess.run([GODOT,'--headless','--path',str(project),'--export-release','macOS',str(dest)],check=True)
shutil.copy2(ROOT/'dist/THIRD_PARTY_NOTICES.txt',dest/'Contents/Resources/THIRD_PARTY_NOTICES.txt')
guide='''MagicDesk · 回声海螺喉口预览

这版用于检查最新的三片卷收、中心触须和材质。仅包含喉口部件，尚非完整海螺/正式版本，也不替换日常 MagicDesk。

点击部件或空格：开合；运动中再次点击可以反向。
按住拖拽：旋转查看。滚轮：放大/缩小。
L：循环演示。R：恢复视角。Esc 或关闭窗口：退出。

此包只为当前 Apple Silicon Mac 构建。完整海螺外壳与整机仍在制作中。
'''
if 'diaphragm' in spec:guide+='\n本轮另含导轮/膜片/回弹联动、声波折返视觉和短促共鸣提示音候选。按住 H 蓄能，松开发出响应；E 单次演示；中途关闭会先卸压再收拢。\n'
if 'collar_clamps' in spec:guide+='\n本轮含贴合瓷壳的卡扣、拉杆与后承座。卡扣固定口沿，正常播放和回声只驱动喉片/膜片；维护松开目前另有独立机构演示。\n'
if 'music_manifest' in globals():
 guide+='\n包含完整《月光奏鸣曲》三个乐章与真实双谱表。点投射器开始月光，点谱面暂停/继续；M播放/暂停，X停止音乐。膜片随录音强弱轻微响应，暂停会逐渐归位。播放中点口沿会淡出谱带与音乐再合拢。当前时间对齐仍为待校准候选。\n'
 (dest/'Contents/Resources/MOONLIGHT_ATTRIBUTION.txt').write_text(music_manifest['attribution']+'\n\n'+(ROOT/'app/assets/collection/art/I/moonlight_candidate/score/ATTRIBUTION.md').read_text())
if body_spec:
 guide='''MagicDesk · 回声海螺机构与月光预览

本机独立预览：当前A喉口、六片机械外壳、连续内芯、金属支承和唯一真实底座。造型、材料与操作匣仍在精修，不替换日常MagicDesk，也不是AAA完成声明。

点击口沿/壳体或空格：开合。关闭时先卸压/收谱，再依次收壳，最后合拢喉口；中途可反向。
点投射器或按M：开始完整《月光奏鸣曲》三个乐章；点谱面或M暂停/继续，X停止音乐。
H按住蓄能后松开，E演示一次回声；音乐期间避免叠加回声。
拖拽旋转、滚轮缩放、R复位、L循环，Esc或关闭窗口退出。

谱面来自真实双谱表，具体时间映射仍待音乐细审。此包只为当前Apple Silicon Mac构建。
'''
(dest/'Contents/Resources/使用说明.txt').write_text(guide)
for file in dest.rglob('*'):
 if not file.is_file() or file.is_symlink():continue
 with file.open('rb') as f:magic=f.read(4)
 if magic not in [b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf']:continue
 archs=subprocess.check_output(['lipo',str(file),'-archs'],text=True).split();assert 'arm64' in archs
 if len(archs)>1:
  temp=file.with_name(file.name+'.arm64');subprocess.run(['lipo',str(file),'-thin','arm64','-output',str(temp)],check=True);temp.chmod(file.stat().st_mode);temp.replace(file)
subprocess.run(['codesign','--force','--deep','--sign','-',str(dest)],check=True);subprocess.run(['codesign','--verify','--deep','--strict','--verbose=2',str(dest)],check=True)
assert sha(registry)==registry_hash
info=plistlib.loads((dest/'Contents/Info.plist').read_bytes());binary=dest/'Contents/MacOS'/info['CFBundleExecutable'];pack=next(dest.rglob('*.pck'));archive=dest.with_name(dest.stem+'-arm64.zip')
subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(dest),str(archive)],check=True)
report={'app':str(dest),'zip':str(archive),'stage':str(stage),'bundle_id':info['CFBundleIdentifier'],'executable':str(binary),'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'pack_sha256':sha(pack),'binary_sha256':sha(binary),'zip_sha256':sha(archive),'registry_unchanged':True,'scope':'Isolated arm64 native mouth inspection app; source contact check passed, but native launch/input/appearance still require verification. Not full conch or AAA acceptance.'}
report['code_sha256']=code_hash
report['code_hash_includes_import_settings']=True
report['code_hash_includes_generated_runtime_config']=True
if body_spec:
 report.update({'source_sha256':body_spec['source_sha256'],'component_sha256':body_spec['component_sha256'],'mouth_source_sha256':spec['source_sha256'],'mouth_component_sha256':spec['component_sha256'],'base_sha256':body_spec['base_sha256'],'scope':'Isolated arm64 conch composition candidate with A, shell/core/support and complete Moonlight. Scoped source/sequence checks passed; native launch/input/visual/audio verification still required. Main App unchanged; not AAA acceptance.'})
out=(body_report.parent if body_report else source_report.parent)/'native';out.mkdir(parents=True,exist_ok=True)
if (out/'build.json').exists():
 previous=json.loads((out/'build.json').read_text());previous_code=previous.get('code_sha256','')
 if previous_code:
  history=out/previous_code[:8];history.mkdir(exist_ok=True);shutil.copy2(out/'build.json',history/'build.json')
  if (out/'native_check.json').exists():
   check=json.loads((out/'native_check.json').read_text())
   if check.get('code_sha256')==previous_code:shutil.copy2(out/'native_check.json',history/'native_check.json')
(out/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(out/'native_check.json').write_text(json.dumps({'source_sha256':report['source_sha256'],'component_sha256':report['component_sha256'],'code_sha256':code_hash,'status':'pending_native_observation','scope':'Export/signature alone do not establish native input or visual acceptance.'},indent=2)+'\n')
print('I_MOUTH_MAC_REVIEW_BUILT',json.dumps(report,ensure_ascii=False),flush=True)
