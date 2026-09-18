import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/F_complete/revision_20260911/optical_probe'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/F_refinement_candidate.blend'));scene=bpy.context.scene;scene.frame_set(1)
for obj in bpy.data.objects:obj.animation_data_clear();obj.hide_render=True
mat=bpy.data.objects['FRevision_ReceiverWave_0'].data.materials[0];image=bpy.data.images.load(str(OUT/'constant.png'),check_existing=True);image.colorspace_settings.name='sRGB'
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE':node.image=image
old=bpy.data.objects['FRevision_ReceiverWave_0'];obj=bpy.data.objects.new('ColorProbe',old.data.copy());scene.collection.objects.link(obj);obj.hide_render=False
world=bpy.data.worlds.new('ProbeBlack');world.use_nodes=True;next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=0;scene.world=world
camera=bpy.data.objects.new('ProbeCamera',bpy.data.cameras.new('ProbeCamera'));scene.collection.objects.link(camera);camera.location=(0,-2,0);camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=1.1;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=False;scene.render.film_transparent=False;scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='None';scene.view_settings.exposure=0.;scene.view_settings.gamma=1.
for gain in [.1,.3,.5,1.0]:
    obj.color=(gain/8.,0,0,1);scene.render.filepath=str(OUT/('blender_%02d.png'%round(gain*10)));bpy.ops.render.render(write_still=True)
emit=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
for link in list(emit.inputs['Strength'].links):mat.node_tree.links.remove(link)
emit.inputs['Strength'].default_value=1.
for gain in [.1,.3,.5,1.0]:
    obj.color=(gain/8.,0,0,1);scene.render.filepath=str(OUT/('blender_unlit_%02d.png'%round(gain*10)));bpy.ops.render.render(write_still=True)
tint=next(n for n in mat.node_tree.nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY')
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
tint.inputs[2].default_value=(1,linear(.96),linear(.86),1)
for gain in [.1,.3,.5,1.0]:
    obj.color=(gain/8.,0,0,1);scene.render.filepath=str(OUT/('blender_linear_tint_%02d.png'%round(gain*10)));bpy.ops.render.render(write_still=True)
print('F_ATLAS_COLOR_PROBE_DONE',flush=True)
