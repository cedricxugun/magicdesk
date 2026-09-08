import bpy,numpy as np,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=bpy.context.scene;S.frame_set(1)
S.render.engine='CYCLES';S.cycles.samples=16;S.cycles.use_denoising=False
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
meshes=[o for o in bpy.data.collections['HELIOS_ASSET'].objects if o.type=='MESH']
changed=[]
for m in bpy.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;output=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
 if not output or not output.inputs['Surface'].links:continue
 old=output.inputs['Surface'].links[0].from_socket
 ao=nt.nodes.new('ShaderNodeAmbientOcclusion');ao.only_local=True;ao.samples=24;ao.inputs['Distance'].default_value=.075
 emission=nt.nodes.new('ShaderNodeEmission');nt.links.new(ao.outputs['Color'],emission.inputs['Color']);nt.links.new(emission.outputs[0],output.inputs['Surface'])
 changed.append((nt,output,old,ao,emission))
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
 o.select_set(True);bpy.context.view_layer.objects.active=o
 if 'CavityAO' in o.data.color_attributes:o.data.color_attributes.remove(o.data.color_attributes['CavityAO'])
 layer=o.data.color_attributes.new(name='CavityAO',type='FLOAT_COLOR',domain='CORNER')
 o.data.color_attributes.active_color_index=o.data.color_attributes.find('CavityAO')
 o.data.color_attributes.render_color_index=o.data.color_attributes.find('CavityAO')
S.render.bake.target='VERTEX_COLORS';S.render.bake.use_clear=True
print('LOCAL_CAVITY_BAKE_BEGIN',len(meshes),flush=True)
bpy.ops.object.bake(type='EMIT')
print('LOCAL_CAVITY_BAKE_FINISHED',flush=True)
for nt,output,old,ao,emission in changed:
 nt.links.new(old,output.inputs['Surface']);nt.nodes.remove(ao);nt.nodes.remove(emission)
values=[]
for o in meshes:
 layer=o.data.color_attributes['CavityAO'];v=np.empty(len(layer.data)*4,dtype='float32');layer.data.foreach_get('color',v);v=v.reshape(-1,4)
 values.append(float(np.mean(v[:,:3])))
 # Restrained local occlusion: only recesses darken; no painted-in directional shadows.
 v[:,:3]=np.clip(v[:,:3],.24,1.0)**.70;v[:,3]=1
 layer.data.foreach_set('color',v.ravel())
S.cycles.samples=96;S.cycles.use_denoising=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.collections['HELIOS_ASSET'].objects:o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['HELIOS_ROOT']
params={'filepath':str(ROOT/'app'/'assets'/'helios_model.glb'),'export_format':'GLB','use_selection':True,'export_animations':False,'export_extras':True,'export_apply':True}
keys=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
if 'export_vertex_color' in keys:params['export_vertex_color']='ACTIVE'
if 'export_all_vertex_colors' in keys:params['export_all_vertex_colors']=True
bpy.ops.export_scene.gltf(**params)
(ROOT/'tests'/'cavity_bake.json').write_text(json.dumps({'mesh_count':len(meshes),'mean_local_ao':float(np.mean(values)),'min_mesh_mean':float(min(values))},indent=2))
print('LOCAL_CAVITY_ASSET_READY',len(meshes),min(values),flush=True)
