"""Fixed-view geometry review and normal-speed study movie from saved R82."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/form_r2'
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/collection/I_nautilus_reset_r82_form_r2.blend'))
s=bpy.context.scene;cam=s.camera
def view(loc,target=(0,0,1.57)):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
def still(n):
 s.render.filepath=str(OUT/(n+'.png'));bpy.ops.render.render(write_still=True)
s.render.resolution_x=880;s.render.resolution_y=968;s.cycles.samples=32
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='CUDA'
 s.cycles.device='GPU'
except:pass
for name,loc in [('rear_closed',(0,8,2.3)),('mouth_closed',(-8,0,2.3)),('top_closed',(0,-.001,9))]:
 s.frame_set(1);view(loc);still(name)
# Deliberately material-free neutral form check.
clay=bpy.data.materials.new('R82_Review_Clay');clay.diffuse_color=(.3,.3,.3,1);clay.use_nodes=True
bsdf=clay.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.32,.32,.32,1);bsdf.inputs['Roughness'].default_value=.55
s.view_layers[0].material_override=clay;view((-4,-7,3.65));still('neutral_form')
# Reflection stripes diagnose actual surface curvature rather than adding detail.
chrome=bpy.data.materials.new('R82_Review_Curvature');chrome.use_nodes=True
p=chrome.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.65,.65,.65,1);p.inputs['Metallic'].default_value=1;p.inputs['Roughness'].default_value=.055
s.view_layers[0].material_override=chrome
w=s.world;oldstrength=w.node_tree.nodes['Background'].inputs[1].default_value
tex=w.node_tree.nodes.new('ShaderNodeTexCoord');wave=w.node_tree.nodes.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X';wave.inputs['Scale'].default_value=3
ramp=w.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT';ramp.color_ramp.elements[0].position=.40;ramp.color_ramp.elements[1].position=.55
w.node_tree.links.new(tex.outputs['Normal'],wave.inputs['Vector']);w.node_tree.links.new(wave.outputs['Fac'],ramp.inputs[0]);w.node_tree.links.new(ramp.outputs['Color'],w.node_tree.nodes['Background'].inputs[0]);w.node_tree.nodes['Background'].inputs[1].default_value=1
lights=[o for o in bpy.data.objects if o.type=='LIGHT']
for o in lights:o.hide_render=True
still('curvature_stripes')
for o in lights:o.hide_render=False
s.view_layers[0].material_override=None
for n in [tex,wave,ramp]:w.node_tree.nodes.remove(n)
w.node_tree.nodes['Background'].inputs[0].default_value=(.16,.17,.20,1);w.node_tree.nodes['Background'].inputs[1].default_value=oldstrength
# Movie is a neutral, complete-frame motion witness. Final appearance is in
# the separate Cycles stills, not claimed from a studio viewport animation.
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl'
s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH';s.display.shading.show_shadows=True
s.display.shading.background_type='WORLD';s.world.color=(.075,.075,.075)
for ma in bpy.data.materials:
 if ma.use_nodes and ma.node_tree.nodes.get('Principled BSDF'):
  ma.diffuse_color=ma.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
s.render.resolution_x=720;s.render.resolution_y=792
s.render.resolution_percentage=100
view((-4,-7,3.65));s.render.image_settings.file_format='PNG'
frames=OUT/'motion_frames_30';frames.mkdir(exist_ok=True)
s.render.filepath=str(frames/'frame_')
s.frame_start=1;s.frame_end=300;s.render.fps=30
s.frame_step=1
bpy.ops.render.render(animation=True)
(OUT/'movie_render_receipt.json').write_text(json.dumps({'source':'blender/collection/I_nautilus_reset_r82_form_r2.blend','source_timeline_fps':30,'rendered_stride':1,'video_fps':30,'duration_seconds':10,'purpose':'neutral studio normal-time shape and opening study; not real-time app performance or final materials/effects'},indent=2))
print('R82_REVIEW_RENDER_DONE',flush=True)
