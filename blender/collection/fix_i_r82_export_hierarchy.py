"""Complete the exported R82 upper hierarchy without moving the authored parts."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[2];BASE=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
old=json.loads((BASE/'installed_r2/build.json').read_text());assert hashlib.sha256((R/old['source']).read_bytes()).hexdigest()==old['source_sha256']
OUT=BASE/'installed_r3';OUT.mkdir(exist_ok=True)
SRC=R/'blender/collection/I_r82_music_receiver_r3.blend';COMP=R/'app/assets/collection/components/I_r82_music_body_r3.glb';assert not SRC.exists() and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));s=bpy.context.scene;root=bpy.data.objects['R82_COIL_ROOT']
assert max(abs(root.matrix_world[r][c]-Matrix.Identity(4)[r][c])for r in range(4)for c in range(4))<1e-8
frames=[1,68,85,100,125,145,175,205,234,290,350,430]
names=[p['node']for p in old['panels']]+[p['mesh']for p in old['panels']]+[j['carriage']for j in old['joints']]+[j['latch']for j in old['joints']]
before={}
for f in frames:
 s.frame_set(f);bpy.context.view_layer.update();before[f]={n:bpy.data.objects[n].matrix_world.copy()for n in names}
s.frame_set(1)
for p in old['panels']:
 node=bpy.data.objects[p['node']];local=node.matrix_basis.copy();node.parent=root;node.matrix_parent_inverse=Matrix.Identity(4);node.matrix_basis=local
error=0.
for f in frames:
 s.frame_set(f);bpy.context.view_layer.update()
 error=max(error,max(abs(bpy.data.objects[n].matrix_world[r][c]-before[f][n][r][c])for n in names for r in range(4)for c in range(4)))
assert error<1e-7,error
# Optical rays must actually disappear when inactive in the editable source.
ma=bpy.data.objects['I_CentralReadingLine'].data.materials[0];ma.node_tree.animation_data_clear();nodes=ma.node_tree.nodes;nodes.clear();links=ma.node_tree.links
out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');tr=nodes.new('ShaderNodeBsdfTransparent');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,.40,.08,1);em.inputs[1].default_value=2
opacity=nodes.new('ShaderNodeValue');opacity.name='I83_ScanVisibility';links.new(opacity.outputs[0],mix.inputs[0]);links.new(tr.outputs[0],mix.inputs[1]);links.new(em.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
for f,v in [(1,0),(187,0),(195,1),(218,1),(232,0),(430,0)]:opacity.outputs[0].default_value=v;opacity.outputs[0].keyframe_insert('default_value',frame=f)
s.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
curves=[o for o in root.children_recursive if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True,export_tangents=True)
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'component':COMP.relative_to(R).as_posix(),'component_sha256':hashlib.sha256(COMP.read_bytes()).hexdigest(),'parent_source':old['source'],'hierarchy_witness':{'frames':frames,'objects':names,'max_world_matrix_error':error},'scope':'Complete exported upper hierarchy including all six moving covers. World poses unchanged at 12 checked states; silent source rays now genuinely transparent when off. Combined receiver/core fit, native visuals and whole art acceptance still pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print('R83_FULL_UPPER_HIERARCHY_EXPORTED',error,report['source_sha256'],flush=True)
