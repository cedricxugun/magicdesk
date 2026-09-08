import bpy,math,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene
old=bpy.data.objects.get('STUDIO_Ground')
if old:bpy.data.objects.remove(old,do_unlink=True)
old=bpy.data.objects.get('STUDIO_Cyclorama')
if old:bpy.data.objects.remove(old,do_unlink=True)
profile=[(-30,-.016),(3,-.016)]
for i in range(1,33):
 a=-math.pi/2+(math.pi/2)*i/32;profile.append((3+4*math.cos(a),4+4*math.sin(a)-.016))
profile.append((7,30));verts=[(x,y,z) for y,z in profile for x in [-30,30]];faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(profile)-1)]
me=bpy.data.meshes.new('Studio_Cyclorama');me.from_pydata(verts,[],faces)
mat=bpy.data.materials['Studio_Backdrop'];p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.78;me.materials.append(mat)
o=bpy.data.objects.new('STUDIO_Cyclorama',me);S.collection.objects.link(o)
for po in me.polygons:po.use_smooth=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
S.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'),compress=True)
if '--skip-review' not in sys.argv:
 S.frame_set(30);S.cycles.samples=96;S.render.filepath=str(ROOT/'review'/'final_closed.png');bpy.ops.render.render(write_still=True)
print('STUDIO_REVIEW_READY',flush=True)
