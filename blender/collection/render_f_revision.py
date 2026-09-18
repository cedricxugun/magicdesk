import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/F_complete/revision_20260911/full_take'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/F_refinement_candidate.blend'))
take=json.loads((OUT/'physical_take.json').read_text());sample=next(s for s in take['samples'] if s['state']['peak_time']>=1.45)
scene=bpy.context.scene;scene.frame_set(sample['frame']);scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.film_transparent=True
scene.render.resolution_x=1200;scene.render.resolution_y=1015;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.type='PERSP';cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=32
for label,location,target,fov in [('source_peak',(.642209,-7.558306,4.298039),(-.007791,.091694,2.26804),46.6167755),('source_console',(.15,-4.,1.22),(0,-1.,.32),43.)]:
    cam.location=location;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32/(2*math.tan(math.radians(fov)/2))
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
print('F_REVISION_SOURCE_RENDERED',sample['frame'],flush=True)
