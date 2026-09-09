import bpy,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/collection/G_complete.blend'))
marker=bpy.context.scene.timeline_markers.get('MEMORY_RELIEF')
bpy.context.scene.frame_set(marker.frame+60 if marker else 1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
            area.spaces.active.shading.type='MATERIAL';area.spaces.active.shading.use_scene_world=True;area.spaces.active.shading.use_scene_lights=True
