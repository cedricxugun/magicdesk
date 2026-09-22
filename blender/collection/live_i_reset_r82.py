"""Task-owned visible R82 review. This is an editable mechanism source, no music runtime."""
import bpy,json,time
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/live';OUT.mkdir(exist_ok=True)
target=R/'blender/collection/I_nautilus_reset_r82_mechanism_r9.blend'
assert Path(bpy.data.filepath).resolve()==target.resolve()
bpy.context.preferences.view.show_splash=False
def ready():
 if not bpy.context.window or not bpy.context.screen:return .5
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.shading.type='MATERIAL';sp.shading.use_scene_world=False;sp.shading.use_scene_lights=False;sp.overlay.show_overlays=False
   sp.region_3d.view_perspective='PERSP';sp.region_3d.view_location=Vector((0,0,1.60));sp.region_3d.view_distance=5.25
   sp.region_3d.view_rotation=Vector((4,7,-2.3)).to_track_quat('-Z','Y')
 bpy.context.scene.frame_set(1)
 if not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
 (OUT/'ready.json').write_text(json.dumps({'file':bpy.data.filepath,'scene':bpy.context.scene.name,'playing':bpy.context.screen.is_animation_playing,'time':time.time(),'scope':'visible mechanism review, no audio playback integration'},indent=2))
 return None
bpy.app.timers.register(ready,first_interval=2.)
stamp=0
def poll():
 global stamp
 p=OUT/'control.json'
 if p.exists() and p.stat().st_mtime_ns!=stamp:
  cmd=json.loads(p.read_text(encoding='utf-8-sig'));stamp=p.stat().st_mtime_ns
  if cmd.get('stop') and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
  if 'frame' in cmd:bpy.context.scene.frame_set(int(cmd['frame']))
  if cmd.get('play') and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
  (OUT/'ack.json').write_text(json.dumps({'frame':bpy.context.scene.frame_current,'playing':bpy.context.screen.is_animation_playing,'time':time.time()}))
 return .75
bpy.app.timers.register(poll,first_interval=4.,persistent=True)
