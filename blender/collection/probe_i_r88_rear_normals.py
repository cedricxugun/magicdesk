"""Same-camera rear appearance attribution; no source file writes."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/back_hardware_r88'
s=json.loads((R/'review/I_refinement/nautilus_reset_r82/oblique_hinge_r87/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene;scene.frame_set(1)
rear=bpy.data.objects['R82_Fixed_Rear_Keel'];mods=[]
for m in rear.modifiers:
 row={'name':m.name,'type':m.type,'show_render':m.show_render}
 for prop in ['width','angle_limit','segments','weight','keep_sharp','harden_normals']:
  if hasattr(m,prop):row[prop]=getattr(m,prop)
 mods.append(row)
 if m.type=='WEIGHTED_NORMAL':m.show_render=False
(OUT/'rear_modifiers.json').write_text(json.dumps(mods,indent=2)+'\n')
print('REAR_MODIFIERS',mods,flush=True)
diffuse='--diffuse' in sys.argv
if diffuse:
 ma=bpy.data.materials.new('R88_DiffuseGeometryDiagnostic');ma.use_nodes=True;nodes=ma.node_tree.nodes;nodes.clear();bs=nodes.new('ShaderNodeBsdfDiffuse');bs.inputs['Color'].default_value=(.40,.40,.40,1);bs.inputs['Roughness'].default_value=.35;output=nodes.new('ShaderNodeOutputMaterial');ma.node_tree.links.new(bs.outputs[0],output.inputs['Surface']);rear.data.materials.clear();rear.data.materials.append(ma)
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=40;scene.render.resolution_x=1000;scene.render.resolution_y=1100
cam=scene.camera;cam.location=(4,7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
scene.render.filepath=str(OUT/('rear_diffuse_diagnostic.png' if diffuse else 'rear_no_weighted_normals.png'));bpy.ops.render.render(write_still=True)
