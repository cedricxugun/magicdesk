"""Actual joint close-up without geometry substitutions."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--'in sys.argv else [];variant=args[0] if args else 'built_r2'
OUT=R/'review/I_refinement/nautilus_reset_r82/back_hardware_r88'/variant;s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene;scene.frame_set(175);bpy.context.view_layer.update()
joint_id=int(args[1]) if len(args)>1 else 5
names={n for row in s['forged_supports'] if row['id']==joint_id for n in [row['support'],row['collar'],row.get('bearing'),row.get('end_cap'),row['guide'],row['rod'],*row['fasteners']]if n}
pts=[o.matrix_world@Vector(v) for name in names for o in [bpy.data.objects[name]] for v in o.bound_box]
centre=Vector([(min(v[k]for v in pts)+max(v[k]for v in pts))/2 for k in range(3)])
cam=scene.camera;cam.location=centre+Vector((4,7,2.08)).normalized()*3;cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.50;cam.data.clip_start=.01
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=96;scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.filepath=str(OUT/('joint_macro.png' if joint_id==5 else f'joint_{joint_id:02d}_macro.png'));bpy.ops.render.render(write_still=True)
