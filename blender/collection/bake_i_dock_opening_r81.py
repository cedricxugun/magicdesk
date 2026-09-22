"""Independent ordinary opening review source; no unsupported service lift."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r81'
s=json.loads((OUT/'build.json').read_text());qa=json.loads((OUT/'contact_check.json').read_text())
assert qa['source_sha256']==s['source_sha256'] and qa['passed']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
 if o.animation_data:o.animation_data_clear()
nodes={}
for row in s['form_panels']:
 names=[row['node']]
 if 'mechanism' in row:names += [row['mechanism']['carriage'],row['mechanism']['rotor']]
 for name in names:nodes[name]=bpy.data.objects[name].matrix_basis.copy()
def smooth(a,b,t):
 u=max(0.,min(1.,(t-a)/(b-a)));return u*u*(3.-2*u)
for frame in range(1,421):
 t=(frame-1)/30
 u=smooth(2,6,t) if t<6 else 1. if t<8 else 1.-smooth(8,12,t)
 for row in s['form_panels']:
  frac=row.get('lift_fraction',0.);clear=min(1.,u/max(frac,1e-6));turn=max(0.,min(1.,(u-frac)/max(1-frac,1e-6)))
  o=bpy.data.objects[row['node']];o.matrix_basis=nodes[o.name];o.location+=Vector(row.get('lift_blender',[0,0,0]))*clear
  o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle']*turn)@o.rotation_quaternion
  if 'mechanism' in row:
   m=row['mechanism'];car=bpy.data.objects[m['carriage']];rot=bpy.data.objects[m['rotor']]
   car.matrix_basis=nodes[car.name];car.location.z+=m['stroke']*clear;rot.matrix_basis=nodes[rot.name]
   rot.rotation_mode='QUATERNION';rot.rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle']*turn)@rot.rotation_quaternion
 for name in nodes:
  o=bpy.data.objects[name]
  for path in ['location','rotation_quaternion','scale']:o.keyframe_insert(data_path=path,frame=frame,group='Normal opening')
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=420;scene.render.fps=30;scene.frame_set(1)
source=ROOT/'blender/collection/I_base_dock_opening_r81.blend';assert not source.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
(OUT/'opening_source.json').write_text(json.dumps({'body_source_sha256':s['source_sha256'],'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frames':420,'fps':30,'duration':14,'animated_nodes':list(nodes),'scope':'Ordinary closed/open/closed body review only. Fixed adapter stays installed. This is not service, new VFX or full App integration.'},indent=2)+'\n')
print('R81_OPENING_SOURCE_SAVED',flush=True)
