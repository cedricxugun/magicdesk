"""Translate the unchanged full-size high valve and supply into the clear seam corridor.
Only this part's source location keys, metadata home, and GLB node translation change.
"""
import bpy,json,struct,pathlib,hashlib
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;frame=S.frame_current
name='P_Thermal_Valve_0';ob=bpy.data.objects[name]
if ob.get('high_valve_corridor_revision')==1:raise RuntimeError('Already relocated; refuse double translation')
delta=Vector((.26,-.10,0));gd=[.26,0.0,.10]
path=ROOT/'app/assets/helios_model.glb';raw=path.read_bytes();header=raw[:12];chunks=[];offset=12
while offset<len(raw):
 length,kind=struct.unpack_from('<II',raw,offset);offset+=8;chunks.append((kind,raw[offset:offset+length]));offset+=length
g=json.loads(next(data for kind,data in chunks if kind==0x4E4F534A))
node=next(n for n in g['nodes']if n.get('name')==name)
assert 'matrix' not in node,'Unexpected matrix node transform'
translation=node.get('translation',[0,0,0]);node['translation']=[translation[i]+gd[i]for i in range(3)]
meta_path=ROOT/'app/assets/mechanism.json';meta=json.loads(meta_path.read_text(encoding='utf8'));part=next(p for p in meta['parts']if p['name']==name)
part['home']['p']=[part['home']['p'][i]+gd[i]for i in range(3)]
meta['high_valve_mount']={'part':name,'translation_from_original':gd,'frame_world':[1.15,2.02,0],'steam_source_world':[1.15,2.62,0],'electrical_contact_local':[0,.59,0]}
# Offset all existing location samples in place, preserving rotation, timing,
# curve interpolation, and both handles. Nothing else in the source is retimed.
changed=0
if ob.animation_data and ob.animation_data.action:
 for layer in ob.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     if curve.data_path!='location':continue
     shift=delta[curve.array_index]
     for key in curve.keyframe_points:
      key.co.y+=shift;key.handle_left.y+=shift;key.handle_right.y+=shift;changed+=1
     curve.update()
ob['high_valve_corridor_revision']=1
S.frame_set(frame)
if not changed:ob.location+=delta
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Helios_Incubator.blend'),compress=True)
payload=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode('utf8');payload+=b' '*((-len(payload))%4)
rebuilt=b''
for kind,data in chunks:
 if kind==0x4E4F534A:data=payload
 rebuilt+=struct.pack('<II',len(data),kind)+data
path.write_bytes(struct.pack('<III',0x46546C67,2,12+len(rebuilt))+rebuilt)
meta_path.write_text(json.dumps(meta,ensure_ascii=False,separators=(',',':')),encoding='utf8')
old_bin=[data for kind,data in chunks if kind==0x004E4942]
report={'part':name,'delta_blender':list(delta),'delta_godot':gd,'source_location_keys_updated':changed,'only_glb_node_translation_changed':True,'geometry_bin_sha256':hashlib.sha256(old_bin[0]).hexdigest(),'part_count':meta['part_count'],'button_count':len(meta['buttons']),'porcelain_radius_unchanged':.09,'steam_source_godot':[1.15,2.62,0]}
(ROOT/'tests/high_valve_relocation.json').write_text(json.dumps(report,indent=2));print('HIGH_VALVE_RELOCATED',json.dumps(report),flush=True)
