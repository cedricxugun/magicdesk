"""Actual geometry reference renders. No generated imagery is composited in."""
import bpy,json,pathlib,math
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive_refined.blend'))
scene=bpy.context.scene;data=json.loads((ROOT/'app/assets/collection/models/G_archive_refined.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def matrix(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
for obj in bpy.data.collections['MODULE_G3'].all_objects:obj.animation_data_clear()
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
    for d in pref.devices:d.use=d.type=='CUDA'
    scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=1440;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
folder=ROOT/'review/G_archive/reference_rework';folder.mkdir(parents=True,exist_ok=True)
def capture(name):scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
def supports():
    for leaf in data['g_mechanism']['leaves']+data['g_mechanism']['covers']:
        node=bpy.data.objects[leaf['node']]
        for rod in leaf['supports']:
            anchor=Vector(rod['anchor']);a=Vector((anchor.x,-anchor.z,anchor.y));end=node.location+Vector((leaf['side']*.06 if 'face' in leaf else 0,0,rod['height']));v=end-a
            obj=bpy.data.objects[rod['node']];obj.location=(a+end)*.5;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=v.to_track_quat('Z','Y');obj.scale=(1,1,max(.001,v.length))
for c in data['controls']:bpy.data.objects[c['name']].matrix_basis=matrix(c['samples'][0])
supports()
for item in data['g_archive']['contents']:
    obj=bpy.data.objects[item['root']]
    for child in [obj]+list(obj.children_recursive):child.hide_render=True
scene.camera.data.lens=40;scene.camera.location=(.90,-7.2,3.8);scene.camera.rotation_euler=(Vector((0,0,1.52))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
capture('book_closed')
for c in data['controls']:bpy.data.objects[c['name']].matrix_basis=matrix(c['samples'][-1])
supports()
bpy.data.objects[data['g_archive']['lift']].location.z=.11;bpy.data.objects[data['g_archive']['slide']].location.y=-.61
butterfly=bpy.data.objects[data['g_archive']['contents'][1]['root']]
for child in [butterfly]+list(butterfly.children_recursive):child.hide_render=False
butterfly.scale=(1.18,)*3
for r in data['g_archive']['contents'][1]['rig']:
    obj=bpy.data.objects[r['name']];obj.matrix_basis=matrix(r['home']);obj.rotation_euler.z=float(r['side'])*(.13 if r.get('upper') else .09)
capture('book_butterfly')
# Same meshes, isolated for a fair close-up against the butterfly design sheet.
platform=bpy.data.objects[data['g_archive']['platform']]
visible=set([butterfly]+list(butterfly.children_recursive)+[platform])
for child in platform.children:
    if child.type in ['MESH','CURVE']:visible.add(child)
for obj in bpy.data.objects:
    if obj.type in ['MESH','CURVE','FONT']:obj.hide_render=obj not in visible
platform.parent=None;platform.matrix_world=Matrix.Identity(4)
butterfly.hide_render=False
scene.camera.location=(.48,-3.50,1.48);scene.camera.rotation_euler=(Vector((0,0,.60))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=54
capture('butterfly_closeup')
print('G_REWORK_RENDERED',str(folder),flush=True)
