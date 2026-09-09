import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive.blend'))
scene=bpy.context.scene;marker=scene.timeline_markers.get('2_PLAYING');scene.frame_set(marker.frame+25 if marker else 1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False;area.spaces.active.shading.type='MATERIAL';area.spaces.active.shading.use_scene_world=True;area.spaces.active.shading.use_scene_lights=True
