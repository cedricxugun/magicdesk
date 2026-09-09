"""Bake the actual G runtime take, including optical assets and native controls."""
import bpy,json,pathlib,math
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_complete.blend'))
scene=bpy.context.scene;scene.frame_set(1)
take=json.loads((ROOT/'review/G_complete/mechanical_take.json').read_text(encoding='utf-8'))
data=json.loads((ROOT/'app/assets/collection/models/G_complete.json').read_text(encoding='utf-8'))
for col in list(bpy.data.collections):
    if col.name.startswith('G_CAPTURED_OPTICS'):
        for o in list(col.all_objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(col)
col=bpy.data.collections.new('G_CAPTURED_OPTICS');scene.collection.children.link(col)
for name in take['samples'][0]['poses']:
    obj=bpy.data.objects.get(name)
    if obj:obj.animation_data_clear()
scene.render.fps=30;scene.frame_end=take['samples'][-1]['frame'];scene.timeline_markers.clear()
atlas=bpy.data.images.load(str(ROOT/'app/assets/collection/art/G/optical_atlas.png'),check_existing=True)
def plane(name,tile):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
    uv=mesh.uv_layers.new();coords=[(0,0),(1,0),(1,1),(0,1)]
    for loop in mesh.loops:
        u,v=coords[loop.vertex_index];uv.data[loop.index].uv=((tile%2+u)*.5,(1-tile//2+v)*.5)
    m=bpy.data.materials.new(name+'_OpticalArt');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage');tex.image=atlas
    info=n.new('ShaderNodeObjectInfo');energy=n.new('ShaderNodeRGBToBW');luma=n.new('ShaderNodeRGBToBW')
    mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=5
    l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(tex.outputs['Color'],p.inputs['Emission Color']);l.new(tex.outputs['Color'],luma.inputs[0]);l.new(info.outputs['Color'],energy.inputs[0]);l.new(luma.outputs[0],mult.inputs[0]);l.new(energy.outputs[0],mult.inputs[1]);l.new(mult.outputs[0],p.inputs['Alpha']);l.new(energy.outputs[0],strength.inputs[0]);l.new(strength.outputs[0],p.inputs['Emission Strength'])
    mesh.materials.append(m);o=bpy.data.objects.new(name,mesh);col.objects.link(o);return o
fx=next(s['fx'] for s in take['samples'] if 'fx' in s)
quads=[plane('G_Optic_%02d'%i,int(item['tile'])) for i,item in enumerate(fx['quads'])]
glints=[plane('G_Swarf_%02d'%i,2) for i in range(64)]
widgets={}
for kind in ['rotary','slider_x','hold','gauge','service']:
    node=bpy.data.objects.get('CTRL_'+kind)
    if node:widgets[kind.replace('_x','')]=(node,[o for o in node.children if 'WidgetSocket' not in o.name and 'WidgetRim' not in o.name])
for root,children in widgets.values():
    for obj in [root]+children:obj.animation_data_clear()
last={};lastframe={}
def matrix(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def key(o,frame):
    for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(prop,frame=frame)
def animate(o,p,f):
    if p==last.get(o.name):return
    o.rotation_mode='QUATERNION'
    if o.name in last and lastframe[o.name]<f-1:o.matrix_basis=matrix(last[o.name]);key(o,f-1)
    o.matrix_basis=matrix(p);key(o,f);last[o.name]=p;lastframe[o.name]=f
reliefs=[]
for name in data['g_mechanism']['relief_layers']:
    row=bpy.data.objects[name]
    for child in row.children:
        child.animation_data_clear()
    reliefs.append(row)
laststage=''
for sample in take['samples']:
    f=sample['frame'];st=sample['state']
    if st['stage']!=laststage:scene.timeline_markers.new(st['stage'].upper(),frame=f);laststage=st['stage']
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:animate(obj,p,f)
    for item in sample['widgets']:
        if item['gesture'] not in widgets:continue
        root,children=widgets[item['gesture']];animate(root,item['pose'],f)
        for o,p in zip(children,item['moving']):animate(o,p,f)
    if 'fx' not in sample:continue
    fx=sample['fx']
    for i,row in enumerate(reliefs):
        reveal=max(0,min(1,fx['projection']*30-i))
        row.hide_render=reveal<.002;row.hide_viewport=reveal<.002;row.keyframe_insert('hide_render',frame=f);row.keyframe_insert('hide_viewport',frame=f)
        row.scale=(1,1,max(.001,reveal));row.keyframe_insert('scale',frame=f)
    for o,item in zip(quads,fx['quads']):
        # GPU quad XY corresponds to Blender XZ; supply C-converted basis.
        o.rotation_mode='QUATERNION';o.matrix_world=CI@Matrix.LocRotScale(Vector(item['pose']['p']),Quaternion((item['pose']['q'][3],*item['pose']['q'][:3])),Vector(item['pose']['s']))
        key(o,f);g=item['gain'];o.color=(g,g,g,1);o.keyframe_insert('color',frame=f)
        o.hide_render=g<.003;o.keyframe_insert('hide_render',frame=f)
    for o,item in zip(glints,fx['particles']):
        o.rotation_mode='QUATERNION';p=item['pose'];o.matrix_world=CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s'])*.075)
        key(o,f);g=item['gain'];o.color=(g,g,g,1);o.keyframe_insert('color',frame=f);o.hide_render=g<.003;o.keyframe_insert('hide_render',frame=f)
for action in bpy.data.actions:
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:point.interpolation='LINEAR' if curve.data_path not in ['hide_render','hide_viewport'] else 'CONSTANT'
    except AttributeError:pass
editor=scene.sequence_editor_create();strips=getattr(editor,'strips',getattr(editor,'sequences',None))
if strips is not None:
    for strip in list(strips):
        if strip.name.startswith('G inscription'):strips.remove(strip)
    marker=scene.timeline_markers.get('MEMORY_RELIEF')
    if marker:
        sound=strips.new_sound('G inscription',str(ROOT/'app/assets/collection/art/G/inscription.wav'),channel=1,frame_start=marker.frame);sound.volume=.25
scene['animation_source']='review/G_complete/mechanical_take.json; actual runtime kinematics and effects'
scene.frame_set(1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/G_complete.blend'))
print('G_BAKED',scene.frame_end,'frames',len(quads),'optics',len(glints),'chips/glints')
