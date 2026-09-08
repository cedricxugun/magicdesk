import bpy,math,pathlib,json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;cam=S.camera
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
S.frame_set(30);S.cycles.samples=128;S.cycles.use_denoising=True
S.render.resolution_x=2400;S.render.resolution_y=1600;S.render.resolution_percentage=100
cam.data.sensor_height=36;S.render.filepath=str(ROOT/'review/final_closed.png');bpy.ops.render.render(write_still=True)
cam.location=(0,-6.4,1.50);cam.rotation_euler=(Vector((0,-.15,.43))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='PERSP';cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36;cam.data.lens=65
S.render.resolution_x=2000;S.render.resolution_y=1150;S.render.filepath=str(ROOT/'review/seven_buttons.png');bpy.ops.render.render(write_still=True)
meta=json.loads((ROOT/'app/assets/mechanism.json').read_text());S.frame_set(1)
info=[]
for b in meta['buttons']:
 mount=bpy.data.objects[b['mount']];cap=bpy.data.objects[b['cap']]
 angle=math.degrees(math.atan2(mount.location.y,mount.location.x));home=cap.location.copy();S.frame_set(587);press=(home-cap.location).length;S.frame_set(1)
 info.append({'index':b['index'],'angle':angle,'local_home':list(home),'function':b['function'],'press_at_587':press})
(ROOT/'tests/seven_button_review.json').write_text(json.dumps({'buttons':info,'part_count':meta['part_count'],'controls':len(meta['controls'])},indent=2))
print('SEVEN_BUTTON_REVIEW_READY',flush=True)
