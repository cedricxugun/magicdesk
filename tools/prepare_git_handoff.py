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
 if not str(p).startswith('app/'):continue
 if str(p).startswith('app/review/')and p.name!='i_collection_preview.gd':continue
 if p.suffix=='.json':
  try:
   for s in strings(json.loads(p.read_text())):reference(s,p)
  except (ValueError,UnicodeDecodeError):pass
 elif p.suffix=='.glb':
  with p.open('rb')as f:
   h=f.read(20)
   if len(h)==20 and h[:4]==b'glTF':
    n,t=struct.unpack('<II',h[12:]);d=json.loads(f.read(n))
    for s in strings(d):reference(s,p)
 elif p.suffix in code_ext:
  try:
   for s in re.findall(r'res://[^\s\"\'`<>\)\]\}]+',p.read_text()):reference(s,p)
  except UnicodeDecodeError:pass
# These runtime directories use a filename prefix plus a selected suffix.
for directory in ['app/assets/collection/art/shared_rotation','app/assets/collection/art/I/echo_r2']:
 for p in Path(directory).rglob('*'):
  if p.is_file():add(p)
# Current editable body/mouth, two active motion stages and the latest WIP source.
for report in ['port_edge_r68/build.json','seam_release_r73/build.json']:
 p=Path('review/I_refinement/nautilus_r1')/report;add(p);d=json.loads(p.read_text())
 for k in ['source','component','mouth_component','mouth_report']:
  if k in d:add(d[k])
 if 'mouth_report'in d:
  m=json.loads(Path(d['mouth_report']).read_text());add(m['source']);add(d['mouth_report'])
for p in ['blender/collection/I_service03_motion_r63b.blend','blender/collection/I_rear03_motion_r71.blend','blender/collection/F_Refined_Controls.blend']:
 add(p)
# Independent preservation baseline; current service clips still use the R61 body.
for report in ['chamber_motion_r36/build.json','curved_returns_r61/build.json']:
 p=Path('review/I_refinement/nautilus_r1')/report;add(p);d=json.loads(p.read_text());add(d['component'])
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
for directory in ['app/assets/collection/art/I/service_r63','app/assets/collection/art/I/rear03_motion_r71','app/assets/collection/art/I/seam_release_r73']:
 for p in Path(directory).rglob('*'):
  if p.is_file():add(p)
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
manifest.write_text(json.dumps({'scope':'Current runtime dependency closure, latest editable sources/motion and active WIP source; selected small handoff evidence. Historical experiment binaries and raw test captures stay local.','main_body_source':'blender/collection/I_nautilus_port_edge_r68.blend','active_wip_source':'blender/collection/I_nautilus_seam_release_r73.blend','paths':sorted(keep)},ensure_ascii=False,indent=2)+'\n')
if args.stage:
 payload=b'\0'.join(p.encode()for p in sorted(keep)if Path(p).is_file())+b'\0'
 subprocess.run(['git','add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=payload,check=True)
 print('Staged curated handoff')
