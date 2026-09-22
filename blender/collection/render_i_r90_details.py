"""Actual network macros, with all source geometry present."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];version=args[0]if args else 'r5';BASE=R/'review/I_refinement/nautilus_reset_r82/network_r90';OUT=BASE/f'built_{version}'
s=json.loads((OUT/'build.json').read_text());paths=json.loads((BASE/('paths_r3.json' if version in {'r4','r5'} else f'paths_{version}.json')).read_text());route=json.loads((BASE/('routing_r2.json'if version!='r1'else'routing_r1.json')).read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene;scene.frame_set(205)
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=96;scene.render.resolution_x=1200;scene.render.resolution_y=1000;cam=scene.camera;direction=Vector((-4,-7,2.08)).normalized();cam.data.ortho_scale=.55;cam.data.clip_start=.01
root=next(j for j in paths['junctions']if j['root']);choices=[]
for j in paths['junctions']:
 degree=sum(seg['start']==j['node'] or seg['end']==j['node']for seg in paths['segments'])
 if degree>=3 and route['nodes'][str(j['node'])].get('visible',False):choices.append(j)
targets=[('supply_macro',root)]
if choices:targets.append(('branch_macro',max(choices,key=lambda j:j['radius']*Vector(j['n']).dot(direction))))
for name,j in targets:
 point=Vector(j['p']);cam.location=point+direction*3;cam.rotation_euler=(point-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
