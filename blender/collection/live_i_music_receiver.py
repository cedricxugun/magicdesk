"""Visible editable current I assembly, with safe append-based future switching."""
import bpy,json,time,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1/live';OUT.mkdir(exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
TARGET=(R/next((a.split('=',1)[1] for a in args if a.startswith('--source=')),'blender/collection/I_r82_music_receiver_r4.blend')).resolve()
assert TARGET.is_relative_to(R/'blender/collection')
displayed_source=str(TARGET)
assert Path(bpy.data.filepath).resolve()==TARGET.resolve()
bpy.context.preferences.view.show_splash=False
def view():
 if not bpy.context.window or not bpy.context.screen:return .5
 for a in bpy.context.screen.areas:
  if a.type=='VIEW_3D':
   sp=a.spaces.active;sp.shading.type='MATERIAL';sp.shading.use_scene_world=False;sp.shading.use_scene_lights=False;sp.overlay.show_overlays=False
   sp.region_3d.view_perspective='PERSP';sp.region_3d.view_location=Vector((0,0,1.62));sp.region_3d.view_distance=5.25;sp.region_3d.view_rotation=Vector((4,7,-2.3)).to_track_quat('-Z','Y')
 bpy.context.scene.frame_set(205)
 (OUT/'ready.json').write_text(json.dumps({'source':bpy.data.filepath,'frame':205,'playing':False,'time':time.time(),'scope':'Current editable assembly, paused for geometry inspection; no claim of native screenshot verification.'},indent=2))
 return None
bpy.app.timers.register(view,first_interval=2.)
stamp=0
def poll():
 global stamp,displayed_source
 file=OUT/'control.json'
 try:
  if file.exists() and file.stat().st_mtime_ns!=stamp:
   cmd=json.loads(file.read_text(encoding='utf-8-sig'));stamp=file.stat().st_mtime_ns
   if cmd.get('stop') and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
   if cmd.get('scene_file'):
    path=(R/cmd['scene_file']).resolve();assert path.is_relative_to(R/'blender/collection')
    with bpy.data.libraries.load(str(path),link=False)as(src,dst):dst.scenes=list(src.scenes)
    bpy.context.window.scene=dst.scenes[0]
    displayed_source=str(path)
   if 'frame'in cmd:bpy.context.scene.frame_set(int(cmd['frame']))
   if cmd.get('play') and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
   (OUT/'ack.json').write_text(json.dumps({'source':displayed_source,'scene':bpy.context.scene.name,'frame':bpy.context.scene.frame_current,'playing':bpy.context.screen.is_animation_playing,'time':time.time()}))
 except Exception as e:(OUT/'ack.json').write_text(json.dumps({'error':str(e)}))
 return .75
bpy.app.timers.register(poll,first_interval=4.,persistent=True)
