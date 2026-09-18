"""Bake the exact runtime take into a new editable source, guarded by hashes."""
import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
sys.path.insert(0,str(Path(__file__).parent))
revision='r3' if '--r3' in sys.argv else 'r2'
review=ROOT/('review/G_optical_curator/ship_'+revision+'/full_take')
take=json.loads((review/'curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator_ship_candidate.{ext}').read_bytes()).hexdigest()==take[key],'Stale take'
data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator_ship_candidate.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_ship_runtime_candidate.blend'))
scene=bpy.context.scene;scene.render.fps=30;scene.frame_end=take['samples'][-1]['frame'];scene.timeline_markers.clear()
for obj in bpy.data.objects:obj.animation_data_clear()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def key(obj,frame):
    for prop in ['location','rotation_quaternion','scale']:obj.keyframe_insert(prop,frame=frame)
previous={};last_key={}
widgets={}
for kind in ['rotary','slider_x','hold','detent','service']:
    root=bpy.data.objects['GCTRL_'+kind]
    widgets[kind.replace('_x','')]=(root,{obj.name.replace('.','_'):obj for obj in root.children})
console_lamps={}
for label in ['Read','Print','Play','Spin','Stop']:
    root=bpy.data.objects.get('ConsoleLamp'+label)
    if root:
        for child in root.children:
            if child.type=='MESH' and child.data.materials:
                material=child.data.materials[0].copy();child.data.materials[0]=material
                console_lamps[label]=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Emission Strength']
def animate(obj,p,frame):
    if p==previous.get(obj.name):return
    obj.rotation_mode='QUATERNION'
    if obj.name in previous and last_key[obj.name]<frame-1:obj.matrix_basis=pose(previous[obj.name]);key(obj,frame-1)
    obj.matrix_basis=pose(p);key(obj,frame);previous[obj.name]=p;last_key[obj.name]=frame
print_root=bpy.data.objects[data['record_player']['print_root']]
roots=[bpy.data.objects[item['root']] for item in data['g_archive']['contents']]
progress_values=[]
face_values={}
def mathnode(nodes,links,operation,*args):
    node=nodes.new('ShaderNodeMath');node.operation=operation
    for i,arg in enumerate(args):
        if isinstance(arg,(float,int)):node.inputs[i].default_value=arg
        else:links.new(arg,node.inputs[i])
    return node.outputs[0]
screen=bpy.data.objects[data['optical_curator']['screen']]
material=bpy.data.materials.new('GA_RecordedExpressions');material.use_nodes=True
nodes=material.node_tree.nodes;links=material.node_tree.links;p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.004,.005,.006,1);p.inputs['Metallic'].default_value=.08;p.inputs['Roughness'].default_value=.23;p.inputs['Coat Weight'].default_value=.4
optical=json.loads((ROOT/'app/assets/collection/lighting_profiles.json').read_text())['profiles']['G']['optical']
p.inputs['Specular IOR Level'].default_value=optical['specular'];p.inputs['Roughness'].default_value=optical['roughness'];p.inputs['Coat Weight'].default_value=optical['coat']
uv=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],sep.inputs[0])
texture=bpy.data.images.load(str(ROOT/'app/assets/collection/art/G_AI/expressions.png'),check_existing=True)
images=[]
for label in ['current','previous']:
    col=nodes.new('ShaderNodeValue');row=nodes.new('ShaderNodeValue');face_values[label]=(col.outputs[0],row.outputs[0])
    vector=nodes.new('ShaderNodeCombineXYZ')
    u=mathnode(nodes,links,'ADD',mathnode(nodes,links,'MULTIPLY',sep.outputs['X'],.3125),col.outputs[0])
    v=mathnode(nodes,links,'ADD',mathnode(nodes,links,'MULTIPLY',mathnode(nodes,links,'SUBTRACT',1.,sep.outputs['Y']),.625),row.outputs[0])
    links.new(u,vector.inputs['X']);links.new(v,vector.inputs['Y'])
    tex=nodes.new('ShaderNodeTexImage');tex.image=texture;tex.extension='CLIP';links.new(vector.outputs[0],tex.inputs['Vector']);images.append(tex)
mix=nodes.new('ShaderNodeMixRGB');links.new(images[1].outputs['Color'],mix.inputs[1]);links.new(images[0].outputs['Color'],mix.inputs[2]);face_values['blend']=mix.inputs[0]
tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1.;tint.inputs[2].default_value=(1.,.46,.08,1.);links.new(mix.outputs[0],tint.inputs[1]);links.new(tint.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=2.1
face_values['brightness']=p.inputs['Emission Strength'];screen.data.materials.clear();screen.data.materials.append(material)
from butterfly_source_formation import prepare
progress_values,gain_values=prepare(roots,print_root,take,skip_indices=(2,))
from ship_source_formation import prepare as prepare_ship
progress_values[2],gain_values[2]=prepare_ship(roots[2],data["g_archive"]["contents"][2]["ship"])
for item in data["g_archive"]["contents"][2]["ship"]["sheets"]+data["g_archive"]["contents"][2]["ship"].get("springs",[]):bpy.data.objects[item["node"]].data.animation_data_clear()
rope_point_keys=0
curve_previous={};curve_last_frame={}
last_stage=''
for sample in take['samples']:
    frame=sample['frame'];state=sample['state'];stage=str(state['selected']+1)+'_'+state['stage']
    if stage!=last_stage:scene.timeline_markers.new(stage,frame=frame);last_stage=stage
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:animate(obj,p,frame)
    for name,rope in {**sample.get('ship_ropes',{}),**sample.get('ship_springs',{})}.items():
        obj=bpy.data.objects[name];animate(obj,rope['pose'],frame)
        points=obj.data.splines[0].points
        assert len(points)==len(rope['points'])
        coords_now=rope['points']
        if coords_now==curve_previous.get(name):continue
        if name in curve_previous and curve_last_frame[name]<frame-1:
            for point,coords in zip(points,curve_previous[name]):
                point.co=(coords[0],-coords[2],coords[1],1.0);point.keyframe_insert('co',frame=frame-1);rope_point_keys+=1
        for point,coords in zip(points,coords_now):
            point.co=(coords[0],-coords[2],coords[1],1.0);point.keyframe_insert('co',frame=frame);rope_point_keys+=1
        curve_previous[name]=coords_now;curve_last_frame[name]=frame
    for widget in sample['widgets']:
        root,children=widgets[widget['gesture']];animate(root,widget['pose'],frame)
        assert len(widget['moving_names'])==len(widget['moving'])
        for name,p in zip(widget['moving_names'],widget['moving']):
            assert name in children,'Unknown physical controller part: '+name
            animate(children[name],p,frame)
    for name,value in sample.get('console_lamps',{}).items():
        if name in console_lamps:
            console_lamps[name].default_value=.025+value*1.65;console_lamps[name].keyframe_insert('default_value',frame=frame)
    for label,state_key in [('current','expression'),('previous','expression_previous')]:
        index=state.get(state_key,0);col,row=face_values[label];col.default_value=(index%4)*.25-.03125;row.default_value=(1-index//4)*.5-.0625
        col.keyframe_insert('default_value',frame=frame);row.keyframe_insert('default_value',frame=frame)
    face_values['blend'].default_value=state.get('expression_blend',1.);face_values['blend'].keyframe_insert('default_value',frame=frame)
    face_values['brightness'].default_value=sample['power']*2.1;face_values['brightness'].keyframe_insert('default_value',frame=frame)
    for index,root in enumerate(roots):
        shown=index==state['loaded_index'] and state['owners'][index]=='platter' and state['print_amount']>.0001
        for obj in [root]+list(root.children_recursive):
            if obj.hide_render==shown or frame==1:
                obj.hide_render=not shown;obj.hide_viewport=not shown;obj.keyframe_insert('hide_render',frame=frame);obj.keyframe_insert('hide_viewport',frame=frame)
        physical=state['physical_print_progress']
        for socket in progress_values[index]:socket.default_value=physical if shown else 0.;socket.keyframe_insert('default_value',frame=frame)
        gain=sample['power']*(1-sample['explosion'])*(.45+math.exp(-((state['print_amount']-.77)/.16)**2)*1.8) if shown and state['print_amount']<.9999 else 0.
        if index==2:gain=sample['power']*(1-sample['explosion']) if shown and state['print_amount']<.9999 else 0.
        for socket in gain_values[index]:socket.default_value=gain;socket.keyframe_insert('default_value',frame=frame)
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:point.interpolation='CONSTANT' if curve.data_path in ['hide_render','hide_viewport'] else 'LINEAR'
scene['motion_source']='curator_take.json: six original records, AI face, real iris, independent projector, all return paths, dismantle and assemble'
scene['effect_bake_scope']='Mechanical/face/console, G1 sealing, G2 deformed winch ropes and hull/cloth formation fields included. Runtime light strands, glints, particles, tide rim pulse and dynamic text remain runtime layers; no pixel-identical GPU VFX parity.'
scene['status']='Candidate mechanical/face/console animation and panel sealing baked; GPU light layers remain runtime';scene.frame_set(1);bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/G_ship_runtime_candidate.blend'))
report={'frames':scene.frame_end,'fps':30,'animated_objects':len(previous),'material_formation':True,'butterfly_panel_seal':True,'ship_panel_weave':True,'ship_rope_point_keys':rope_point_keys,'main_source_overwritten':False,'gpu_light_layers_baked':False,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256']}
(review/'blender_bake.json').write_text(json.dumps(report,indent=2));print('SHIP_CURATOR_BAKED',json.dumps(report),flush=True)
