"""Task-owned Blender preview channel. Reload appends a new scene and retains
the previous scene, so user edits to an older preview are not discarded."""
import bpy,pathlib,json,time
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
control=ROOT/'review/G_record_player/blender_control.json';ack=ROOT/'review/G_record_player/blender_ack.json'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_record_player.blend'))
last_stamp=0
def view():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False;area.spaces.active.shading.type='MATERIAL';area.spaces.active.shading.use_scene_world=True;area.spaces.active.shading.use_scene_lights=True
def poll():
    global last_stamp
    try:
        if control.exists() and control.stat().st_mtime_ns!=last_stamp:
            cmd=json.loads(control.read_text(encoding='utf-8-sig'));last_stamp=control.stat().st_mtime_ns
            if cmd.get('reload'):
                path=(ROOT/'blender/collection/G_record_player.blend').resolve()
                with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.scenes=['G_Record_Player']
                if dst.scenes and dst.scenes[0]:bpy.context.window.scene=dst.scenes[0]
            scene=bpy.context.window.scene;scene.frame_set(int(cmd.get('frame',1)));view()
            ack.write_text(json.dumps({'ok':True,'scene':scene.name,'frame':scene.frame_current,'time':time.time()}),encoding='utf-8')
    except Exception as e:ack.write_text(json.dumps({'ok':False,'error':str(e)}),encoding='utf-8')
    return .8
view();bpy.app.timers.register(poll,first_interval=.8,persistent=True)
