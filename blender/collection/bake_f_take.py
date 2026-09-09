"""Bake the runtime's physical take into the editable Blender source.
Mechanisms, controller gestures and solid field particles use the captured
transforms. The source therefore shares the runtime timing, not a second fake
sine-wave animation. Only F_complete.blend is updated.
"""
import bpy,json,pathlib,math
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/F_complete.blend'))
scene=bpy.context.scene;scene.frame_set(1)
take=json.loads((ROOT/'review/F_complete/physical_take.json').read_text(encoding='utf-8'))
metadata=json.loads((ROOT/'app/assets/collection/models/F_complete.json').read_text(encoding='utf-8'))
for collection in list(bpy.data.collections):
    if collection.name=='F_CAPTURED_FIELD' or collection.name.startswith('F_CAPTURED_FIELD.'):
        for obj in list(collection.all_objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(collection)
for name in take['samples'][0]['poses']:
    obj=bpy.data.objects.get(name)
    if obj:obj.animation_data_clear()
signal=bpy.data.materials.get('Collection_Signal')
if signal:signal.node_tree.animation_data_clear()
if scene.sequence_editor:
    strips=getattr(scene.sequence_editor,'strips',getattr(scene.sequence_editor,'sequences',None))
    if strips:
        for strip in list(strips):
            if strip.name.startswith('F calibration'):strips.remove(strip)
scene.render.fps=take['fps'];scene.frame_end=take['samples'][-1]['frame']

def matrix(p):
    return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def key(o,frame):
    o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_quaternion',frame=frame);o.keyframe_insert('scale',frame=frame)
last={};last_key={}
def animate(o,p,frame):
    o.rotation_mode='QUATERNION'
    if p==last.get(o.name):return
    if o.name in last and last_key[o.name]<frame-1:
        o.matrix_basis=matrix(last[o.name]);key(o,frame-1)
    o.matrix_basis=matrix(p);key(o,frame);last[o.name]=p;last_key[o.name]=frame

# Every input cassette uses the same root and local moving pieces as Godot.
widgets={}
for kind in ['rotary','hold','detent','gauge','service']:
    node=bpy.data.objects.get('CTRL_'+kind)
    if node:
        widgets[kind]=(node,[o for o in node.children if 'WidgetSocket' not in o.name and 'WidgetRim' not in o.name])
        for obj in [node]+widgets[kind][1]:obj.animation_data_clear()

fx_collection=bpy.data.collections.new('F_CAPTURED_FIELD');scene.collection.children.link(fx_collection)
def emission_material(name,metal=False):
    material=bpy.data.materials.new(name);material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links;p=nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.72,.51,.23,1)
    p.inputs['Metallic'].default_value=.94 if metal else 0
    p.inputs['Roughness'].default_value=.20
    p.inputs['Emission Color'].default_value=(1,.64,.25,1)
    info=nodes.new('ShaderNodeObjectInfo');luma=nodes.new('ShaderNodeRGBToBW');scale=nodes.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=6
    links.new(info.outputs['Color'],luma.inputs[0]);links.new(luma.outputs[0],scale.inputs[0]);links.new(scale.outputs[0],p.inputs['Emission Strength'])
    return material
foil_mat=emission_material('F_CapturedMetalField',True)
line_mat=emission_material('F_CapturedFilament')
atlas=bpy.data.images.load(str(ROOT/'app/assets/collection/art/F/field_atlas.png'),check_existing=True)
def image_plane(name,tile):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
    uv=mesh.uv_layers.new();coords=[(0,0),(1,0),(1,1),(0,1)]
    for loop in mesh.loops:
        u,v=coords[loop.vertex_index];uv.data[loop.index].uv=((tile%2+u)*.5,((1-tile//2)+v)*.5)
    material=bpy.data.materials.new(name+'_Atlas');material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links;shader=nodes.get('Principled BSDF')
    image=nodes.new('ShaderNodeTexImage');image.image=atlas
    luma=nodes.new('ShaderNodeRGBToBW');info=nodes.new('ShaderNodeObjectInfo');strength=nodes.new('ShaderNodeRGBToBW')
    alpha=nodes.new('ShaderNodeMath');alpha.operation='MULTIPLY'
    energy=nodes.new('ShaderNodeMath');energy.operation='MULTIPLY';energy.inputs[1].default_value=6
    links.new(image.outputs['Color'],shader.inputs['Emission Color']);links.new(image.outputs['Color'],shader.inputs['Base Color'])
    links.new(image.outputs['Color'],luma.inputs[0]);links.new(info.outputs['Color'],strength.inputs[0]);links.new(luma.outputs[0],alpha.inputs[0]);links.new(strength.outputs[0],alpha.inputs[1]);links.new(alpha.outputs[0],shader.inputs['Alpha'])
    links.new(strength.outputs[0],energy.inputs[0]);links.new(energy.outputs[0],shader.inputs['Emission Strength'])
    mesh.materials.append(material);obj=bpy.data.objects.new(name,mesh);fx_collection.objects.link(obj);return obj
waves=[image_plane('F_ReceiverWave_'+str(i),0) for i in range(2)]
seed=image_plane('F_WritebackSeed',2)
prototypes=[bpy.data.objects['F3_VernierTickPrototype'],bpy.data.objects['F3_SwarfPrototype']]
for obj in prototypes:obj.hide_render=True;obj.hide_set(True)
shards=[]
for i in range(112):
    original=prototypes[0 if i<28 else 1]
    o=bpy.data.objects.new('F_FieldNeedle_%03d'%i,original.data.copy());fx_collection.objects.link(o)
    o.data.materials.clear();o.data.materials.append(foil_mat);o.rotation_mode='QUATERNION';shards.append(o)

lines=[]
for index in range(4):
    curve=bpy.data.curves.new('F_FieldPath_'+str(index),'CURVE');curve.dimensions='3D';curve.bevel_depth=.0023 if index<3 else .0020;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');spline.points.add(24 if index<3 else 1)
    obj=bpy.data.objects.new(curve.name,curve);fx_collection.objects.link(obj);curve.materials.append(line_mat);lines.append(obj)

lights=[]
for i in range(3):
    d=bpy.data.lights.new('F_FieldLight_'+str(i),'POINT');d.color=(1,.64,.27);d.shadow_soft_size=.12
    o=bpy.data.objects.new(d.name,d);fx_collection.objects.link(o);lights.append(o)

phase_markers=set();peak_frames=[]
scene.timeline_markers.clear()
for sample in take['samples']:
    frame=sample['frame']
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:animate(obj,p,frame)
    for item in sample['widgets']:
        if item['gesture'] not in widgets:continue
        root,moving=widgets[item['gesture']];animate(root,item['pose'],frame)
        for obj,p in zip(moving,item['moving']):animate(obj,p,frame)
    state=sample['state'];stage=state['stage']
    if stage not in phase_markers:
        scene.timeline_markers.new(stage.upper(),frame=frame);phase_markers.add(stage)
    peak_time=state['peak_time']
    if 0<=peak_time<1/take['fps']*1.1:peak_frames.append(frame)
    if 'fx' not in sample:continue
    bpy.context.view_layer.update()
    fx=sample['fx'];gain=fx['gain'];visible=fx['visible']
    for obj,p in zip(shards,fx['shards']):
        obj.matrix_world=matrix(p)
        if not visible:obj.scale=(.00001,)*3
        key(obj,frame)
        color=min(1,p['glow']/4) if visible else 0;obj.color=(color,color,color,1);obj.keyframe_insert('color',frame=frame)
    plumb=bpy.data.objects[metadata['f_physics']['plumb_pivot']]
    prism=bpy.data.objects[metadata['f_physics']['prism_pivot']]
    receiver=bpy.data.objects[metadata['f_fx']['receiver']]
    tip=bpy.data.objects[metadata['sockets']['weight_tip']].matrix_world.translation
    foot=Vector((tip.x,tip.y,receiver.matrix_world.translation.z+.058))
    for i,obj in enumerate(lines):
        spline=obj.data.splines[0]
        if i<3:
            a=bpy.data.objects[metadata['f_fx']['contacts'][[0,4,8][i]]].matrix_world.translation
            endpoint=plumb.matrix_world@Vector((0,0,-.55)) if i!=1 else prism.matrix_world@Vector((0,0,-.53))
            middle=(a+endpoint)*.5+Vector((-.12,-.22 if i%2==0 else .20,.08))
            positions=[a*(1-t)*(1-t)+middle*2*t*(1-t)+endpoint*t*t for t in [k/24 for k in range(25)]]
        else:positions=[tip,foot]
        for point,position in zip(spline.points,positions):point.co=(*position,1);point.keyframe_insert('co',frame=frame)
        strength=gain*.20 if i<3 else (state['coherence']*.20+(1.4 if peak_time>=0 else 0))*sample['open']
        if not visible:strength=0
        obj.color=(strength,)*3+(1,);obj.keyframe_insert('color',frame=frame)
    center=plumb.matrix_world@Vector((0,0,-.49))
    peak=(max(0,min(1,peak_time/.85))*(1-max(0,min(1,(peak_time-3)/2.5)))) if peak_time>=0 else 0
    for i,o in enumerate(waves):
        phase=(max(0,peak_time)*.32+i*.5)%1;size=(.30+phase*.65)*1.2
        o.location=foot+Vector((0,0,.01+i*.003));o.scale=(size,size,size)
        o.keyframe_insert('location',frame=frame);o.keyframe_insert('scale',frame=frame)
        power=peak*(1-phase) if visible else 0;o.color=(power,)*3+(1,);o.keyframe_insert('color',frame=frame)
    returning=max(0,min(1,(peak_time-3.4)/2.1)) if peak_time>=0 else 0
    angle=math.radians(90+returning*(51-state['preload_value']*28))
    seed.location=bpy.data.objects[metadata['upper']].matrix_world@Vector((-.1+.887*math.cos(angle),-.125,1.8+.887*math.sin(angle)))
    seed.rotation_mode='QUATERNION';seed.rotation_quaternion=(scene.camera.matrix_world.translation-seed.location).to_track_quat('Z','Y');seed.scale=(.20,)*3
    key(seed,frame);power=peak if visible else 0;seed.color=(power,)*3+(1,);seed.keyframe_insert('color',frame=frame)
    for i,o in enumerate(lights):
        o.location=[center+Vector((0,-.10,.04)),foot+Vector((0,0,.09)),bpy.data.objects[metadata['f_fx']['contacts'][0]].matrix_world.translation][i]
        o.data.energy=(45 if i<2 else 20)*gain;o.keyframe_insert('location',frame=frame);o.data.keyframe_insert('energy',frame=frame)
    signal=bpy.data.materials.get('Collection_Signal')
    if signal:
        emission=signal.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'];emission.default_value=.10+gain*2.5;emission.keyframe_insert('default_value',frame=frame)

for action in bpy.data.actions:
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:point.interpolation='LINEAR'
    except AttributeError:pass
if peak_frames:
    try:
        editor=scene.sequence_editor_create();strips=getattr(editor,'strips',getattr(editor,'sequences',None))
        sound=strips.new_sound('F calibration',str(ROOT/'app/assets/collection/art/F/calibration.wav'),channel=1,frame_start=peak_frames[0]);sound.volume=.25
    except Exception as exc:print('AUDIO_STRIP',str(exc))
scene['animation_source']='review/F_complete/physical_take.json; tests/collection/f_visual_take.gd'
scene['physics']='Coupled constrained four-bar + two spherical hangers, RK4 240 Hz. Native rendering remains interactive.'
scene['take_fps']=take['fps'];scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
            area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL'
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/F_complete.blend'))
report={'frames':len(take['samples']),'fps':take['fps'],'animated_objects':len(last),'field_particles':len(shards),'phase_markers':sorted(phase_markers),'same_physics_as_runtime':True,'original_sources_preserved':True}
(ROOT/'review/F_complete/blender_bake.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('F_PHYSICAL_ANIMATION_BAKED',report,flush=True)
