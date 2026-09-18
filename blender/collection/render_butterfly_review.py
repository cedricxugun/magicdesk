"""Render the saved source without rebuilding it or changing its saved cameras."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_butterfly_r2.blend'))
scene=bpy.context.scene;camera=scene.camera;out=ROOT/'review/G_optical_curator/butterfly_r2'
scene.render.resolution_percentage=100;scene.cycles.samples=48
for name,frame,position,target,scale in [
    ('component_open',120,(.35,-3.5,1.25),(0,0,.48),1.25),
    ('component_folded',1,(.35,-3.5,1.25),(0,0,.48),1.25),
    ('component_beat',204,(.35,-3.5,1.25),(0,0,.48),1.25),
    ('component_rear',120,(-.35,3.5,1.25),(0,0,.48),1.25),
    ('hinge_detail',120,(.30,.55,.75),(.022,.047,.55),.27),
    ('hinge_folded_detail',1,(.30,.55,.75),(.022,.047,.55),.27),
    ('mount_socket',120,(.07,-.30,-.16),(0,0,.024),.23)]:
    if '--mount-only' in sys.argv and name!='mount_socket':continue
    for obj in bpy.data.objects:
        if 'ReferenceOriginalDisc' in obj.name:obj.hide_render=name=='mount_socket'
    scene.frame_set(frame);camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
