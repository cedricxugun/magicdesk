"""Visible, task-owned Blender review; loading later versions keeps old scenes."""
import bpy, json, time
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/I_nautilus_coupling_r76.blend'))
bpy.context.preferences.view.show_splash=False
spec=json.loads((OUT/'build.json').read_text())
for row in spec['form_panels']:
    o=bpy.data.objects[row['node']];o.animation_data_clear()
    o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender'])
    o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
    if 'mechanism' in row:
        m=row['mechanism']
        for k in ['carriage','rotor']:bpy.data.objects[m[k]].animation_data_clear()
        bpy.data.objects[m['carriage']].location=(0,0,m['stroke'])
        r=bpy.data.objects[m['rotor']];r.rotation_mode='QUATERNION'
        r.rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
def set_view():
    # open_mainfile during startup invalidates the previous UI context until
    # Blender finishes creating the new window/screen on its main loop.
    if not bpy.context.window or not bpy.context.screen:return .5
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.overlay.show_overlays=False
            sp.shading.type='MATERIAL';sp.shading.use_scene_world=False;sp.shading.use_scene_lights=False
            sp.region_3d.view_perspective='PERSP';sp.region_3d.view_location=Vector((0,0,1.55))
            sp.region_3d.view_distance=5.2
            sp.region_3d.view_rotation=Vector((5,6,-2.8)).to_track_quat('-Z','Y')
    return None
bpy.app.timers.register(set_view,first_interval=1.)
stamp=0
def tick():
    global stamp
    file=OUT/'live_control.json'
    try:
        if file.exists() and file.stat().st_mtime_ns!=stamp:
            cmd=json.loads(file.read_text(encoding='utf-8-sig'));stamp=file.stat().st_mtime_ns
            if cmd.get('scene_file'):
                path=(ROOT/cmd['scene_file']).resolve()
                assert path.is_relative_to(ROOT/'blender/collection')
                with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.scenes=list(src.scenes)
                bpy.context.window.scene=dst.scenes[0]
            if 'frame' in cmd:bpy.context.scene.frame_set(cmd['frame'])
            if cmd.get('play') and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
            if cmd.get('stop') and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
            if cmd.get('screenshot'):bpy.ops.screen.screenshot(filepath=str(OUT/'blender_screen.png'))
            (OUT/'live_ack.json').write_text(json.dumps({'ok':True,'scene':bpy.context.scene.name,'time':time.time()}))
    except Exception as e:(OUT/'live_ack.json').write_text(json.dumps({'ok':False,'error':str(e)}))
    return .75
bpy.app.timers.register(tick,first_interval=2.,persistent=True)
print('I_SERVICE_BLENDER_REVIEW_READY',flush=True)
