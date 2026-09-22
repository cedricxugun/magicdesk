"""Curated portable checkpoint; update explicit active source/evidence selections before future handoffs."""
import json,re,subprocess,struct,collections,os,argparse
from pathlib import Path
R=Path(__file__).resolve().parents[1];os.chdir(R)
parser=argparse.ArgumentParser(description='Stage only the current runtime, editable sources and compact handoff evidence; preserve local historical experiments.')
parser.add_argument('--stage',action='store_true');args=parser.parse_args()
tracked=set(subprocess.check_output(['git','ls-files','-z']).decode().split('\0')); keep=set(p for p in tracked if p); missing=set(); queue=[]; enqueued=set()
def add(p):
 p=Path(p)
 try:p=p.resolve().relative_to(R)
 except ValueError:return
 name=p.as_posix()
 if p.is_file():
  keep.add(name)
  if name not in enqueued:queue.append(p);enqueued.add(name)
code_ext={'.gd','.gdshader','.glsl','.tscn','.tres','.gdextension','.godot','.cs','.csproj','.props','.targets','.sh','.py','.ps1','.cfg','.uid','.h','.hpp','.c','.cpp','.m','.mm','.swift','.sln','.plist','.entitlements','.cmake'}
for root in ['app','tools','tests','blender','native']:
 for p in (R/root).rglob('*'):
  if any(x in {'.godot','__pycache__','checkpoints','.venv','bin','obj'}for x in p.parts):continue
  if p.is_file() and p.suffix in code_ext:add(p)
# Scan all ordinary runtime code; isolated old review scripts do not pull old assets.
scan=[Path(p)for p in keep if p.startswith('app/')and not p.startswith('app/review/')and Path(p).suffix in code_ext]
queue.extend(scan)
for p in ['app/assets/collection/registry.json','app/assets/collection/control_profiles.json','app/assets/collection/lighting_profiles.json','app/review/i_collection_preview.gd']:add(p);queue.append(Path(p))
visited=set()
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
def reference(s,origin):
 if s.startswith('res://../'):return
 if s.startswith('res://'):
  p=Path('app')/s[6:]
  if p.is_file():add(p)
  elif p.is_dir():missing.add('DIR '+str(p))
  elif '%'not in s and '*'not in s:missing.add(s)
 elif s.startswith(('app/','blender/'))and Path(s).is_file():add(s)
 elif not s.startswith(('data:','http','/'))and Path(s).suffix in {'.png','.jpg','.jpeg','.glb','.json','.ogg','.mp3','.wav','.svg','.tres','.res'}:
  p=origin.parent/s
  if p.is_file():add(p)
while queue:
 p=queue.pop()
 if str(p)in visited:continue
 visited.add(str(p))
 if not p.as_posix().startswith('app/'):continue
 if p.as_posix().startswith('app/review/')and p.name!='i_collection_preview.gd':continue
 if p.suffix=='.json':
  try:
   for s in strings(json.loads(p.read_text(encoding='utf-8'))):reference(s,p)
  except (ValueError,UnicodeDecodeError):pass
 elif p.suffix=='.glb':
  with p.open('rb')as f:
   h=f.read(20)
   if len(h)==20 and h[:4]==b'glTF':
    n,t=struct.unpack('<II',h[12:]);d=json.loads(f.read(n))
    for s in strings(d):reference(s,p)
 elif p.suffix in code_ext:
  try:
   for s in re.findall(r'res://[^\s\"\'`<>\)\]\}]+',p.read_text(encoding='utf-8')):reference(s,p)
  except UnicodeDecodeError:pass
# These runtime directories use a filename prefix plus a selected suffix.
for directory in ['app/assets/collection/art/shared_rotation','app/assets/collection/art/I/echo_r2']:
 for p in Path(directory).rglob('*'):
  if p.is_file():add(p)
# Preserve runtime sources; older rejected candidates remain local.
# Current R90 is an independent candidate, not a runtime replacement.
for report in ['port_edge_r68/build.json','seam_release_r73/build.json']:
 p=Path('review/I_refinement/nautilus_r1')/report;add(p);d=json.loads(p.read_text(encoding='utf-8'))
 for k in ['source','component','mouth_component','mouth_report','candidate_base_component']:
  if k in d:add(d[k])
 if 'mouth_report'in d:
  m=json.loads(Path(d['mouth_report']).read_text(encoding='utf-8'));add(m['source']);add(d['mouth_report'])
for p in ['blender/collection/I_service03_motion_r63b.blend','blender/collection/I_rear03_motion_r71.blend','blender/collection/F_Refined_Controls.blend']:
 add(p)
for name in ['installed_r5/build.json','optical_core_build_r2.json','optical_layout_r2.json']:
 p=Path('review/I_refinement/nautilus_reset_r82/music_interface_r1')/name
 add(p);r82=json.loads(p.read_text(encoding='utf-8'))
 for key in ['source','component','core_source','core_component']:
  if key in r82 and name!='installed_r5/build.json':add(r82[key])
for name in ['old_mouth_inventory.json','fit_search.json','optical_placement_r2.json','runtime_qa_r2.json',
             'legacy_runtime_qa.json','tangent_audit_r2.json','installed_r5/evaluated_geometry.json',
             'installed_r5/export_geometry_check.json','installed_r5/installed_contact_check.json',
             'full_work_r2/result.json','native_r6/render_review.json','native_r6/state_00.png','native_r6/state_03.png',
             'installed_r3/build.json','installed_r3/installed_contact_check.json','native_r2/INVALID.md']:
 add(Path('review/I_refinement/nautilus_reset_r82/music_interface_r1')/name)
for p in Path('app/assets/collection/art/I/r82_music_interface/r2').rglob('*'):
 if p.is_file():add(p)
for name in ['build.json','morph_witnesses.json','runtime_morph_qa.json','cowl_contact_check.json',
             'open.png','native/render_review.json','native/state_03.png',
             'hinge_study/study_dense.json','hinge_study/study_release.json',
             'hinge_study/outer_hinge_release_geometry_only.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/chambers_r3')/name)
for p in ['app/assets/collection/art/I/r84_chambers/r3/chamber_layout.json',
          'review/I_refinement/nautilus_reset_r82/chambers_r2/visibility.json']:
 add(p)
for p in ['blender/collection/I_r90_acoustic_network_r5.blend',
          'app/assets/collection/components/I_r90_acoustic_network_r5.glb',
          'app/assets/collection/art/I/r90_network/r5/chamber_layout.json',
          'app/assets/collection/art/I/r88_forged_supports/r4/chamber_layout.json']:
 add(p)
for name in ['build.json','network_contacts.json','contact_check.json','installed_contact_check.json',
             'import_audit.json','morph_witnesses.json','runtime_morph_qa.json','network_runtime_qa.json',
             'open.png','native/render_review.json','native/state_00.png','native/state_03.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/network_r90/built_r5')/name)
for name in ['paths_r3.json','plate_parameters_r4.json','routing_r2.json']:
 add(Path('review/I_refinement/nautilus_reset_r82/network_r90')/name)
for name in ['build.json','contact_check.json','contact_check_dense.json','open.png','closed.png',
             'native/render_review.json','native/state_03.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/outer_hinge_r2')/name)
for name in ['build.json','contact_check_dense.json','installed_contact_check.json','import_audit.json',
             'open.png','native/render_review.json','native/state_03.png',
             'native_taa/render_review.json','native_taa/state_00.png','native_taa/state_03.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/oblique_hinge_r87')/name)
for name in ['gap_sector_envelope.json','gap_sector_wide.json','r4/build.json','r4/panel02_axis_dense.json']:
 add(Path('review/I_refinement/nautilus_reset_r82/finish_r86')/name)
for name in ['build.json','interface_check.json','contact_check.json','installed_contact_check.json','import_audit.json',
             'joint_macro.png','rear_open.png','native/render_review.json','native/state_00.png','native/state_03.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/back_hardware_r88/built_r4')/name)
for name in ['inventory.json','rear_modifiers.json','rear_closed.png','rear_open.png','rear_diffuse_diagnostic.png',
             'built_r2/missing_seat_diagnosis.json','built_r3/interface_check.json','built_r3/contact_check_dense.json']:
 add(Path('review/I_refinement/nautilus_reset_r82/back_hardware_r88')/name)
for name in ['build.json','cell_contacts.json','contact_check.json','installed_contact_check.json','import_audit.json',
             'morph_witnesses.json','runtime_morph_qa.json','open.png','closed.png',
             'native/render_review.json','native/state_00.png','native/state_03.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/chambers_r89/built_r3')/name)
for name in ['layout_selected.json','rear_ray_probe.json','spill_diagnostic.json',
             'rear_no_chamber_spill/state_03.png','rear_shadow_bias/state_03.png',
             'built_r2/cell_contacts.json','built_r2/rim_contact_diagnosis.json']:
 add(Path('review/I_refinement/nautilus_reset_r82/chambers_r89')/name)
for name in ['build.json','mechanism_check.json','saddle_packaging_search.json','movie_render_receipt.json','movie_validation.json',
             'closed.png','open.png','rear_connection.png','nautilus_mechanism_r82_r9.mp4']:
 add(Path('review/I_refinement/nautilus_reset_r82/mechanism_r9')/name)
for name in ['music_spatial_fit.json','music_fit_open.png']:
 add(Path('review/I_refinement/nautilus_reset_r82/mechanism_r6')/name)
for name in ['build.json','motion_check.json','movie_render_receipt.json','movie_validation.json',
             'closed.png','open.png','side_closed.png','rear_closed.png','mouth_closed.png','top_closed.png',
             'neutral_form.png','curvature_stripes.png','nautilus_form_motion_r82.mp4']:
 add(Path('review/I_refinement/nautilus_reset_r82/form_r2')/name)
# Independent preservation baseline; current service clips still use the R61 body.
for report in ['chamber_motion_r36/build.json','curved_returns_r61/build.json']:
 p=Path('review/I_refinement/nautilus_r1')/report;add(p);d=json.loads(p.read_text(encoding='utf-8'));add(d['component'])
# Selected reproducible inputs and compact evidence for current handoff, never raw takes.
folders=['port_edge_r68','seam_release_r73','coupling_threads_r75','mouth_cassette_release_r74','rear03_motion_r71','rear03_release_r70','shell02_release_r72']
for folder in folders:
 base=Path('review/I_refinement/nautilus_r1')/folder
 for p in base.rglob('*'):
  if not p.is_file():continue
  if any(x in {'frames','initial_without_pose_witness','render','baseline_views','main_previous','render_stills','render_stills_r2','route_r4','partial_bolts_r3'}for x in p.parts):continue
  if p.suffix in {'.json','.txt','.md','.log'}and p.stat().st_size<3_000_000:add(p)
  if p.name in {'04_I_music.png','assembled_front.png','shell_out.png','rear03_release_r71_r2.mp4'}:add(p)
for p in ['review/I_refinement/nautilus_r1/main_adapter_r59/registry.json','review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json','review/I_refinement/nautilus_r1/rear03_release_r70/partial_bolts_r3/bolt_disengagement.json']:
 add(p)
# Current R76 evidence is an explicit allowlist. Do not collect raw frames,
# live controls/screens, diagnostic dumps, invalid macro captures or old logs.
for name in ['build.json','thread_interlock.json','release/probe.json',
             'views/receipt.json','views/01_prepared.png','views/03_withdrawn.png',
             'macro/receipt.json','macro/actual_screw.png','motion_review/report.json',
             'motion_review/qa_report.json','motion_review/validation.json',
             'motion_review/coupling_r76.mp4']:
 add(Path('review/I_refinement/nautilus_r1/coupling_repair_r76')/name)
add('review/I_refinement/nautilus_r1/shell02_after_coupling_r77/probe.json')
add('review/I_refinement/nautilus_r1/base_connection_r78/installed_audit.json')
for name in ['build.json','refinement.json','contact_check.json','opening_source.json','opening_witnesses.json',
             'views/receipt.json','views/01_installed_closed.png','views/04_support_rear.png','views/05_metal_path_cutaway.png',
             'baseline/receipt.json','baseline/04_support_rear.png','motion/receipt.json','motion/qa_receipt.json',
             'motion/validation.json','motion/dock_opening_r81.mp4']:
 add(Path('review/I_refinement/nautilus_r1/base_dock_r81')/name)
# Small reconstruction inputs and failed diagnostics; no failed R79/R80 binaries.
for name in ['base_dock_r79/survey.json','base_dock_r79/contact_check.json',
             'base_dock_r80/build.json','base_dock_r80/build_check.json','base_dock_r80/contact_check.json']:
 add(Path('review/I_refinement/nautilus_r1')/name)
for name in ['01_installed_closed.png','03_support_front.png','04_support_rear.png']:
 add(Path('review/I_refinement/nautilus_r1/coupling_repair_r76/installed')/name)
# Authored design library and licenses, excluding generated score-page review exports.
for p in Path('production').rglob('*'):
 if not p.is_file():continue
 if p.suffix in {'.md','.txt','.json','.ly','.ily','.pdf','.png','.svg'}:add(p)
for p in ['AGENTS.md','HANDOFF.md','PRODUCTION_ART.md','.gitignore','.gitattributes','concepts/production_selection.json']:add(p)
# Small source MIDI and canonical recordings used by the ongoing score-alignment tools.
for i in range(1,4):
 add(f'production/I_refinement/moonlight/engraving/moonlight{i}-staff.midi')
 add(f'production/I_refinement/moonlight/mutopia/moonlight{i}.mid')
 add(f'production/I_refinement/moonlight/recording_source_{i}.html')
 add(f'production/I_refinement/moonlight/pitman_movement_{i}.ogg'if i<3 else 'production/I_refinement/moonlight/pitman_movement_3_original.mp3')
add('tools/geometry/requirements-planar-trim.txt')
# Dedicated currently authored motion assets and active candidate chamber layout.
for directory in ['app/assets/collection/art/I/service_r63','app/assets/collection/art/I/rear03_motion_r71','app/assets/collection/art/I/seam_release_r73','app/assets/collection/art/I/coupling_r76','app/assets/collection/art/I/base_dock_r81']:
 for p in Path(directory).rglob('*'):
  if p.is_file():add(p)
# These superseded R76/R81 datasets are large historical dumps, not inputs to R90.
# Preserve them locally; the current editable source and current reports are sufficient.
excluded_history={
 'review/I_refinement/nautilus_r1/base_dock_r81/build.json',
 'review/I_refinement/nautilus_r1/base_dock_r80/build.json',
 'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json',
}
keep.difference_update(excluded_history)
# Preserve import options only alongside an included source resource.
for name in list(keep):
 for suffix in ['.import','.uid']:
  p=Path(name+suffix)
  if p.is_file():keep.add(p.as_posix())
new=sorted(p for p in keep if p not in tracked and Path(p).is_file());summary=collections.defaultdict(lambda:[0,0])
for p in new:
 key='/'.join(p.split('/')[:2]);summary[key][0]+=1;summary[key][1]+=Path(p).stat().st_size
print('NEW',len(new),'GB',round(sum(Path(p).stat().st_size for p in new)/1e9,3));print('BY_DIR',dict(summary));print('DYNAMIC_OR_MISSING',sorted(missing));print('COMPONENTS',[p for p in new if p.endswith('.glb')]);print('BLENDS',[p for p in new if p.endswith('.blend')])
manifest=Path('production/GIT_HANDOFF_SCOPE.json')
keep.add(manifest.as_posix());keep.add('tools/prepare_git_handoff.py')
manifest.write_text(json.dumps({'scope':'Current runtime dependency closure, latest editable sources/motion and active WIP source; selected small handoff evidence. Historical experiment binaries and raw test captures stay local.','main_body_source':'blender/collection/I_nautilus_port_edge_r68.blend','active_wip_source':'blender/collection/I_r90_acoustic_network_r5.blend','last_valid_combined_source':'blender/collection/I_r90_acoustic_network_r5.blend','active_core_source':'blender/collection/I_r82_acoustic_optics_r2.blend','active_wip_status':'R90 r5 continuous formed acoustic backbone, real sockets and 44 optical meshes connect twelve resonators. Scoped contact, 1440 imported morph witness and 29184 UV-vertex/phase/clock checks pass. Latest guided-network contrast needs visual validation; Movie Maker attempt produced zero-byte AVI with no receipt. Manual pressure/echo network, controls/full service/main App/EXE/transparent performance and remaining queue incomplete. Main registry R68.','last_rejected_engineering_candidate':'blender/collection/I_base_dock_r81.blend','active_design_rework':'production/I_refinement/nautilus_reset_r82/network_r90/README.md','paths':sorted(keep)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if args.stage:
 payload=b'\0'.join(p.encode()for p in sorted(keep)if Path(p).is_file())+b'\0'
 subprocess.run(['git','add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=payload,check=True)
 print('Staged curated handoff')
