"""Bake the archive player's six actual runtime acts into G_archive.blend."""
import bpy,json,pathlib,math,sys
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
model='G_archive_detail'
if '--' in sys.argv:
    for arg in sys.argv[sys.argv.index('--')+1:]:
        if arg.startswith('--model='):model=arg.split('=',1)[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection'/(model+'.blend')))
scene=bpy.context.scene;scene.frame_set(1)
take=json.loads((ROOT/'review/G_archive/archive_take.json').read_text(encoding='utf-8'))
data=json.loads((ROOT/'app/assets/collection/models'/(model+'.json')).read_text(encoding='utf-8'))
for col in list(bpy.data.collections):
    if col.name.startswith('G4_CAPTURED_READ'):
        for obj in list(col.all_objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(col)
col=bpy.data.collections.new('G4_CAPTURED_READ');scene.collection.children.link(col)
scene.render.fps=30;scene.frame_end=take['samples'][-1]['frame'];scene.timeline_markers.clear()
for name in take['samples'][0]['poses']:
    obj=bpy.data.objects.get(name)
    if obj:obj.animation_data_clear()
atlas=bpy.data.images.load(str(ROOT/'app/assets/collection/art/G/optical_atlas.png'),check_existing=True)
def plane(name,tile):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
    uv=mesh.uv_layers.new();coords=[(0,0),(1,0),(1,1),(0,1)]
    for loop in mesh.loops:
        u,v=coords[loop.vertex_index];uv.data[loop.index].uv=((tile%2+u)*.5,(1-tile//2+v)*.5)
    mat=bpy.data.materials.new(name+'_Art');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage');tex.image=atlas;info=n.new('ShaderNodeObjectInfo');value=n.new('ShaderNodeRGBToBW');lum=n.new('ShaderNodeRGBToBW');mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';energy=n.new('ShaderNodeMath');energy.operation='MULTIPLY';energy.inputs[1].default_value=5
    l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(tex.outputs['Color'],p.inputs['Emission Color']);l.new(tex.outputs['Color'],lum.inputs[0]);l.new(info.outputs['Color'],value.inputs[0]);l.new(value.outputs[0],mul.inputs[0]);l.new(lum.outputs[0],mul.inputs[1]);l.new(mul.outputs[0],p.inputs['Alpha']);l.new(value.outputs[0],energy.inputs[0]);l.new(energy.outputs[0],p.inputs['Emission Strength'])
    mesh.materials.append(mat);obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);return obj
fx=next(s['fx'] for s in take['samples'] if 'fx' in s)
quads=[plane('G4_ReadArt_%02d'%i,int(v['tile'])) for i,v in enumerate(fx['quads'])]
particles=[plane('G4_ReadGlint_%02d'%i,2) for i in range(len(fx['particles']))]
widgets={}
for kind in ['rotary','slider_x','hold','gauge','service']:
    node=bpy.data.objects.get('CTRL_'+kind)
    if node:
        widgets[kind.replace('_x','')]=(node,[o for o in node.children if 'WidgetSocket' not in o.name and 'WidgetRim' not in o.name])
        for o in [node]+widgets[kind.replace('_x','')][1]:o.animation_data_clear()
last={};keyframe={}
def mat(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def key(o,f):
    for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(prop,frame=f)
def animate(o,p,f):
    if p==last.get(o.name):return
    o.rotation_mode='QUATERNION'
    if o.name in last and keyframe[o.name]<f-1:o.matrix_basis=mat(last[o.name]);key(o,f-1)
    o.matrix_basis=mat(p);key(o,f);last[o.name]=p;keyframe[o.name]=f
roots=[bpy.data.objects[c['root']] for c in data['g_archive']['contents']]
signal=bpy.data.materials.get('Collection_Signal')
if signal:signal.node_tree.animation_data_clear()
previous='';cue_frames=[]
for sample in take['samples']:
    f=sample['frame'];state=sample['state'];tag=str(state['selected']+1)+'_'+state['stage'].upper()
    if tag!=previous:scene.timeline_markers.new(tag,frame=f);previous=tag
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:animate(obj,p,f)
    for item in sample['widgets']:
        if item['gesture'] in widgets:
            node,children=widgets[item['gesture']];animate(node,item['pose'],f)
            for o,p in zip(children,item['moving']):animate(o,p,f)
    for i,obj in enumerate(roots):
        visible=i==state['loaded_index'] and state['display_amount']>.002
        for child in [obj]+list(obj.children_recursive):
            if child.hide_render==visible or f==1:
                child.hide_render=not visible;child.hide_viewport=not visible;child.keyframe_insert('hide_render',frame=f);child.keyframe_insert('hide_viewport',frame=f)
    if signal:
        strength=signal.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'];strength.default_value=sample['open']*(.18+state['display_amount']*.5+state['action_energy']*.45);strength.keyframe_insert('default_value',frame=f)
    if 'fx' not in sample:continue
    for objects,items,scale in [(quads,sample['fx']['quads'],1),(particles,sample['fx']['particles'],.045)]:
        for o,item in zip(objects,items):
            p=item['pose'];o.rotation_mode='QUATERNION';o.matrix_world=CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s'])*scale);key(o,f)
            g=item['gain'];o.color=(g,g,g,1);o.keyframe_insert('color',frame=f);o.hide_render=g<.003;o.keyframe_insert('hide_render',frame=f)
for action in bpy.data.actions:
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:point.interpolation='CONSTANT' if curve.data_path in ['hide_render','hide_viewport'] else 'LINEAR'
    except AttributeError:pass
scene['animation_source']='review/G_archive/archive_take.json; same controller and per-specimen rigs as runtime'
scene.frame_set(1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection'/(model+'.blend')))
(ROOT/'review/G_archive/blender_bake.json').write_text(json.dumps({'frames':scene.frame_end,'fps':30,'animated_objects':len(last),'specimens':6,'optical_layers':len(quads),'glints':len(particles),'same_runtime_take':True},indent=2),encoding='utf-8')
print('G_ARCHIVE_BAKED',scene.frame_end,'frames',len(last),'objects',flush=True)
