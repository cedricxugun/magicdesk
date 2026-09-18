"""Fit three real two-stage cassettes to the current nautilus, preserving its body."""
import bpy,json,hashlib,sys,shutil,struct,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
OUT=ROOT/'review/I_refinement/nautilus_r1/upper_cassettes_r19';OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/'blender/collection/I_nautilus_upper_cassettes_r19.blend';COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_upper_cassettes_r19.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=ROOT/'review/I_refinement/nautilus_r1/trunnion_support_r18/build.json';seed=json.loads(parent.read_text());assert sha(ROOT/seed['source'])==seed['source_sha256']=='37fae48487d23170c11361b0f975b4d58ae375c180df4a4966d4d7edf339f8e8';assert json.loads((parent.parent/'checkpoint.json').read_text())['source_sha256']==seed['source_sha256'];assert [i+1 for i,r in enumerate(seed['form_panels']) if r['active']]==[3,4,5];assert not any('mechanism' in r for r in seed['form_panels'])
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded upper-cassette edits';archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-upper-cassettes-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];panels=[3,4,5]
allowed={'IN1_%s_%02d'%(kind,panel) for panel in panels for kind in ['PorcelainPanel','FixedRearShell','Hinge']}
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [d.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed};source_skins={n:fingerprint(bpy.data.objects[n]) for n in allowed if n in bpy.data.objects and not n.startswith('IN1_Hinge_')}
from i_nautilus_cassette_builder import build_cassette
seed['real_cassettes']=[];solids=[];engagement=[]
for panel in panels:
    try:
        print('BUILD_CURRENT_CASSETTE',panel,flush=True);mechanism,parts,samples=build_cassette(seed,panel,scene);seed['real_cassettes'].append(mechanism);solids.extend(parts);engagement.extend(samples)
        work=OUT/'work';work.mkdir(parents=True,exist_ok=True);progress=work/('after_panel_%02d.blend'%panel);bpy.ops.wm.save_as_mainfile(filepath=str(progress),compress=True)
        (work/('after_panel_%02d.json'%panel)).write_text(json.dumps({'parent_source_sha256':seed['source_sha256'],'working_source':str(progress.relative_to(ROOT)),'working_source_sha256':sha(progress),'completed_panels':[r['panel_number'] for r in seed['real_cassettes']],'spec':seed,'solids':solids,'engagement':engagement,'scope':'Unverified construction checkpoint, not a finished component or App.'},indent=2)+'\n')
    except Exception:
        failed=OUT/('failed_panel_%02d_%s.blend'%(panel,sha(Path(__file__))[:8]));bpy.ops.wm.save_as_mainfile(filepath=str(failed),compress=True);(OUT/'construction_failure.json').write_text(json.dumps({'parent_source_sha256':seed['source_sha256'],'panel':panel,'completed_panels':[r['panel_number'] for r in seed['real_cassettes']],'diagnostic_source':str(failed.relative_to(ROOT)),'error':traceback.format_exc(),'scope':'Incomplete diagnostic scene; never promote by filename.'},indent=2)+'\n');raise
scene.frame_set(1);bpy.context.view_layer.update();changed=[n for n,f in protected.items() if fingerprint(bpy.data.objects[n])!=f];assert not changed,changed
assert [i+1 for i,r in enumerate(seed['form_panels']) if 'mechanism' in r]==panels
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
r={**seed,'parent_source_sha256':seed['source_sha256'],'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'new_cassette_solids':solids,'cassette_source_skins':source_skins,'status':'three_current_cassettes_candidate_checks_pending','review_scope':'Three guided translation/captive-pivot cassettes fit to the current03/04/05 covers; body, mouth, supports and other source geometry preserved. Actual contacts, pose transfer, power drive, housings, art/audio/native sequence remain unverified or incomplete.'}
(OUT/'build.json').write_text(json.dumps(r,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'passed':not changed,'protected_mesh_count':len(protected),'changed_protected':changed,'allowed_changes':sorted(allowed)},indent=2)+'\n');(OUT/'guide_engagement.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'samples':engagement,'scope':'Guide axial engagement at selected source frames; not full collision or native acceptance.'},indent=2)+'\n');print('CURRENT_THREE_CASSETTES_BUILT',r['source_sha256'],flush=True)
