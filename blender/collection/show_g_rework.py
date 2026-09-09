"""Open the current visual-rework geometry without starting an offline render."""
import bpy,json,pathlib,math
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive_refined.blend'))
scene=bpy.context.scene;scene.frame_set(1);data=json.loads((ROOT/'app/assets/collection/models/G_archive_refined.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
for c in data['controls']:
    p=c['samples'][-1];bpy.data.objects[c['name']].matrix_basis=CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
for leaf in data['g_mechanism']['leaves']+data['g_mechanism']['covers']:
    node=bpy.data.objects[leaf['node']]
    for rod in leaf['supports']:
        a=Vector((rod['anchor'][0],-rod['anchor'][2],rod['anchor'][1]));end=node.location+Vector((leaf['side']*.06 if 'face' in leaf else 0,0,rod['height']));v=end-a
        obj=bpy.data.objects[rod['node']];obj.location=(a+end)*.5;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=v.to_track_quat('Z','Y');obj.scale=(1,1,v.length)
bpy.data.objects[data['g_archive']['lift']].location.z=.11;bpy.data.objects[data['g_archive']['slide']].location.y=-.61
for i,item in enumerate(data['g_archive']['contents']):
    root=bpy.data.objects[item['root']]
    for obj in [root]+list(root.children_recursive):obj.hide_set(i!=1);obj.hide_render=i!=1
    if i==1:root.scale=(1.18,)*3
scene.camera.data.lens=40;scene.camera.location=(.90,-7.2,3.8);scene.camera.rotation_euler=(Vector((0,0,1.52))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False;area.spaces.active.shading.type='MATERIAL';area.spaces.active.shading.use_scene_world=True;area.spaces.active.shading.use_scene_lights=True
