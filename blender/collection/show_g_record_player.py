import bpy,pathlib
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_record_player.blend'))
scene=bpy.context.scene;scene.frame_set(1)
scene.camera.location=(1.0,-5.8,3.15);scene.camera.rotation_euler=(Vector((0,0,1.15))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=38
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False;area.spaces.active.shading.type='MATERIAL';area.spaces.active.shading.use_scene_world=True;area.spaces.active.shading.use_scene_lights=True
