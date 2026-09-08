"""Authorized material-only sync. Validate baseline, save packed main blend, export static home GLB."""
import bpy,pathlib,json,hashlib,array,struct,importlib.util,datetime,os
from mathutils import Matrix,Vector,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];MAIN=ROOT/'blender'/'Helios_Incubator.blend';GLB=ROOT/'app'/'assets'/'helios_model.glb';META=ROOT/'app'/'assets'/'mechanism.json';REV=ROOT/'review';REPORT=REV/'ceramic_sync_validation.json'
def sha_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()
metadata_hash=sha_file(META);meta=json.loads(META.read_text(encoding='utf-8'));source_hash=sha_file(MAIN)
bpy.ops.wm.open_mainfile(filepath=str(MAIN));S=bpy.context.scene;original_frame=S.frame_current;S.frame_set(1);bpy.context.view_layer.update();COL=bpy.data.collections['HELIOS_ASSET'];C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def arrhash(seq,prop,n):
 a=array.array('f',[0.])*n;seq.foreach_get(prop,a);return hashlib.sha256(a.tobytes()).hexdigest()
def actions():
 data=[]
 for a in sorted(bpy.data.actions,key=lambda a:a.name):
  curves=[]
  for lay in a.layers:
   for st in lay.strips:
    for bag in st.channelbags:
     for fc in bag.fcurves:curves.append([fc.data_path,fc.array_index,[[list(k.co),k.interpolation,list(k.handle_left),list(k.handle_right)] for k in fc.keyframe_points]])
  data.append([a.name,curves])
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def camera():
 o=S.camera;return {'name':o.name,'matrix':[list(x) for x in o.matrix_world],'type':o.data.type,'lens':o.data.lens,'sensor_fit':o.data.sensor_fit,'sensor_width':o.data.sensor_width,'sensor_height':o.data.sensor_height,'resolution':[S.render.resolution_x,S.render.resolution_y,S.render.resolution_percentage]}
def materials_other():
 data={}
 for m in bpy.data.materials:
  if m.name=='Ivory_Enamel':continue
  nodes=[]
  if m.use_nodes:
   for n in m.node_tree.nodes:
    vals=[]
    for sock in n.inputs:
     if hasattr(sock,'default_value'):
      v=sock.default_value
      try:v=list(v)
      except TypeError:pass
      vals.append([sock.name,v])
    nodes.append([n.name,n.bl_idname,vals,n.image.name if n.type=='TEX_IMAGE' and n.image else None])
  data[m.name]=nodes
 return data
def geometry():
 out={}
 for o in COL.objects:
  if o.type!='MESH':continue
  me=o.data;attrs={}
  for c in me.color_attributes:attrs[c.name]={'domain':c.domain,'type':c.data_type,'count':len(c.data),'hash':arrhash(c.data,'color',len(c.data)*4)}
  out[o.name]={'verts':len(me.vertices),'loops':len(me.loops),'polygons':len(me.polygons),'positions':arrhash(me.vertices,'co',len(me.vertices)*3),'uv':{u.name:arrhash(u.data,'uv',len(u.data)*2) for u in me.uv_layers},'color_attributes':attrs,'active_color':me.color_attributes.active_color.name if me.color_attributes.active_color else None,'materials':[m.name if m else None for m in me.materials]}
 return out
def objects():return {o.name:{'parent':o.parent.name if o.parent else None,'matrix_local':[list(r) for r in o.matrix_local],'type':o.type} for o in COL.objects}
assert len(meta['buttons'])==meta['button_count']==7
assert len(meta['parts'])==meta['part_count']==70
assert len([o for o in COL.objects if o.name.startswith('BUTTON_') and o.name.endswith('_CAP')])==7
assert abs(bpy.data.objects[meta['turntable']].rotation_euler.z)<1.e-7,'Source frame1 turn is not zero'
for b in meta['buttons']:
 assert b['mount'] in bpy.data.objects and b['cap'] in bpy.data.objects
for p in meta['parts']:
 assert p['name'] in bpy.data.objects
 o=bpy.data.objects[p['name']];actual=C@o.matrix_local@C.inverted();h=p['home'];q=h['q'];expected=Matrix.LocRotScale(Vector(h['p']),Quaternion((q[3],q[0],q[1],q[2])),Vector(h['s']))
 assert max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4))<2.e-5,'Home transform mismatch '+p['name']
baseline={'camera':camera(),'actions':actions(),'geometry':geometry(),'objects':objects(),'other_materials':materials_other()}
print('CERAMIC_SYNC_BASELINE_VERIFIED',len(meta['buttons']),len(meta['parts']),flush=True)
spec=importlib.util.spec_from_file_location('ceramic_material_update',ROOT/'blender'/'ceramic_material_update.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);mat=module.apply_ceramic_material()
packed=[]
for n in mat.node_tree.nodes:
 if n.type=='TEX_IMAGE' and n.image:n.image.pack();packed.append(n.image.name)
assert len(packed)==3
assert camera()==baseline['camera'];assert actions()==baseline['actions'];assert geometry()==baseline['geometry'];assert objects()==baseline['objects'];assert materials_other()==baseline['other_materials']
assert sha_file(META)==metadata_hash and sha_file(MAIN)==source_hash,'External asset changed during sync'
S.frame_set(original_frame);bpy.ops.wm.save_as_mainfile(filepath=str(MAIN),compress=True)
# Reopen the saved native source to validate the actual persisted data.
bpy.ops.wm.open_mainfile(filepath=str(MAIN));S=bpy.context.scene;S.frame_set(1);COL=bpy.data.collections['HELIOS_ASSET'];bpy.context.view_layer.update()
assert camera()==baseline['camera'];assert actions()==baseline['actions'];assert geometry()==baseline['geometry'];assert objects()==baseline['objects'];assert materials_other()==baseline['other_materials'];assert sha_file(META)==metadata_hash
mat=bpy.data.materials['Ivory_Enamel'];assert all(n.image.packed_file for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
assert abs(bpy.data.objects[meta['turntable']].rotation_euler.z)<1.e-7
# Emission is intentionally .8 for the runtime asset only; native animated source remains unchanged.
core_tree=bpy.data.materials['Solar_Core_Emission'].node_tree
# Exporter reevaluates frame 1; temporarily detach the node-tree action so its .05 key
# cannot override the authorized .8 runtime reference. Never save this export-only state.
if core_tree.animation_data:core_tree.animation_data.action=None
core=core_tree.nodes.get('Principled BSDF');core.inputs['Emission Strength'].default_value=.8
bpy.ops.object.select_all(action='DESELECT')
for o in COL.objects:o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects[meta['root']]
candidate=REV/'ceramic_refine_model_candidate.glb'
bpy.ops.export_scene.gltf(filepath=str(candidate),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True)
def glb_read(path):
 data=path.read_bytes();jlen,jtyp=struct.unpack_from('<II',data,12);j=json.loads(data[20:20+jlen]);pos=20+jlen;blen,btyp=struct.unpack_from('<II',data,pos);return j,data[pos+8:pos+8+blen]
def accessor_bytes(j,buf,index):
 a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};types={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};width=sizes[a['componentType']]*types[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width)
 return b''.join(buf[start+i*stride:start+i*stride+width] for i in range(a['count']))
def glb_geometry(j,buf):
 result={}
 for node in j['nodes']:
  if 'mesh' not in node:continue
  mesh=j['meshes'][node['mesh']];prims=[]
  for p in mesh['primitives']:
   attrs={k:hashlib.sha256(accessor_bytes(j,buf,v)).hexdigest() for k,v in p['attributes'].items()}
   if 'indices' in p:attrs['indices']=hashlib.sha256(accessor_bytes(j,buf,p['indices'])).hexdigest()
   prims.append(attrs)
  result[node['name']]=prims
 return result
oldj,oldbin=glb_read(GLB);newj,newbin=glb_read(candidate)
assert glb_geometry(oldj,oldbin)==glb_geometry(newj,newbin),'GLB geometry, UV, normals or vertex AO changed'
old_nodes={n['name']:{k:v for k,v in n.items() if k in ['translation','rotation','scale','matrix','extras']} for n in oldj['nodes']}
new_nodes={n['name']:{k:v for k,v in n.items() if k in ['translation','rotation','scale','matrix','extras']} for n in newj['nodes']}
assert old_nodes==new_nodes,'GLB node home data changed'
newnames={n['name'] for n in newj['nodes']};assert all(p['name'] in newnames for p in meta['parts']);assert all(b['cap'] in newnames and b['mount'] in newnames for b in meta['buttons'])
ivory=next(m for m in newj['materials'] if m['name']=='Ivory_Enamel');assert ivory['pbrMetallicRoughness'].get('metallicFactor',1)==0
assert ivory['normalTexture'].get('scale',1)==.2 or abs(ivory['normalTexture'].get('scale',1)-.2)<1.e-6
export_core=next(m for m in newj['materials'] if m['name']=='Solar_Core_Emission');es=export_core.get('extensions',{}).get('KHR_materials_emissive_strength',{}).get('emissiveStrength',1.)
assert abs(export_core['emissiveFactor'][0]*es-.8)<1.e-6,'Runtime core emission not .8'
assert sha_file(META)==metadata_hash
candidate.replace(GLB)
report={'passed':True,'synced_at_local':datetime.datetime.now().astimezone().isoformat(),'main_blend':str(MAIN),'main_blend_size':MAIN.stat().st_size,'glb':str(GLB),'glb_size':GLB.stat().st_size,'metadata_sha256_unchanged':metadata_hash,'button_count':7,'independent_parts':70,'part_homes_unchanged':True,'native_animation_sha256_unchanged':baseline['actions'],'main_camera_unchanged':baseline['camera'],'mesh_uv_normals_vertex_AO_exactly_unchanged':True,'other_native_materials_unchanged':True,'packed_ceramic_images':packed,'export_frame':1,'export_turntable_rotation_z':0.,'runtime_core_emission':.8,'exported_ceramic_material':ivory,'exported_color_0_primitives':sum('COLOR_0' in p['attributes'] for m in newj['meshes'] for p in m['primitives'])}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('CERAMIC_MAIN_AND_GLB_SYNCED',json.dumps({'blend_bytes':MAIN.stat().st_size,'glb_bytes':GLB.stat().st_size,'time':report['synced_at_local']}),flush=True)
