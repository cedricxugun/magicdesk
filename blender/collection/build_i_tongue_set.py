"""Add the other two tongues to the checked first-tongue source, preserving the axial head."""
import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_tongue_factory import add_tongue
from i_tongue_path import TonguePath
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/tongue_set';OUT.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((OUT.parent/'tongue_probe/build.json').read_text());source=ROOT/seed['source'];assert sha(source)==seed['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(source));target=ROOT/'blender/collection/I_tongue_set.blend'
if target.exists():
 old=json.loads((OUT/'build.json').read_text());assert sha(target)==old['source_sha256'],'Unrecorded set edits';(target.parent/'checkpoints'/('I-tongue-set-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
mouth=bpy.data.objects['IAM_Mouth'];col=bpy.data.collections['MODULE_IAM'];scene=bpy.context.scene
groups=[{k:seed[k] for k in ['tongue_index','mesh_names','drive','carriage','spool','spin_sign','pose_steps','rows','states','motion_textures','texture_sha256','field_pixel_sha256','field_sample_front_center','field_sample_stored_center','visible_length','total_material_length']}];paths=[TonguePath(0)]
for index in [1,2]:
 group,path=add_tongue(index,ROOT,ROOT/'app/assets/collection/art/I/tongue_set',mouth,col);groups.append(group);paths.append(path)
for index,group in enumerate(groups):
 group['window']=[index*.15,index*.15+.66]
 for name in [group['drive'],group['carriage'],group['spool']]:bpy.data.objects[name].animation_data_clear()
for frame in range(1,434):
 time=(frame-1)/60;global_feed=max(0,min(1,(time-.4)/2.6)) if time<4.2 else 1-max(0,min(1,(time-4.2)/2.6))
 for group,path in zip(groups,paths):
  start,end=group['window'];v=max(0,min(1,(global_feed-start)/(end-start)));amount=float(v*v*(3-2*v));drive=bpy.data.objects[group['drive']];drive['feed']=amount;drive.keyframe_insert(data_path='["feed"]',frame=frame)
  state=path.frames(amount)[4];carriage=bpy.data.objects[group['carriage']];spool=bpy.data.objects[group['spool']];carriage.location=state['axis'];carriage.keyframe_insert('location',frame=frame);spool.rotation_euler.z=group['spin_sign']*state['angle'];spool.keyframe_insert('rotation_euler',frame=frame)
scene.frame_start=1;scene.frame_end=433;scene.render.fps=60;scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_tongue_set.glb';bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True)
report={'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'tongues':groups,'scope':'Three retained tape-spring tongues with staggered coiling/inverse extension; axial head and full-topology field renderer retained. Packing/inter-tongue contacts, actual appearance, full bearing/motor/case/return supports and main App integration pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_TONGUE_SET_BUILT',flush=True)
