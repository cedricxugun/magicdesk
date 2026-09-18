"""Bake real source module transforms into a reusable animation-only GLB."""
import bpy,json,hashlib,struct,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
wide='--wide'in sys.argv
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/service_r63'/('stage03_wide'if wide else 'stage03');ART=ROOT/'app/assets/collection/art/I/service_r63';ART.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61/build.json').read_text());p=json.loads((OUT/'plan.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/s['source'])==p['source_sha256']==s['source_sha256']
assert not p['new_contact_pairs']
assert all(not x['contacts'] for x in p['samples'] if x['time']>0.)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.animation_data:o.animation_data_clear()
    if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:o.data.shape_keys.animation_data_clear()
for row in s['form_panels']:
    o=bpy.data.objects[row['node']];o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
    if 'mechanism'in row:
        m=row['mechanism'];bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];assert all(abs(body.matrix_world[i][j]-Matrix.Identity(4)[i][j])<1e-7 for i in range(4)for j in range(4))
root=bpy.data.objects.new('IS63_MotionRoot',None);scene.collection.objects.link(root);root.parent=body
groups=[x for x in p['groups'] if x['id']in p['active_groups']];markers={};homes={}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def delta(g,t):
    u=max(0,min(1,(t-g['start'])/g['duration']))
    if 'release_offset_blender'in g:
        a=Vector(g['release_offset_blender']);return a*smooth(u/.25) if u<=.25 else a+(Vector(g['offset_blender'])-a)*smooth((u-.25)/.75)
    return Vector(g['offset_blender'])*smooth(u)
fps=60;end=210;scene.render.fps=fps;scene.frame_start=0;scene.frame_end=end
for g in groups:
    marker=bpy.data.objects.new('IS63_'+g['id'],None);scene.collection.objects.link(marker);marker.parent=root;marker.empty_display_type='ARROWS';marker.empty_display_size=.08;markers[g['id']]=marker
    for name in g['roots']:
        target=bpy.data.objects[name];world=target.matrix_world.copy();homes[name]=[list(r)for r in world];target.parent=marker;target.matrix_world=world
    for frame in range(end+1):marker.location=delta(g,frame/fps);marker.keyframe_insert(data_path='location',frame=frame)
scene.frame_set(0);bpy.context.view_layer.update()
source=ROOT/('blender/collection/I_service03_motion_r63b.blend'if wide else 'blender/collection/I_service03_motion_r63.blend');assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
# Read evaluated Blender marker positions. The binary animation is a bake of
# these actual keys, separate from the unchanged body GLB's geometry.
def godot(v):return [float(v.x),float(v.z),-float(v.y)]
positions={g['id']:[]for g in groups};witnesses=[];local=[Vector((0,0,0)),Vector((.01,0,0)),Vector((0,.01,0)),Vector((0,0,.01))]
for frame in range(end+1):
    scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    for key,marker in markers.items():positions[key].append(godot(marker.evaluated_get(dg).location))
    if frame in [0,6,15,33,42,69,99,105,111,123,135,165,195,210]:
        witnesses.append({'time':frame/fps,'points':{name:[godot(bpy.data.objects[name].evaluated_get(dg).matrix_world@v)for v in local]for name in homes}})
binary=bytearray();views=[];accessors=[]
def accessor(rows,width):
    offset=len(binary)
    for row in rows:binary.extend(struct.pack('<'+'f'*width,*row))
    view=len(views);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(binary)-offset})
    index=len(accessors);accessors.append({'bufferView':view,'componentType':5126,'count':len(rows),'type':'SCALAR'if width==1 else 'VEC3','min':[min(r[i]for r in rows)for i in range(width)],'max':[max(r[i]for r in rows)for i in range(width)]});return index
times=accessor([[f/fps]for f in range(end+1)],1);nodes=[{'name':'IS63_MotionRoot','children':list(range(1,len(groups)+1))}];samplers=[];channels=[]
for i,g in enumerate(groups,1):
    nodes.append({'name':'IS63_'+g['id']});output=accessor(positions[g['id']],3);samplers.append({'input':times,'output':output,'interpolation':'LINEAR'});channels.append({'sampler':i-1,'target':{'node':i,'path':'translation'}})
data={'asset':{'version':'2.0','generator':'Blender-evaluated MagicDesk service03 transform bake'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':nodes,'animations':[{'name':'Service03','samplers':samplers,'channels':channels}],'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
j=json.dumps(data,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
asset=ART/('service03_motion_wide.glb'if wide else 'service03_motion.glb');asset.write_bytes(glb)
manifest={'body_source_sha256':s['source_sha256'],'body_component_sha256':s['component_sha256'],'motion_source':str(source.relative_to(ROOT)),'motion_source_sha256':sha(source),'motion_asset':'res://assets/collection/art/I/service_r63/service03_motion.glb','motion_asset_sha256':sha(asset),'clip':'Service03','duration':end/fps,'fps':fps,'groups':[{'id':g['id'],'marker':'IS63_'+g['id'],'roots':g['roots']}for g in groups],'prepared_opening':1.,'local_points':[godot(v)for v in local],'source_witnesses':witnesses,'scope':'Authored/baked stage03 hinge-cap/pin withdrawal and front cover extraction only. Body GLB unchanged. Full service mode, collar unlock, other module releases and final VFX remain pending.'}
manifest['motion_asset']='res://'+str(asset.relative_to(ROOT/'app'))
(ART/('service03_motion_wide.json'if wide else 'service03_motion.json')).write_text(json.dumps(manifest,indent=2)+'\n');(OUT/'motion_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('SERVICE03_BAKED',manifest['motion_source_sha256'],len(glb),flush=True)
