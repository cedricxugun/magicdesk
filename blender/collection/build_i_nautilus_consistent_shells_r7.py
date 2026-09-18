"""Give the adjacent porcelain pieces compatible walls, preserving their exterior."""
import bpy,json,hashlib,struct,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_native_receiver_shell as shell
OUT=ROOT/'review/I_refinement/nautilus_r1/consistent_shells_r7';OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/'blender/collection/I_nautilus_consistent_shells_r7.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/nautilus_r1/core_bridge_r4/build.json').read_text());metadata=json.loads((ROOT/'review/I_refinement/nautilus_r1/wall_metadata_r5/build.json').read_text());mapping=json.loads((ROOT/'review/I_refinement/nautilus_r1/wall_metadata_r5/object_meshes.json').read_text())
assert seed['source_sha256']=='0e1193ca0b6e45d55cfbdebb07add0ceca4a3bdb2a681ea2bb723a5cfb5c6d8d'==sha(ROOT/seed['source']);assert metadata['source_sha256']==mapping['source_sha256']==sha(ROOT/metadata['source'])
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded shell edits';archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-nautilus-consistent-shells-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];names=sorted(mapping['objects'])
def signature(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return [h.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in names}
with bpy.data.libraries.load(str(ROOT/metadata['source']),link=False) as (src,dst):dst.meshes=[mapping['objects'][name] for name in names]
rows=[]
for name,mesh in zip(names,dst.meshes):
    reinforcement={'center':[-.52895,.16109,1.04977],'radius':.10,'reason':'Measured lower mouth-to-body heel corner, reinforced inward only'} if name=='IN1_PorcelainPanel_02' else None
    rows.append(shell.rebuild(bpy.data.objects[name],mesh,reinforcement));print('CONSISTENT_SHELL_BUILT',name,flush=True)
bpy.context.view_layer.update();changed=[name for name,value in protected.items() if signature(bpy.data.objects[name])!=value];assert not changed,changed
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_nautilus_consistent_shells_r7.glb';bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':seed['source_sha256'],'consistent_shells':rows,'status':'consistent_wall_candidate_checks_pending','review_scope':'All porcelain outer source triangles, positions and corner normals retained. Adjacent inner walls use one consistent native solver; 02 lower heel has authored inward reinforcement. All metal, A and base meshes retained exactly. Wall distance, joints, chamber seats and native/art acceptance still require review.'}
result['core_bridge'].pop('receiver_recess',None)
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed,'other_meshes':len(protected),'changed':changed,'shells':rows},indent=2)+'\n');print('CONSISTENT_NAUTILUS_SHELLS_BUILT',flush=True)
