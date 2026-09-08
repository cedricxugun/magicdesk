import bpy,math,pathlib,json,sys
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;S.frame_set(1)
hdr=bpy.data.images.load(str(ROOT/'app'/'assets'/'studio_small_09_4k.exr'),check_existing=True)
nt=S.world.node_tree
for n in nt.nodes:
 if n.type=='TEX_ENVIRONMENT':n.image=hdr
nt.nodes.get('Background').inputs['Strength'].default_value=.30
for name,loc,power,size,sy,color in [('Key',(-3.2,-4,4.8),480,2.6,4,(1,.94,.85)),('Rim',(3.5,2,4),640,1.2,3.5,(.85,.90,1)),('Front',(0,-6,2.5),120,4,2,(1,.97,.90))]:
 o=bpy.data.objects.get('STUDIO_'+name)
 if not o:continue
 o.location=loc;o.rotation_euler=(Vector((0,0,1.8))-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.shape='RECTANGLE';o.data.size=size;o.data.size_y=sy;o.data.color=color
core_mat=bpy.data.materials['Solar_Core_Emission'];ps=core_mat.node_tree.nodes.get('Principled BSDF')
for frame,value in [(1,.05),(24,.8),(140,.8),(170,2.5),(180,1.8),(195,3.2),(210,2.4),(235,2.0),(250,.8),(530,.8),(570,.03),(600,.03)]:
 ps.inputs['Emission Strength'].default_value=value;ps.inputs['Emission Strength'].keyframe_insert('default_value',frame=frame)
old=bpy.data.objects.get('Core_Photometric_Bounce')
if old:bpy.data.objects.remove(old,do_unlink=True)
light=bpy.data.lights.new('Core_Photometric_Bounce','POINT');light.color=(1,.18,.02);light.shadow_soft_size=.16
o=bpy.data.objects.new('Core_Photometric_Bounce',light);S.collection.objects.link(o);o.parent=bpy.data.objects['CORE_LIFT'];o.location=(0,0,0)
for frame,value in [(1,0),(24,16),(145,16),(180,55),(205,75),(245,20),(260,16),(530,16),(570,0),(600,0)]:light.energy=value;light.keyframe_insert('energy',frame=frame)
turn=bpy.data.objects['TURNTABLE']
for frame,value in [(1,0),(145,.38),(250,.72),(260,.72),(375,.72),(465,.72),(530,1.06),(600,1.18)]:turn.rotation_euler.z=value;turn.keyframe_insert('rotation_euler',frame=frame)
meta=json.loads((ROOT/'app'/'assets'/'mechanism.json').read_text(encoding='utf-8'))
for b,frame in zip(meta['buttons'],[4,50,160,260,375,490,585]):
 cap=bpy.data.objects[b['cap']];home=cap.location.copy()
 for f,amount in [(1,0),(frame,0),(frame+2,.016),(frame+9,0),(600,0)]:cap.location=home-Vector((0,0,amount));cap.keyframe_insert('location',frame=f)
cam=S.camera;cam.location=(.65,-7.65,3.95);cam.rotation_euler=(Vector((0,0,1.92))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=36;cam.data.lens=36/(2*math.tan(math.radians(34)/2))
S.cycles.samples=128;S.cycles.use_denoising=True;S.render.resolution_x=2400;S.render.resolution_y=1600;S.render.resolution_percentage=100
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast';S.view_settings.exposure=-.1
S.frame_set(1)
for area in bpy.context.screen.areas if bpy.context.screen else []:
 if area.type=='VIEW_3D':area.spaces.active.shading.type='RENDERED';area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
for im in bpy.data.images:
 if im.source=='FILE':
  try:im.pack()
  except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'),compress=True)
for name,frame in ([] if '--skip-review' in sys.argv else [('final_closed',30),('final_open',150),('final_exploded',340)]):
 S.frame_set(frame);S.render.filepath=str(ROOT/'review'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FINAL_BLENDER_REVIEW_READY',flush=True)
