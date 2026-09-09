"""Actual Cycles reference; separate from native realtime render evidence."""
import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_complete.blend'))
scene=bpy.context.scene;marker=scene.timeline_markers.get('MEMORY_RELIEF');scene.frame_set(marker.frame+66 if marker else 570)
scene.render.engine='CYCLES';scene.cycles.samples=80;scene.cycles.use_denoising=True
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
    for d in pref.devices:d.use=d.type=='CUDA'
    scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.render.resolution_x=1440;scene.render.resolution_y=1160;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.render.filepath=str(ROOT/'production/G_complete/images/G_cycles_reference.png')
bpy.ops.render.render(write_still=True)
print('G_CYCLES_REFERENCE',scene.render.filepath,flush=True)
