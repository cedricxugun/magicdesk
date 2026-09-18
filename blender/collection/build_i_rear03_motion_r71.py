"""Bake measured rear03 service translations from actual Blender source keys."""
import bpy,json,hashlib,collections,sys,struct,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/rear03_release_r70';OUT.mkdir(parents=True,exist_ok=True)
partial='--partial-bolts'in sys.argv
if partial:OUT=OUT/('two_stage_r5'if '--two-step'in sys.argv else 'route_r4'if '--wide-search'in sys.argv else 'partial_bolts_r3');OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/build.json').read_text());plan=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json').read_text());assert plan['source_sha256']==s['source_sha256'];assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
for row in s['form_panels']:
 o=bpy.data.objects[row['node']];o.animation_data_clear();o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
 if 'mechanism'in row:
  m=row['mechanism']
  for k in ['carriage','rotor']:bpy.data.objects[m[k]].animation_data_clear()
  bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE'];parts=list(dict.fromkeys(o for r in [body,mouth]for o in r.children_recursive if o.type=='MESH'))
orig=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'));base=next(o for o in bpy.data.objects if o not in orig and o.name.split('.')[0]=='BASE_FIXED');base_parts=[o for o in [base,*base.children_recursive]if o.type=='MESH']
offsets={o.name:Vector((0,0,.45))if o.name not in plan['fixed_adapter_names']else Vector()for o in parts}
for row in plan['groups']+plan['legs']+plan['ports']:
 for name in row['names']:offsets[name]+=Vector(row['offset'])
homes={o.name:o.matrix_world.copy()for o in parts}
def depth(o):
 n=0
 while o.parent:n+=1;o=o.parent
 return n
for o in sorted(parts,key=depth):
 pose=homes[o.name].copy();pose.translation+=offsets[o.name];o.matrix_world=pose
bpy.context.view_layer.update()
front=json.loads((ROOT/'review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json').read_text())
front_names=set();front_homes={o.name:o.matrix_world.copy()for o in parts};front_deltas={}
for row in front['groups']:
 if row['id']not in ['cover_03','pin_cap_03','pin_03']:continue
 for name in row['meshes']:front_names.add(name);front_deltas[name]=Vector(row['offset_blender'])
for o in sorted([bpy.data.objects[n]for n in front_names],key=depth):
 pose=front_homes[o.name].copy();pose.translation+=front_deltas[o.name];o.matrix_world=pose
bpy.context.view_layer.update()
front_pose_error=max(abs(o.matrix_world[i][j]-(front_homes[o.name][i][j]+(front_deltas[o.name][i]if j==3 and i<3 else 0.)))for o in [bpy.data.objects[n]for n in front_names]for i in range(4)for j in range(4))
assert front_pose_error<1e-6
def geo(objects):
 v=[];f=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();n=len(v);v.extend(e.matrix_world@x.co for x in m.vertices);f.extend(tuple(n+i for i in t.vertices)for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
 return v,f,owners
OUT=ROOT/'review/I_refinement/nautilus_r1/rear03_motion_r71';OUT.mkdir(parents=True,exist_ok=True);ART=ROOT/'app/assets/collection/art/I/rear03_motion_r71';ART.mkdir(parents=True,exist_ok=True)
plan_path=ROOT/'review/I_refinement/nautilus_r1/rear03_release_r70/two_stage_r5/probe.json';motion_plan=json.loads(plan_path.read_text());assert motion_plan['source_sha256']==s['source_sha256']and motion_plan['two_step_shell'];assert all(not r['contacts']for r in motion_plan['samples'])
bolt_proof=json.loads((plan_path.parent.parent/'partial_bolts_r3/bolt_disengagement.json').read_text());assert bolt_proof['passed']and bolt_proof['source_sha256']==s['source_sha256']
art_manifest=ROOT/'production/I_refinement/nautilus_r1/rear03_release_r70/art_manifest.json';assert art_manifest.exists()
# This source preserves the prepared assembly for authoring only. It is never a
# replacement for the ordinary body source: static hardware is already parked.
for o in bpy.data.objects:
 if o.animation_data:o.animation_data_clear()
 if o.type=='MESH'and o.data.shape_keys and o.data.shape_keys.animation_data:o.data.shape_keys.animation_data_clear()
root=bpy.data.objects.new('IS71_MotionRoot',None);bpy.context.scene.collection.objects.link(root);root.parent=body
markers={};homes={};groups=motion_plan['groups'];normal=Vector(groups[0]['normal']);waypoint=Vector(motion_plan['shell_waypoints'][1]);last=Vector(motion_plan['shell_waypoints'][2])
def smooth(t):
 t=max(0.,min(1.,t));return t*t*t*(10+t*(-15+6*t))
def movement(g,t):
 loosen=smooth((t-.3)/.7);cassette=smooth((t-1.3)/1.2)
 if g['id'].startswith('rear_bolt'):return normal*(.010*loosen+.8*cassette)
 if g['id']=='cassette03':return normal*.8*cassette
 if g['id']=='rear_shell03':return waypoint*smooth((t-2.6)/.6)+(last-waypoint)*smooth((t-3.3)/1.5)
 raise AssertionError(g['id'])
scene=bpy.context.scene;fps=60;end=312;scene.render.fps=fps;scene.frame_start=0;scene.frame_end=end
for g in groups:
 marker=bpy.data.objects.new('IS71_'+g['id'],None);scene.collection.objects.link(marker);marker.parent=root;markers[g['id']]=marker
 for name in g['names']:homes[name]=bpy.data.objects[name].matrix_world.copy()
for g in groups:
 for name in sorted(g['names'],key=lambda n:depth(bpy.data.objects[n])):
  target=bpy.data.objects[name];target.parent=markers[g['id']];target.matrix_world=homes[name]
for g in groups:
 marker=markers[g['id']]
 for frame in range(end+1):marker.location=movement(g,frame/fps);marker.keyframe_insert(data_path='location',frame=frame)
 for curve in marker.animation_data.action.layers[0].strips[0].channelbag(marker.animation_data.action_slot).fcurves:
  for key in curve.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(0);bpy.context.view_layer.update();source=ROOT/'blender/collection/I_rear03_motion_r71.blend';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
def godot(v):return [float(v.x),float(v.z),-float(v.y)]
positions={g['id']:[]for g in groups};witnesses=[];local=[Vector((0,0,0)),Vector((.01,0,0)),Vector((0,.01,0)),Vector((0,0,.01))]
for frame in range(end+1):
 scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 for k,marker in markers.items():positions[k].append(godot(marker.evaluated_get(dg).location))
 if frame in [0,18,30,42,60,78,96,120,150,156,174,192,198,222,252,288,312]:witnesses.append({'time':frame/fps,'points':{name:[godot(bpy.data.objects[name].evaluated_get(dg).matrix_world@p)for p in local]for name in homes}})
binary=bytearray();views=[];accessors=[]
def accessor(rows,width):
 offset=len(binary)
 for row in rows:binary.extend(struct.pack('<'+'f'*width,*row))
 view=len(views);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(binary)-offset});index=len(accessors);accessors.append({'bufferView':view,'componentType':5126,'count':len(rows),'type':'SCALAR'if width==1 else 'VEC3','min':[min(r[i]for r in rows)for i in range(width)],'max':[max(r[i]for r in rows)for i in range(width)]});return index
times=accessor([[f/fps]for f in range(end+1)],1);nodes=[{'name':'IS71_MotionRoot','children':list(range(1,len(groups)+1))}];samplers=[];channels=[]
for i,g in enumerate(groups,1):
 nodes.append({'name':'IS71_'+g['id']});output=accessor(positions[g['id']],3);samplers.append({'input':times,'output':output,'interpolation':'LINEAR'});channels.append({'sampler':i-1,'target':{'node':i,'path':'translation'}})
data={'asset':{'version':'2.0','generator':'Blender evaluated MagicDesk rear03 translation bake'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':nodes,'animations':[{'name':'Rear03Service','samplers':samplers,'channels':channels}],'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors};j=json.dumps(data,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary;asset=ART/'rear03_motion.glb';asset.write_bytes(glb);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'body_source_sha256':s['source_sha256'],'body_component_sha256':s['component_sha256'],'motion_source':str(source.relative_to(ROOT)),'motion_source_sha256':sha(source),'motion_asset':'res://'+str(asset.relative_to(ROOT/'app')),'motion_asset_sha256':sha(asset),'clip':'Rear03Service','duration':end/fps,'fps':fps,'groups':[{'id':g['id'],'marker':'IS71_'+g['id'],'roots':g['names']}for g in groups],'prepared_opening':1.,'local_points':[godot(v)for v in local],'source_witnesses':witnesses,'preparation_support_plan':'review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json','preparation_front_plan':'review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json','art_manifest':str(art_manifest.relative_to(ROOT)),'scope':'Authored Blender translation stage after already-parked supports/front cover. Four motion tracks drive 36 actual mesh members. Fine threaded screw rotation, combined complete service and final VFX remain unfinished.'}
(ART/'rear03_motion.json').write_text(json.dumps(manifest,indent=2)+'\n');(OUT/'motion_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('REAR03_MOTION_BAKED',manifest['motion_source_sha256'],len(glb))
