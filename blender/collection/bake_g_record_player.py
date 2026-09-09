"""Bake actual same-disc runtime motion and physical controls into Blender.

The print boundary follows the real platter; objects retain unit scale.
The two input hashes must match before any source file is written.
"""
import bpy,json,pathlib,math,sys,hashlib
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
take=json.loads((ROOT/'review/G_record_player/record_take.json').read_text(encoding='utf-8'))
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:
    assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_record_player.{ext}').read_bytes()).hexdigest()==take[key],f'Stale {ext} take'
data=json.loads((ROOT/'app/assets/collection/models/G_record_player.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_record_player.blend'))
scene=bpy.context.scene;scene.name='G_Record_Player';scene.frame_set(1);scene.render.fps=30;scene.frame_end=take['samples'][-1]['frame'];scene.timeline_markers.clear()
for col in list(bpy.data.collections):
    if col.name.startswith('GR_CAPTURED_OPTICS'):
        for name in [o.name for o in col.all_objects]:
            obj=bpy.data.objects.get(name)
            if obj:bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(col)
# Replace only generated preview widgets, retaining source mechanism and base.
names=set()
for obj in bpy.data.objects:
    if obj.name.startswith(('CTRL_','GCTRL_')):names.add(obj.name);names.update(c.name for c in obj.children_recursive)
for name in names:
    obj=bpy.data.objects.get(name)
    if obj:bpy.data.objects.remove(obj,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/record_controls.glb'));added=set(bpy.data.objects)-before
widgets={}
for kind in ['rotary','slider_x','hold','detent','service']:
    obj=next(o for o in added if o.name=='GCTRL_'+kind);obj.parent=None
    children=[o for o in obj.children if 'WidgetSocket' not in o.name and 'WidgetRim' not in o.name]
    widgets[kind.replace('_x','')]=(obj,children)
    for o in [obj]+list(obj.children_recursive):added.discard(o)
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
for name in take['samples'][0]['poses']:
    obj=bpy.data.objects.get(name)
    if obj:obj.animation_data_clear()
col=bpy.data.collections.new('GR_CAPTURED_OPTICS');scene.collection.children.link(col)
atlas=bpy.data.images.load(str(ROOT/'app/assets/collection/art/G/optical_atlas.png'),check_existing=True)
def mathnode(nodes,links,op,*values):
    n=nodes.new('ShaderNodeMath');n.operation=op
    for i,value in enumerate(values):
        if isinstance(value,(int,float)):n.inputs[i].default_value=value
        else:links.new(value,n.inputs[i])
    return n.outputs[0]
def plane(name,tile):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
    uv=mesh.uv_layers.new();coords=[(0,0),(1,0),(1,1),(0,1)]
    for loop in mesh.loops:
        u,v=coords[loop.vertex_index];uv.data[loop.index].uv=((tile%2+u)*.5,(1-tile//2+v)*.5)
    m=bpy.data.materials.new(name+'_Atlas');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage');tex.image=atlas;info=n.new('ShaderNodeObjectInfo');value=n.new('ShaderNodeRGBToBW');lum=n.new('ShaderNodeRGBToBW');l.new(info.outputs['Color'],value.inputs[0]);l.new(tex.outputs['Color'],lum.inputs[0])
    l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(tex.outputs['Color'],p.inputs['Emission Color']);l.new(mathnode(n,l,'MULTIPLY',value.outputs[0],5),p.inputs['Emission Strength']);l.new(mathnode(n,l,'MULTIPLY',value.outputs[0],lum.outputs[0]),p.inputs['Alpha'])
    mesh.materials.append(m);obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);return obj
first_fx=next(s['fx'] for s in take['samples'] if 'fx' in s)
quads=[plane('GR_OpticalLayer%02d'%i,int(v['tile'])) for i,v in enumerate(first_fx['quads'])]
sparks=[plane('GR_PrintGlint%02d'%i,2) for i in range(32)]
print_root=bpy.data.objects[data['record_player']['print_root']]
roots=[bpy.data.objects[c['root']] for c in data['g_archive']['contents']]
print_values=[]
for i,root in enumerate(roots):
    values=[];materials={}
    for obj in [root]+list(root.children_recursive):
        obj.hide_set(False)
        if obj.type not in ['MESH','CURVE','FONT']:continue
        for slot in obj.material_slots:
            original=slot.material
            if not original or not original.use_nodes:continue
            if original.name in materials:slot.material=materials[original.name];continue
            m=original.copy();m.name='GR_Print%d_'%i+original.name;materials[original.name]=m;slot.material=m
            n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
            if not p:continue
            tex=n.new('ShaderNodeTexCoord');tex.object=print_root;sep=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Object'],sep.inputs[0])
            height=take['heights'][i];progress=n.new('ShaderNodeValue');progress.name='RecordedPrintProgress';values.append(progress.outputs[0])
            z=sep.outputs['Z'];boundary=mathnode(n,l,'MULTIPLY',progress.outputs[0],height);ghost=mathnode(n,l,'GREATER_THAN',z,boundary)
            metallic=p.inputs['Metallic'].default_value
            visible=mathnode(n,l,'LESS_THAN',z,mathnode(n,l,'ADD',boundary,height*.38 if metallic>=.8 else .0001))
            l.new(visible,p.inputs['Alpha'])
            if metallic>=.8:
                mix=n.new('ShaderNodeMixRGB');l.new(ghost,mix.inputs[0]);mix.inputs[2].default_value=(.006,.016,.022,1)
                if p.inputs['Base Color'].is_linked:l.new(p.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
                else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
                l.new(mix.outputs[0],p.inputs['Base Color']);l.new(mathnode(n,l,'MULTIPLY',mathnode(n,l,'SUBTRACT',1,ghost),metallic),p.inputs['Metallic'])
            edge=mathnode(n,l,'MAXIMUM',0,mathnode(n,l,'SUBTRACT',1,mathnode(n,l,'DIVIDE',mathnode(n,l,'ABSOLUTE',mathnode(n,l,'SUBTRACT',z,boundary)),.018)))
            live=mathnode(n,l,'LESS_THAN',progress.outputs[0],.9999);edge=mathnode(n,l,'MULTIPLY',edge,live)
            color=n.new('ShaderNodeMixRGB');l.new(ghost,color.inputs[0]);color.inputs[1].default_value=(1,.55,.19,1);color.inputs[2].default_value=(.14,.48,.8,1)
            energy=mathnode(n,l,'ADD',mathnode(n,l,'MULTIPLY',edge,7),mathnode(n,l,'MULTIPLY',ghost,2.4 if metallic>=.8 else 0))
            l.new(color.outputs[0],p.inputs['Emission Color']);l.new(energy,p.inputs['Emission Strength'])
    print_values.append(values)
lamps={}
for key in ['Read','Print','Play','Spin','Stop']:
    obj=bpy.data.objects.get('ConsoleLamp'+key)
    if obj:
        for child in obj.children:
            if child.type=='MESH':
                mat=child.data.materials[0].copy();mat.name='GR_ConsoleLens'+key;child.data.materials[0]=mat;lamps[key]=mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
last={};keys={}
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def key(obj,f):
    for prop in ['location','rotation_quaternion','scale']:obj.keyframe_insert(prop,frame=f)
def animate(obj,p,f):
    if p==last.get(obj.name):return
    obj.rotation_mode='QUATERNION'
    if obj.name in last and keys[obj.name]<f-1:obj.matrix_basis=pose(last[obj.name]);key(obj,f-1)
    obj.matrix_basis=pose(p);key(obj,f);last[obj.name]=p;keys[obj.name]=f
def optical(obj,p,gain,f,scale=1):
    obj.rotation_mode='QUATERNION';obj.matrix_world=CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s'])*scale);key(obj,f)
    obj.color=(gain,gain,gain,1);obj.keyframe_insert('color',frame=f);obj.hide_render=gain<.002;obj.hide_viewport=gain<.002;obj.keyframe_insert('hide_render',frame=f);obj.keyframe_insert('hide_viewport',frame=f)
previous=''
for sample in take['samples']:
    f=sample['frame'];state=sample['state'];tag=str(state['selected']+1)+'_'+state['stage'].upper()
    if tag!=previous:scene.timeline_markers.new(tag,frame=f);previous=tag
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:animate(obj,p,f)
    for item in sample['widgets']:
        obj,children=widgets[item['gesture']];animate(obj,item['pose'],f)
        for child,p in zip(children,item['moving']):animate(child,p,f)
    for i,root in enumerate(roots):
        visible=i==state['loaded_index'] and state['print_amount']>.0001
        for child in [root]+list(root.children_recursive):
            if child.hide_render==visible or f==1:
                child.hide_render=not visible;child.hide_viewport=not visible;child.keyframe_insert('hide_render',frame=f);child.keyframe_insert('hide_viewport',frame=f)
        for value in print_values[i]:value.default_value=state['print_amount'] if i==state['loaded_index'] else 0.;value.keyframe_insert('default_value',frame=f)
    for key_name,value in sample.get('console_lamps',{}).items():
        if key_name in lamps:lamps[key_name].default_value=.025+value*1.65;lamps[key_name].keyframe_insert('default_value',frame=f)
    if 'fx' not in sample:continue
    for obj,item in zip(quads,sample['fx']['quads']):optical(obj,item['pose'],item['gain'],f)
    # The runtime pool has fixed seeds and uses this same time/pivot formula.
    fx=sample['fx'];origin=Vector((0,.906,.72));height=state['print_amount']*take['heights'][max(0,state['loaded_index'])]
    for i,obj in enumerate(sparks):
        a=i*2.39996+state['platter_angle'];t=((f/30)*.55+i/32)%1;r=.16+.24*(i%7)/6
        p=dict(fx['quads'][2]['pose']);p['p']=list(origin+Vector((r*math.cos(a),height+t*.10,r*math.sin(a))));p['s']=[.045]*3
        gain=sample['power']*(1-sample['explosion'])*(1-t)*.40 if state['stage'] in ['printing','erasing'] else 0
        optical(obj,p,gain,f)
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:point.interpolation='CONSTANT' if curve.data_path in ['hide_render','hide_viewport'] else 'LINEAR'
scene['animation_source']='record_take.json; original-disc movement, six acts, printing, physical console, return, explosion and interruption'
scene['console']='Physical controls only; no floating operator panel'
scene.frame_set(1)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/G_record_player.blend'))
(ROOT/'review/G_record_player/blender_bake.json').write_text(json.dumps({'frames':scene.frame_end,'fps':30,'animated_objects':len(last),'optical_layers':len(quads),'glints':len(sparks),'specimens':6,'physical_controls':5,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256'],'print_method':'platter-local height shader; fixed object scale'},indent=2),encoding='utf-8')
print('RECORD_SOURCE_BAKED',scene.frame_end,len(last),flush=True)
