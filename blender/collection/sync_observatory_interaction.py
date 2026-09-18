"""Update only observatory motion and console cue curves from the actual take."""
import bpy,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
take=json.loads((ROOT/'review/G_optical_curator/curator_take.json').read_text());data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator.json').read_text())
before=json.loads((ROOT/'review/G_optical_curator/observatory_interaction/non_observatory_before.json').read_text())
frames=[{k:v for k,v in s['poses'].items() if k not in before['ignored']} for s in take['samples']]
assert hashlib.sha256(json.dumps(frames,sort_keys=True,separators=(',',':')).encode()).hexdigest()==before['sha256'],'Unrelated motion changed'
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator.{ext}').read_bytes()).hexdigest()==take[key]
source=ROOT/'blender/collection/G_optical_curator.blend';backup=ROOT/'blender/collection/checkpoints'/('before-observatory-interaction-'+hashlib.sha256(source.read_bytes()).hexdigest()[:12]+'.blend');backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
nodes={r['name']:bpy.data.objects[r['name']] for r in data['g_archive']['contents'][0]['rig']}
visibility={}
for name,obj in nodes.items():
    # Preserve the existing visibility schedule while replacing pose curves.
    visibility[name]=[]
    for sample in take['samples']:
        state=sample['state'];visibility[name].append(state['loaded_index']==0 and state['owners'][0]=='platter' and state['print_amount']>.0001)
    obj.animation_data_clear();obj.rotation_mode='QUATERNION'
lamps={}
for label in ['Read','Print','Play','Spin','Stop']:
    root=bpy.data.objects.get('ConsoleLamp'+label)
    if root:
        for child in root.children:
            if child.type=='MESH' and child.data.materials:lamps[label]=next(n for n in child.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Emission Strength']
previous={};last={}
def key(obj,frame):
    for p in ['location','rotation_quaternion','scale']:obj.keyframe_insert(p,frame=frame)
for index,sample in enumerate(take['samples']):
    frame=sample['frame']
    for name,obj in nodes.items():
        value=sample['poses'][name]
        if previous.get(name)!=value:
            if name in previous and last[name]<frame-1:obj.matrix_basis=pose(previous[name]);key(obj,frame-1)
            obj.matrix_basis=pose(value);key(obj,frame);previous[name]=value;last[name]=frame
        shown=visibility[name][index]
        if index==0 or visibility[name][index-1]!=shown:
            obj.hide_render=not shown;obj.hide_viewport=not shown;obj.keyframe_insert('hide_render',frame=frame);obj.keyframe_insert('hide_viewport',frame=frame)
    for name,value in sample.get('console_lamps',{}).items():
        if name in lamps:lamps[name].default_value=.025+value*1.65;lamps[name].keyframe_insert('default_value',frame=frame)
for obj in nodes.values():
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for p in curve.keyframe_points:p.interpolation='CONSTANT' if curve.data_path in ['hide_render','hide_viewport'] else 'LINEAR'
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(source))
report={'frames':len(take['samples']),'rig_nodes_updated':len(nodes),'other_motion_unchanged':True,'console_cues_updated':True,'gpu_interaction_cues_baked':False,'interaction_profile_sha256':hashlib.sha256((ROOT/'app/assets/collection/observatory_interaction.json').read_bytes()).hexdigest(),'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256'],'backup':str(backup.relative_to(ROOT))}
(ROOT/'review/G_optical_curator/observatory_interaction/source_sync.json').write_text(json.dumps(report,indent=2)+'\n');print('OBSERVATORY_INTERACTION_SOURCE',json.dumps(report),flush=True)
