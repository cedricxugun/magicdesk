import bpy,bmesh,math,json,pathlib
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;S.frame_set(1)
COL=bpy.data.collections['HELIOS_ASSET'];BASE=bpy.data.objects['BASE_FIXED']
if bpy.data.objects.get('BUTTON_06_MOUNT'):raise RuntimeError('Shutdown button already exists; refusing to duplicate it')
meta=json.loads((ROOT/'app/assets/mechanism.json').read_text(encoding='utf-8'))
old_mounts=[bpy.data.objects[b['mount']] for b in meta['buttons']]
old_centers=[o.matrix_world.translation.copy() for o in old_mounts]
rotation=Matrix.Rotation(math.radians(-9),4,'Z');moved=[0]*6
# The fixed bezels were merged into BASE_FIXED. Rotate only their small,
# disconnected components; the continuous fascia and pedestal stay untouched.
for ob in list(BASE.children):
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data);pending=set(bm.verts)
 while pending:
  first=pending.pop();component=[first];stack=[first]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    other=e.other_vert(v)
    if other in pending:pending.remove(other);stack.append(other);component.append(other)
  points=[ob.matrix_world@v.co for v in component]
  center=sum(points,Vector())/len(points)
  index=min(range(6),key=lambda k:(center-old_centers[k]).length)
  if (center-old_centers[index]).length>.22:continue
  if max((p-old_centers[index]).length for p in points)>.255:continue
  local=ob.matrix_world.inverted()@rotation@ob.matrix_world
  for v in component:v.co=local@v.co
  moved[index]+=1
 bm.to_mesh(ob.data);bm.free();ob.data.update()
if min(moved)<20:raise RuntimeError('Insufficient bezel components moved: '+str(moved))
for i,mount in enumerate(old_mounts):
 a=math.radians(-144+18*i);radial=Vector((math.cos(a),math.sin(a),0))
 mount.location=radial*1.373+Vector((0,0,.31));mount.rotation_mode='QUATERNION';mount.rotation_quaternion=radial.to_track_quat('Z','Y')
M={'Red':bpy.data.materials['Cherry_Enamel'],'Chrome':bpy.data.materials['Polished_Nickel'],'Steel':bpy.data.materials['Dark_Brushed_Steel'],'Black':bpy.data.materials['Graphite'],'Rubber':bpy.data.materials['Black_Polymer'],'Amber':bpy.data.materials['Amber_Light'],'Letter':bpy.data.materials['Ivory_Engraving'],'Brass':bpy.data.materials['Warm_Nickel']}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(encoding='utf-8'),str(ROOT/'blender/fast_geometry.py'),'exec'))
angle=math.radians(-36);radial=Vector((math.cos(angle),math.sin(angle),0))
mount=bpy.data.objects.new('BUTTON_06_MOUNT',None);COL.objects.link(mount);mount.parent=BASE;mount.location=radial*1.373+Vector((0,0,.31));mount.rotation_mode='QUATERNION';mount.rotation_quaternion=radial.to_track_quat('Z','Y')
cyl('Button_6_Gasket',.146,.018,'Rubber',mount,(0,0,.002))
cyl('Button_6_Bezel',.138,.043,'Steel',mount,(0,0,.023))
torus('Button_6_MilledRim',.124,.009,'Chrome',mount,(0,0,.051))
for j in range(36):
 a=j*math.tau/36;cyl('Button_6_KnurledEdge',.003,.012,'Chrome',mount,(.135*math.cos(a),.135*math.sin(a),.032),n=8)
cyl('Button_6_Status_Jewel',.007,.004,'Amber',mount,(0,.152,.006),n=16)
cu=bpy.data.curves.new('Button_6_Index','FONT');cu.body='07';cu.align_x='CENTER';cu.size=.021;cu.extrude=.00035;cu.bevel_depth=.00012
label=bpy.data.objects.new('Button_6_Index',cu);COL.objects.link(label);label.parent=mount;label.location=(0,-.157,.012);cu.materials.append(M['Letter'])
cap=cyl('BUTTON_06_CAP',.113,.016,'Red',mount,(0,0,.055),n=64)
torus('Button_6_Enamel_Inlay',.102,.0018,'Brass',cap,(0,0,.010))
for a in [-math.pi/4,math.pi/4]:cube('Shutdown_Nickel_Cross',(.022,.139,.008),'Chrome',cap,(0,0,.013),.003,rot=(0,0,a))
# Apply geometry modifiers and consolidate only the new static controls.
new=list(mount.children_recursive)
bpy.ops.object.select_all(action='DESELECT')
for o in new:
 if o.type in ['MESH','CURVE']:o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.object.convert(target='MESH')
cap_children=[o for o in cap.children if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
cap.select_set(True)
for o in cap_children:o.select_set(True)
bpy.context.view_layer.objects.active=cap;bpy.ops.object.join()
fixed=[o for o in mount.children if o.type=='MESH' and o!=cap]
bpy.ops.object.select_all(action='DESELECT')
for o in fixed:o.select_set(True)
bpy.context.view_layer.objects.active=fixed[0];bpy.ops.object.join();fixed[0].name='BUTTON_06_FIXED'
for ob in [cap,fixed[0]]:
 if ob.data.uv_layers:ob.data.uv_layers.active.name='UVMap'
 layer=ob.data.color_attributes.new(name='CavityAO',type='FLOAT_COLOR',domain='CORNER')
 for datum in layer.data:datum.color=(1,1,1,1)
 ob.data.color_attributes.active_color_index=ob.data.color_attributes.find('CavityAO');ob.data.color_attributes.render_color_index=ob.data.color_attributes.find('CavityAO')
home=cap.location.copy()
for f,amount in [(1,0),(585,0),(587,.016),(594,0),(600,0)]:
 cap.location=home-Vector((0,0,amount));cap.keyframe_insert('location',frame=f)
cap.animation_data.action.name='HELIOS_Demo__BUTTON_06_CAP'
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def transform(m):
 p,q,s=(C@m@C.inverted()).decompose();return {'p':list(p),'q':[q.x,q.y,q.z,q.w],'s':list(s)}
S.frame_set(1);bpy.context.view_layer.update()
meta['buttons'].append({'index':6,'mount':mount.name,'cap':cap.name,'home':transform(cap.matrix_local),'function':'quit'})
meta['button_functions']=['wake','bloom','overload','explode','assemble','rotate','quit']
for i,b in enumerate(meta['buttons']):b['home']=transform(bpy.data.objects[b['cap']].matrix_local);b['function']=meta['button_functions'][i]
meta['button_count']=7
(ROOT/'app/assets/mechanism.json').write_text(json.dumps(meta,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
assert abs(bpy.data.objects['TURNTABLE'].rotation_euler.z)<1e-7
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Helios_Incubator.blend'),compress=True)
bpy.data.materials['Solar_Core_Emission'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.8
bpy.ops.object.select_all(action='DESELECT')
for o in COL.objects:o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['HELIOS_ROOT']
bpy.ops.export_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True)
report=json.loads((ROOT/'blender/model_report.json').read_text());report['buttons']=7;report['mesh_objects']=len([o for o in COL.objects if o.type=='MESH']);(ROOT/'blender/model_report.json').write_text(json.dumps(report,indent=2))
(ROOT/'tests/seven_button_geometry.json').write_text(json.dumps({'button_count':7,'shifted_bezel_components':moved,'button_angles':[-144+18*i for i in range(7)],'part_count':meta['part_count'],'controls':len(meta['controls']),'shutdown_keyframes':[585,587,594]},indent=2))
print('SEVEN_BUTTON_ASSET_READY',moved,flush=True)
