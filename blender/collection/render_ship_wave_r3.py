import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_ship_r3.blend'));scene=bpy.context.scene
out=ROOT/'review/G_optical_curator/ship_r3';out.mkdir(exist_ok=True)
scene.cycles.samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=1100
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
for label,frame,scale,loc,target in [('whole',1,1.16,(1.5,-3.5,1.4),(0,0,.46)),('engine',110,.77,(.8,-3,.98),(0,0,.15)),('engine_front',170,.76,(.1,-3,.6),(0,0,.15))]:
    scene.frame_set(frame);camera=scene.camera;camera.data.ortho_scale=scale;camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
