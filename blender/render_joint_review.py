import bpy,math,pathlib,json,sys
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;cam=S.camera
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
S.render.engine='CYCLES';S.cycles.samples=128;S.cycles.use_denoising=True
S.render.resolution_x=2400;S.render.resolution_y=1600;S.render.resolution_percentage=100
cam.data.sensor_height=36
for name,frame in ([] if '--close-only' in sys.argv else [('final_exploded',340)] if '--exploded-only' in sys.argv else [('final_closed',30),('final_open',150),('final_exploded',340)]):
 S.frame_set(frame)
 if name=='final_exploded':
  # Expand the sensor and pixel canvas together: same model size per pixel,
  # more room above/below the pedestal, with no camera movement or zoom.
  S.render.resolution_y=2100;cam.data.sensor_height=36*2100/1600
 S.render.filepath=str(ROOT/'review'/(name+'.png'));bpy.ops.render.render(write_still=True)
# Close views are actual Cycles renders. These camera changes are never saved or exported.
for name,frame in ([] if '--exploded-only' in sys.argv else [('joint_closed',30),('joint_half_open',88),('joint_fully_open',150)]):
 S.frame_set(frame)
 turn=bpy.data.objects['TURNTABLE'];anchor=turn.matrix_world@Vector((0,-.92,1.06))
 loc=turn.matrix_world@Vector((1.1,-3.45,1.48))
 cam.location=loc;cam.rotation_euler=(anchor-loc).to_track_quat('-Z','Y').to_euler()
 cam.data.type='PERSP';cam.data.lens=58;cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36
 S.render.resolution_x=1800;S.render.resolution_y=1200
 S.render.filepath=str(ROOT/'review'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('JOINT_REVIEW_RENDERED',flush=True)
