"""Export a native G2 review bundle from a private staging copy of app/."""
import hashlib,json,os,shutil,subprocess,tempfile,plistlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GODOT='/Applications/Godot.app/Contents/MacOS/Godot'
assert subprocess.check_output([GODOT,'--version'],text=True).startswith('4.7.1.stable.')
registry=ROOT/'app/assets/collection/registry.json';original=hashlib.sha256(registry.read_bytes()).hexdigest()
stage_parent=ROOT/'dist/staging';stage_parent.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='ship_mac_',dir=stage_parent));app=stage/'app'
shutil.copytree(ROOT/'app',app,ignore=shutil.ignore_patterns('.godot','.DS_Store'))
# Cached imports are copied, never linked back into the working project.
shutil.copytree(ROOT/'app/.godot/imported',app/'.godot/imported')
for path in app.rglob('*'):
    if path.is_file() and path.stat().st_size<1024 and path.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):raise RuntimeError('Unresolved LFS '+str(path))
path=app/'assets/collection/registry.json';data=json.loads(path.read_text());g=next(x for x in data['models'] if x['id']=='G')
g['scene']='res://assets/collection/models/G_optical_curator_ship_candidate.glb';g['metadata']='res://assets/collection/models/G_optical_curator_ship_candidate.json';g['development_status']='G2 isolated native review; not final all-model acceptance';path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
path=app/'project.godot';path.write_text(path.read_text().replace('config/name="MagicDesk"','config/name="MagicDesk G2 Review"'))
path=app/'export_presets.cfg';path.write_text(path.read_text().replace('application/bundle_identifier="com.cedricxugun.magicdesk"','application/bundle_identifier="com.cedricxugun.magicdesk.g2review"'))
dest=ROOT/'dist/macos-review/MagicDesk-G2-review.app';dest.parent.mkdir(exist_ok=True)
subprocess.run([GODOT,'--headless','--editor','--path',str(app),'--import','--quit'],check=True)
subprocess.run([GODOT,'--headless','--path',str(app),'--export-release','macOS',str(dest)],check=True)
shutil.copy2(ROOT/'dist/THIRD_PARTY_NOTICES.txt',dest/'Contents/Resources/THIRD_PARTY_NOTICES.txt')
shutil.copy2(ROOT/'使用说明-macOS.md',dest/'Contents/Resources/使用说明-macOS.md')
for path in dest.rglob('*'):
    if not path.is_file() or path.is_symlink():continue
    with path.open('rb') as f:magic=f.read(4)
    if magic not in [b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf']:continue
    archs=subprocess.check_output(['lipo',str(path),'-archs'],text=True).split();assert 'arm64' in archs
    if len(archs)>1:
        temp=path.with_name(path.name+'.arm64');subprocess.run(['lipo',str(path),'-thin','arm64','-output',str(temp)],check=True);temp.chmod(path.stat().st_mode);temp.replace(path)
subprocess.run(['codesign','--force','--deep','--sign','-',str(dest)],check=True)
subprocess.run(['codesign','--verify','--deep','--strict','--verbose=2',str(dest)],check=True)
assert hashlib.sha256(registry.read_bytes()).hexdigest()==original,'Working registry changed'
info=plistlib.loads((dest/'Contents/Info.plist').read_bytes());binary=dest/'Contents/MacOS'/info['CFBundleExecutable'];pack=next(dest.rglob('*.pck'))
report={'app':str(dest),'stage':str(stage),'bundle_id':info['CFBundleIdentifier'],'executable':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'pack_sha256':hashlib.sha256(pack.read_bytes()).hexdigest(),'main_registry_sha256':original,'main_registry_unchanged':True,'scope':'Isolated arm64 ad-hoc review bundle; native validation not implied by export/signature'}
revision='r3' if json.loads((ROOT/'app/assets/collection/models/G_optical_curator_ship_candidate.json').read_text())['g_archive']['contents'][2]['ship'].get('wave_drive_version',2)==3 else 'r2'
out=ROOT/('review/G_optical_curator/ship_'+revision+'/native');out.mkdir(parents=True,exist_ok=True);(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('SHIP_NATIVE_BUILD',json.dumps(report),flush=True)
