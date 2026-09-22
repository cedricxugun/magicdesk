"""Normal-speed 30fps neutral motion witness for an independent R82 source."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[0] if args else 'mechanism_r8'
assert variant in ['mechanism_r8','mechanism_r9']
OUT=R/'review/I_refinement/nautilus_reset_r82'/variant
d=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']))
s=bpy.context.scene;cam=s.camera;cam.location=(-4,-7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.show_shadows=True;s.display.shading.background_type='WORLD';s.world.color=(.075,.075,.075)
for ma in bpy.data.materials:
 if ma.use_nodes and ma.node_tree.nodes.get('Principled BSDF'):ma.diffuse_color=ma.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
s.render.resolution_x=720;s.render.resolution_y=792;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.frame_start=1;s.frame_end=300;s.frame_step=1;s.render.fps=30
frames=OUT/'motion_frames';frames.mkdir(exist_ok=True);s.render.filepath=str(frames/'frame_')
bpy.ops.render.render(animation=True)
(OUT/'movie_render_receipt.json').write_text(json.dumps({'source':d['source'],'source_sha256':d['source_sha256'],'frames':300,'fps':30,'seconds':10,'scope':'Neutral studio shape/motion witness. No final materials, audio/VFX or native performance claim.'},indent=2)+'\n')
print('R82_R8_MOVIE_RENDERED',flush=True)
