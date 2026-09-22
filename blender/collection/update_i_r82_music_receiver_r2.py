"""Use the camera-centred R83 optics without redoing the receiver machining.
Export only the upper body for an isolated Godot combined preview.
"""
import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path(__file__).resolve().parents[2];BASE=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
OUT=BASE/'installed_r2';OUT.mkdir(exist_ok=True)
SRC=R/'blender/collection/I_r82_music_receiver_r2.blend';COMP=R/'app/assets/collection/components/I_r82_music_body_r2.glb';assert not SRC.exists() and not COMP.exists()
old=json.loads((BASE/'installed_r1/build.json').read_text());core=json.loads((BASE/'optical_core_build_r2.json').read_text());placement=json.loads((BASE/'optical_placement_r2.json').read_text());layout=json.loads((BASE/'optical_layout_r2.json').read_text())
body=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));s=bpy.context.scene;s.frame_set(1)
old_module=bpy.data.objects['IAM_MODULE'];old_col=next(c for c in old_module.users_collection if c.name.startswith('MODULE_IAM'))
remove=set(old_col.all_objects)|set(old_module.children_recursive)|{old_module}
for o in list(remove):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.collections.remove(old_col,do_unlink=True)
with bpy.data.libraries.load(str(R/core['source']),link=False)as(src,dst):dst.collections=['MODULE_IAM']
s.collection.children.link(dst.collections[0]);module=bpy.data.objects['IAM_MODULE'];module.matrix_world=Matrix(placement['matrix_blender']);mouth=bpy.data.objects['IAM_Mouth']
for g in core['tongues']:bpy.data.objects[g['drive']].animation_data_clear()
# Keep the original, exact curve and shape fields, with source review timing.
for f in range(1,431):
 opening=max(0,min(1,(f-1)/78)) if f<79 else 1. if f<350 else max(0,1-(f-350)/78)
 for g in core['tongues']:
  lo,hi=g['window'];t=max(0,min(1,(opening-lo)/(hi-lo)));o=bpy.data.objects[g['drive']];o['feed']=t*t*(3-2*t);o.keyframe_insert(data_path='["feed"]',frame=f)
sheet=bpy.data.objects['I_MoonlightStaff'];ma=sheet.data.materials[0];nodes=ma.node_tree.nodes;links=ma.node_tree.links
# Match the real runtime's aspect-preserving score window (quarter 4 for this
# silent source still), rather than squeezing a complete texture tile.
catalog=json.loads((R/'app/assets/collection/art/I/moonlight_candidate/score/manifest.json').read_text());row=catalog['movements'][0]
note=next(a['x']for a in row['anchors']if abs(a['quarter']-4.)<1e-8)
width=row['height']*layout['width']/layout['height'];offset=note-width/2
mapping=next(n for n in nodes if n.type=='VECT_MATH' and n.operation=='MULTIPLY_ADD')
mapping.inputs[1].default_value=(width/row['tile_width'],-1,1);mapping.inputs[2].default_value=(offset/row['tile_width'],1,0)
tex=next(n for n in nodes if n.type=='TEX_IMAGE');tex.extension='CLIP'
mix=next(n for n in nodes if n.type=='MIX_SHADER');old_input=mix.inputs[0].links[0].from_socket
mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.name='I83_ProjectionReveal';links.new(old_input,mult.inputs[0]);links.new(mult.outputs[0],mix.inputs[0])
for f,v in [(1,0),(175,0),(195,1),(218,1),(232,0),(430,0)]:mult.inputs[1].default_value=v;mult.inputs[1].keyframe_insert('default_value',frame=f)
# Bake exactly the same shortest-arc, preserved-roll aiming used by Godot.
rest={}
for tip in layout['scanner']['tips']:
 head=bpy.data.objects[tip['head_node']]
 for c in list(head.constraints):head.constraints.remove(c)
 head.animation_data_clear();head.rotation_mode='QUATERNION'
 rest[head.name]=head.matrix_basis.to_3x3().copy()
for f in range(1,431):
 s.frame_set(f);bpy.context.view_layer.update();focus=mouth.matrix_world@Vector(layout['scanner']['focus'])
 for tip in layout['scanner']['tips']:
  head=bpy.data.objects[tip['head_node']];parent=head.parent.matrix_world.to_3x3();baseline=parent@rest[head.name]
  start_axis=(baseline@Vector((0,0,-1))).normalized();direction=(focus-head.matrix_world.translation).normalized()
  world_basis=start_axis.rotation_difference(direction).to_matrix()@baseline
  head.rotation_quaternion=(parent.inverted()@world_basis).to_quaternion();head.keyframe_insert('rotation_quaternion',frame=f)
# Source-view beam hooks follow the lens point; runtime uses measured shader offsets.
s.frame_set(1);bpy.context.view_layer.update();col=bpy.data.collections['MODULE_IAM']
for i,tip in enumerate(layout['scanner']['tips']):
 ray=bpy.data.objects[tip['ray']];lens=bpy.data.objects[tip['lens_node']]
 target=bpy.data.objects.new('I83_BeamTipHook_'+str(i),None);col.objects.link(target);target.parent=lens;target.location=tip['lens_focus_local_blender']
 bpy.context.view_layer.update();indices=[]
 uv=ray.data.uv_layers.active
 for face in ray.data.polygons:
  for li in face.loop_indices:
   if uv.data[li].uv.y<.001:indices.append(ray.data.loops[li].vertex_index)
 indices=list(set(indices));assert len(indices)==2
 group=ray.vertex_groups.new(name='MeasuredLensStart');group.add(indices,1.,'REPLACE')
 hook=ray.modifiers.new('Physical lens attachment','HOOK');hook.object=target;hook.vertex_group=group.name;hook.matrix_inverse=target.matrix_world.inverted()@ray.matrix_world
 ray.hide_render=False
for name in ['I_CentralReadingLine']+[t['ray']for t in layout['scanner']['tips']]:
 o=bpy.data.objects[name];o.hide_render=False;mat=o.data.materials[0]
 bsdf=mat.node_tree.nodes.get('Principled BSDF')
 if bsdf:
  for f,v in [(1,0),(175,0),(195,2),(218,2),(232,0),(430,0)]:bsdf.inputs['Emission Strength'].default_value=v;bsdf.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
s.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
# This is an upper-body export, not another complete pedestal.
root=bpy.data.objects['R82_COIL_ROOT']
curves=[o for o in root.children_recursive if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True,export_tangents=True)
M=Matrix(placement['matrix_blender']);q=M.to_quaternion()
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'component':COMP.relative_to(R).as_posix(),'component_sha256':hashlib.sha256(COMP.read_bytes()).hexdigest(),'core_report':(BASE/'optical_core_build_r2.json').relative_to(R).as_posix(),'core_source':core['source'],'core_component':core['component'],'core_component_sha256':core['component_sha256'],'music_optics_layout':core['music_optics_layout'],'mouth_placement':{'p':[M.translation.x,M.translation.z,-M.translation.y],'q':[q.x,q.z,-q.y,q.w],'s':[placement['scale']]*3},'panels':body['panels'],'joints':body['joints'],'source_timing_shift_frames':60,'source_score_preview_quarter':4.,'scope':'Camera-centred readable optics with retained receiver machining, real-size score, retained functional mouth and source head/ray following. Upper body exported separately; receiver fit/full core motion/whole-body runtime/art not yet accepted.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
# Reload editable source for render so export conversion is not a saved mutation.
bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;cam=s.camera
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
 for v in p.devices:v.use=v.type=='CUDA'
 s.cycles.device='GPU'
except:pass
s.cycles.samples=64;s.render.resolution_x=1200;s.render.resolution_y=1320
C=Vector(placement['score_center_world'])
for name,f,loc,target,span in [('installed_reading',205,(-4,-7,3.65),(0,0,1.57),4.1),('mouth_reading',205,(-3,-6,2.8),tuple(C),1.65)]:
 s.frame_set(f);bpy.context.view_layer.update();cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R83_CENTERED_RECEIVER_READY',flush=True)
