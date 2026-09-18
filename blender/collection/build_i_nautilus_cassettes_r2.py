"""Extend the preserved, checked 04 cassette to the three remaining front covers."""
import bpy,json,hashlib,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
OUT=ROOT/'review/I_refinement/nautilus_r1/cassettes_r2';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_nautilus_cassettes_r2.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed_path=ROOT/'review/I_refinement/nautilus_r1/hinge_r1/build.json';seed=json.loads(seed_path.read_text())
assert sha(ROOT/seed['source'])==seed['source_sha256'] and sha(ROOT/seed['component'])==seed['component_sha256']
assert [i+1 for i,r in enumerate(seed['form_panels']) if 'mechanism' in r]==[4]
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded multi-cassette edits'
    folder=OUT/'iterations'/old['source_sha256'][:12];folder.mkdir(parents=True,exist_ok=True)
    for file in OUT.glob('*.json'):shutil.copy2(file,folder/file.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',folder/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-nautilus-cassettes-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
for r in seed['form_panels']:
    o=bpy.data.objects[r['mesh']];assert len(o.data.vertices)>128 and len(o.data.polygons)>64
from i_nautilus_cassette_builder import build_cassette
solids=[];engagement=[]
for panel in [3,5,6]:
    print('BUILDING_ACTUAL_CASSETTE',panel,flush=True)
    mechanism,parts,samples=build_cassette(seed,panel,scene)
    seed['real_cassettes'].append(mechanism);solids+=parts;engagement+=samples
    print('ACTUAL_CASSETTE_DONE',panel,len(parts),flush=True)
scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot']
assert [i+1 for i,r in enumerate(seed['form_panels']) if 'mechanism' in r]==[3,4,5,6]
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_nautilus_cassettes_r2.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
points=[o.matrix_world@v.co for o in root.children_recursive if o.type=='MESH' for v in o.data.vertices]
result={**seed,'parent_source_sha256':seed['source_sha256'],'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'new_cassette_solids':solids,'status':'four_cassette_candidate_checks_pending','review_scope':'Preserved checked 04 mechanism plus newly constructed 03/05/06 with actual surface mounts. All cassette/neighbor/base interactions and source/runtime poses need renewed checks. Power drive, final housings, materials, music VFX/native/art remain incomplete.'}
result['bounds_blender']={'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'guide_engagement.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'samples':engagement,'scope':'Actual mesh axial overlap samples for new 03/05/06 guides, not full collision or native acceptance.'},indent=2)+'\n')
print('FOUR_NAUTILUS_CASSETTES_BUILT',flush=True)
