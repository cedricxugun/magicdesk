import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene
# The animation uses a constant camera. More vertical pixels accommodate the
# exploded crown; the sensor grows proportionally, preserving model pixel size.
S.render.resolution_x=2400;S.render.resolution_y=2100;S.render.resolution_percentage=100
S.camera.data.sensor_fit='VERTICAL';S.camera.data.sensor_height=47.25
S.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Helios_Incubator.blend'),compress=True)
print('FULL_ANIMATION_CANVAS_SAVED_NO_GLB_EXPORT',flush=True)
