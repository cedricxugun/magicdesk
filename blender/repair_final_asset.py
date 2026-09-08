import bpy,bmesh,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;S.frame_set(1);fixed=0
for o in bpy.data.collections['HELIOS_ASSET'].objects:
 if o.type!='MESH' or '_BaseJoint_' not in o.name:continue
 bm=bmesh.new();bm.from_mesh(o.data);pending=set(bm.faces);layer=bm.loops.layers.float_color.get('CavityAO')
 while pending:
  face=pending.pop();component=[face];stack=[face]
  while stack:
   f=stack.pop()
   for e in f.edges:
    for ff in e.link_faces:
     if ff in pending:pending.remove(ff);stack.append(ff);component.append(ff)
  if not all(len(e.link_faces)==2 for f in component for e in f.edges):continue
  vol=0.
  for f in component:
   vv=[v.co for v in f.verts]
   for k in range(1,len(vv)-1):vol+=vv[0].dot(vv[k].cross(vv[k+1]))/6
  if vol<-.000000001:
   fixed+=1
   for f in component:
    f.normal_flip()
    if layer:
     for loop in f.loops:loop[layer]=(1,1,1,1)
 bm.to_mesh(o.data);bm.free();o.data.update()
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.collections['HELIOS_ASSET'].objects:o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['HELIOS_ROOT']
# Interactive emission uses its own power controller, so export the powered reference level.
bpy.data.materials['Solar_Core_Emission'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.8
bpy.ops.export_scene.gltf(filepath=str(ROOT/'app'/'assets'/'helios_model.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True)
(ROOT/'tests'/'normals_repair.json').write_text(json.dumps({'fixed_inverted_closed_components':fixed,'expected':12},indent=2))
S.frame_set(30);S.cycles.samples=96;S.render.filepath=str(ROOT/'review'/'final_closed.png');bpy.ops.render.render(write_still=True)
S.frame_set(150);S.render.filepath=str(ROOT/'review'/'final_open.png');bpy.ops.render.render(write_still=True)
print('FINAL_ASSET_REPAIRED',fixed,flush=True)
