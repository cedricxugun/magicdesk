"""Bake only the replacement component; preserve the other verified actions."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
stem=ROOT/'app/assets/collection/models/G_optical_curator_observatory_candidate'
data=json.loads(stem.with_suffix('.json').read_text());entry=data['g_archive']['contents'][0]
take=json.loads((ROOT/'review/G_optical_curator/observatory_r2/app/curator_take.json').read_text())
original=json.loads((ROOT/'review/G_optical_curator/curator_take.json').read_text())
old_data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256(stem.with_suffix('.'+ext).read_bytes()).hexdigest()==take[key],'Stale candidate take'
assert len(take['samples'])==len(original['samples']),'Full candidate take required'
ignored={entry['root'],old_data['g_archive']['contents'][0]['root']}
ignored.update(r['name'] for r in entry['rig']);ignored.update(r['name'] for r in old_data['g_archive']['contents'][0]['rig'])
for old,new in zip(original['samples'],take['samples']):
    assert old['frame']==new['frame'] and old['state']==new['state'],'Non-component state changed'
    assert {k:v for k,v in old['poses'].items() if k not in ignored}=={k:v for k,v in new['poses'].items() if k not in ignored},'Other mechanism poses changed'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/data['source_blend']))
scene=bpy.context.scene;assert scene.frame_end==take['samples'][-1]['frame']
root=bpy.data.objects[entry['root']];print_root=bpy.data.objects[data['record_player']['print_root']]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
nodes={name:bpy.data.objects[name] for name in [entry['root']]+[r['name'] for r in entry['rig']]}
for obj in nodes.values():obj.animation_data_clear()
all_objects=[root]+list(root.children_recursive)
for obj in all_objects:obj.hide_set(False)
materials={};processed=set();progress_sockets=[];height=take['heights'][0]
def mathnode(nt,operation,*args):
    node=nt.nodes.new('ShaderNodeMath');node.operation=operation
    for i,arg in enumerate(args):
        if isinstance(arg,(float,int)):node.inputs[i].default_value=arg
        else:nt.links.new(arg,node.inputs[i])
    return node.outputs[0]
for obj in all_objects:
    if obj.type not in ['MESH','CURVE','FONT']:continue
    for slot in obj.material_slots:
        source=slot.material
        if not source or not source.use_nodes:continue
        if source.as_pointer() in processed:continue
        if source.name in materials:slot.material=materials[source.name];continue
        # The independent geometry source has unbaked material templates.
        assert not source.name.startswith('GO2_Recorded_'),'Prepare a fresh candidate before rebaking the component'
        mat=source.copy();mat.name='GO2_Recorded_'+source.name;materials[source.name]=mat;slot.material=mat
        processed.add(mat.as_pointer())
        nt=mat.node_tree;principled=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
        coord=nt.nodes.new('ShaderNodeTexCoord');coord.object=print_root;sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(coord.outputs['Object'],sep.inputs[0])
        value=nt.nodes.new('ShaderNodeValue');value.name='RecordedFormation';progress_sockets.append(value.outputs[0])
        front=mathnode(nt,'MULTIPLY',mathnode(nt,'ADD',value.outputs[0],.035 if principled.inputs['Metallic'].default_value>.8 else 0),height)
        nt.links.new(mathnode(nt,'LESS_THAN',sep.outputs['Z'],front),principled.inputs['Alpha'])
        distance=mathnode(nt,'ABSOLUTE',mathnode(nt,'SUBTRACT',sep.outputs['Z'],mathnode(nt,'MULTIPLY',value.outputs[0],height)))
        edge=mathnode(nt,'MAXIMUM',0,mathnode(nt,'SUBTRACT',1,mathnode(nt,'DIVIDE',distance,.018)))
        strength=mathnode(nt,'MULTIPLY',mathnode(nt,'MULTIPLY',edge,6),mathnode(nt,'LESS_THAN',value.outputs[0],.9999))
        principled.inputs['Emission Color'].default_value=(1,.69,.33,1);nt.links.new(strength,principled.inputs['Emission Strength'])
previous={};last_frame={}
def key(obj,frame):
    for name in ['location','rotation_quaternion','scale']:obj.keyframe_insert(name,frame=frame)
for sample in take['samples']:
    frame=sample['frame'];state=sample['state']
    for name,obj in nodes.items():
        value=sample['poses'][name]
        if previous.get(name)==value:continue
        obj.rotation_mode='QUATERNION'
        if name in previous and last_frame[name]<frame-1:obj.matrix_basis=pose(previous[name]);key(obj,frame-1)
        obj.matrix_basis=pose(value);key(obj,frame);previous[name]=value;last_frame[name]=frame
    shown=state['loaded_index']==0 and state['owners'][0]=='platter' and state['print_amount']>.0001
    for obj in all_objects:
        if obj.hide_render==shown or frame==1:
            obj.hide_render=not shown;obj.hide_viewport=not shown;obj.keyframe_insert('hide_render',frame=frame);obj.keyframe_insert('hide_viewport',frame=frame)
    for socket in progress_sockets:socket.default_value=state['physical_print_progress'] if shown else 0.;socket.keyframe_insert('default_value',frame=frame)
for obj in all_objects:
    if not obj.animation_data or not obj.animation_data.action:continue
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:point.interpolation='CONSTANT' if curve.data_path in ['hide_render','hide_viewport'] else 'LINEAR'
scene['observatory_integration_state']='Replacement component and formation baked from full candidate runtime; other actions proven unchanged'
scene.frame_set(1);bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/data['source_blend']))
maximum=0.;checked=0
for sample in take['samples'][::93]+[take['samples'][-1]]:
    scene.frame_set(sample['frame'])
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name);assert obj,'Missing source object '+name
        expected=pose(p);maximum=max(maximum,max(abs(expected[i][j]-obj.matrix_basis[i][j]) for i in range(4) for j in range(4)));checked+=1
report={'passed':maximum<.00001,'frames':scene.frame_end,'new_rig_objects':len(nodes),'checked_transforms':checked,'max_matrix_error':maximum,'other_runtime_motion_unchanged':True,'gpu_vfx_baked':False,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256']}
(ROOT/'review/G_optical_curator/observatory_r2/source_animation_report.json').write_text(json.dumps(report,indent=2)+'\n');print('OBSERVATORY_CANDIDATE_BAKED',json.dumps(report),flush=True)
assert report['passed'],'Candidate source animation diverged'
