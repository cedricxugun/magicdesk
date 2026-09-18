"""Bake captured F revision into its isolated source; no main source overwrite.
Mechanical/UI tracks are 30 Hz, optical/field tracks use the recorded 15 Hz
samples. Texture planes use the authored atlas, not reconstructed sine paths.
"""
import bpy,sys,json,math,hashlib,shutil,collections
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/F_complete/revision_20260911/full_take'
TARGET=ROOT/'blender/collection/F_refinement_candidate.blend'
ORIGINAL=ROOT/'blender/collection/F_complete.blend'
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original_hash=sha(ORIGINAL);take=json.loads((OUT/'physical_take.json').read_text())
peak=next(s['fx'] for s in take['samples'] if 'fx' in s and 1.4<s['state']['peak_time']<1.65)
assert max(p['glow'] for p in peak['shards'][:28])>.05, 'Invalid field capture: dummy renderer data'
assert len({tuple(round(v,4) for v in p['p']) for p in peak['shards'][:28]})==28, 'Collapsed field positions'
for path,key in [('models/F_complete.glb','model_sha256'),('models/F_complete.json','metadata_sha256'),('f_refined_controls.glb','controls_sha256')]:
    assert sha(ROOT/'app/assets/collection'/path)==take[key],('Stale take',path)
backup=ROOT/'blender/collection/checkpoints'/('F-before-revision-bake-'+sha(TARGET)[:12]+'.blend')
if not backup.exists():shutil.copy2(TARGET,backup)
bpy.ops.wm.open_mainfile(filepath=str(TARGET));scene=bpy.context.scene;scene.frame_set(1)
for obj in bpy.data.objects:obj.animation_data_clear()
for col in list(bpy.data.collections):
    if col.name.startswith(('F_CAPTURED_FIELD','F_REVISION_FIELD')):
        for obj in list(col.all_objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(col)
if scene.sequence_editor:scene.sequence_editor_clear()
scene.render.fps=take['fps'];scene.frame_end=take['samples'][-1]['frame'];scene.timeline_markers.clear()
fxcol=bpy.data.collections.new('F_REVISION_FIELD');scene.collection.children.link(fxcol)
tracks=collections.defaultdict(lambda:collections.defaultdict(list));previous_quat={}
def put(obj,path,index,frame,value):tracks[obj][path,index].append((frame,float(value)))
def matrix(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def pose(obj,p,frame):
    loc,q,scale=matrix(p).decompose();obj.rotation_mode='QUATERNION'
    if obj.name in previous_quat and q.dot(previous_quat[obj.name])<0:q.negate()
    previous_quat[obj.name]=q.copy()
    for prop,values in [('location',loc),('rotation_quaternion',q),('scale',scale)]:
        for i,v in enumerate(values):put(obj,prop,i,frame,v)
def visible(obj,value,frame):put(obj,'hide_render',0,frame,not value);put(obj,'hide_viewport',0,frame,not value)
def gain(obj,value,frame,variant=0.):
    put(obj,'color',0,frame,value/8.);put(obj,'color',1,frame,variant)
    put(obj,'color',2,frame,0.);put(obj,'color',3,frame,1.)
# Recorded projected glyphs are rebuilt as complete meshes, never assigned to
# potentially reordered glTF vertices by index.
glyph_vertices=0
for name,surfaces in take['console_projection']['meshes'].items():
    obj=bpy.data.objects[name];materials=list(obj.data.materials);verts=[];faces=[];normals=[];face_materials=[]
    for i,surface in enumerate(surfaces):
        offset=len(verts);verts.extend(CI.to_3x3()@Vector(v) for v in surface['vertices'])
        normals.extend(CI.to_3x3()@Vector(v) for v in surface['normals'])
        indices=surface['indices']
        for k in range(0,len(indices),3):faces.append(tuple(offset+j for j in indices[k:k+3]));face_materials.append(i)
    mesh=bpy.data.meshes.new(name+'_ExactPanelFit');mesh.from_pydata(verts,[],faces);mesh.update()
    for mat in materials:mesh.materials.append(mat)
    for poly,index in zip(mesh.polygons,face_materials):poly.material_index=min(index,len(materials)-1);poly.use_smooth=True
    if len(normals)==len(verts):mesh.normals_split_custom_set_from_vertices(normals)
    obj.data=mesh;glyph_vertices+=len(verts)
    ready=max(1,take.get('caption_ready_frame',1));visible(obj,ready<=1,1)
    if ready>1:visible(obj,False,ready-1);visible(obj,True,ready)
widgets={}
for kind in ['rotary','hold','detent','gauge','service']:
    obj=bpy.data.objects['FCTRL_'+kind];widgets[kind]=(obj,{o.name.replace('.','_'):o for o in obj.children})
# Shader equivalents use actual per-object captured gain. Object color R stores
# gain/8 to retain HDR strength without clamping its UI-color storage.
def mathnode(nodes,links,op,*inputs):
    node=nodes.new('ShaderNodeMath');node.operation=op
    for i,v in enumerate(inputs):
        if isinstance(v,(int,float)):node.inputs[i].default_value=v
        else:links.new(v,node.inputs[i])
    return node.outputs[0]
def color_gain(nodes,links):
    info=nodes.new('ShaderNodeObjectInfo');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(info.outputs['Color'],sep.inputs[0])
    return mathnode(nodes,links,'MULTIPLY',sep.outputs['X'],8.),sep.outputs['Y']
foilmat=bpy.data.materials.new('FRevision_ManufacturedNeedles');foilmat.use_nodes=True
nodes=foilmat.node_tree.nodes;links=foilmat.node_tree.links;p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');field,var=color_gain(nodes,links)
mix=nodes.new('ShaderNodeMixRGB');links.new(var,mix.inputs[0]);mix.inputs[1].default_value=(.46,.30,.10,1);mix.inputs[2].default_value=(.82,.69,.37,1);links.new(mix.outputs[0],p.inputs['Base Color'])
p.inputs['Metallic'].default_value=.94;p.inputs['Roughness'].default_value=.20;p.inputs['Coat Weight'].default_value=.22;p.inputs['Coat Roughness'].default_value=.14
p.inputs['Emission Color'].default_value=(1,.68,.27,1)
links.new(mathnode(nodes,links,'MULTIPLY',field,mathnode(nodes,links,'ADD',.8,mathnode(nodes,links,'MULTIPLY',var,1.4))),p.inputs['Emission Strength'])
atlas=bpy.data.images.load(str(ROOT/'app/assets/collection/art/F/field_atlas.png'),check_existing=True);plane_materials={}
def atlas_material(tile):
    if tile in plane_materials:return plane_materials[tile]
    mat=bpy.data.materials.new('FRevision_Atlas_'+str(tile));mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');tex=nodes.new('ShaderNodeTexImage');tex.image=atlas;tex.extension='EXTEND'
    coord=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coord.outputs['UV'],sep.inputs[0]);vector=nodes.new('ShaderNodeCombineXYZ')
    du,dv={0:(-.0052,-.0007),1:(0,0),2:(-.0091,-.0491),3:(0,-.0443)}[tile]
    u=mathnode(nodes,links,'MINIMUM',.995,mathnode(nodes,links,'MAXIMUM',.005,mathnode(nodes,links,'ADD',sep.outputs['X'],du)))
    v=mathnode(nodes,links,'MINIMUM',.995,mathnode(nodes,links,'MAXIMUM',.005,mathnode(nodes,links,'ADD',sep.outputs['Y'],dv)))
    links.new(mathnode(nodes,links,'MULTIPLY',.5,mathnode(nodes,links,'ADD',tile%2,u)),vector.inputs['X'])
    links.new(mathnode(nodes,links,'SUBTRACT',1.,mathnode(nodes,links,'MULTIPLY',.5,mathnode(nodes,links,'ADD',tile//2,v))),vector.inputs['Y']);links.new(vector.outputs[0],tex.inputs['Vector'])
    rgb=nodes.new('ShaderNodeSeparateXYZ');links.new(tex.outputs['Color'],rgb.inputs[0]);value=mathnode(nodes,links,'MAXIMUM',rgb.outputs['X'],mathnode(nodes,links,'MAXIMUM',rgb.outputs['Y'],rgb.outputs['Z']))
    t=mathnode(nodes,links,'MINIMUM',1.,mathnode(nodes,links,'MAXIMUM',0.,mathnode(nodes,links,'DIVIDE',mathnode(nodes,links,'SUBTRACT',value,.018),.077)))
    mask=mathnode(nodes,links,'MULTIPLY',mathnode(nodes,links,'MULTIPLY',t,t),mathnode(nodes,links,'SUBTRACT',3.,mathnode(nodes,links,'MULTIPLY',2.,t)))
    strength,_=color_gain(nodes,links)
    alpha=mathnode(nodes,links,'MULTIPLY',mask,mathnode(nodes,links,'MINIMUM',.9,mathnode(nodes,links,'MULTIPLY',value,mathnode(nodes,links,'MULTIPLY',1.8,strength))))
    tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1.;tint.inputs[2].default_value=(1,((.96+.055)/1.055)**2.4,((.86+.055)/1.055)**2.4,1);links.new(tex.outputs['Color'],tint.inputs[1])
    emit=nodes.new('ShaderNodeEmission');links.new(tint.outputs[0],emit.inputs['Color']);emit.inputs['Strength'].default_value=1. # Metal unshaded atlas output ignores EMISSION; verified by zero/extreme probe
    transparent=nodes.new('ShaderNodeBsdfTransparent');blend=nodes.new('ShaderNodeMixShader');links.new(alpha,blend.inputs[0]);links.new(transparent.outputs[0],blend.inputs[1]);links.new(emit.outputs[0],blend.inputs[2]);links.new(blend.outputs[0],out.inputs['Surface'])
    plane_materials[tile]=mat;return mat

def quad(name,tile,size=(1,1),u_range=(0,1)):
    w,h=size;v=[(-w/2,h/2,0),(w/2,h/2,0),(w/2,-h/2,0),(-w/2,-h/2,0)]
    me=bpy.data.meshes.new(name);me.from_pydata([CI.to_3x3()@Vector(p) for p in v],[],[(0,3,2,1)])
    uv=me.uv_layers.new();coords=[(u_range[0],0),(u_range[1],0),(u_range[1],1),(u_range[0],1)]
    for loop in me.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
    me.materials.append(atlas_material(tile));obj=bpy.data.objects.new(name,me);fxcol.objects.link(obj);obj.visible_shadow=False;obj.visible_diffuse=False;obj.visible_glossy=False;obj.visible_transmission=False;return obj
first_fx=next(s['fx'] for s in take['samples'] if 'fx' in s)
# Runtime GLB prototypes include authored bevels; source raw mesh data does not.
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/collection/models/F_complete.glb'))
imported=set(bpy.data.objects)-existing;prototype_meshes={}
for name in ['F3_VernierTickPrototype','F3_SwarfPrototype']:
    runtime=next(o for o in imported if o.type=='MESH' and o.name.startswith(name))
    prototype_meshes[name]=runtime.data.copy();bpy.data.objects[name].hide_render=True
for obj in imported:bpy.data.objects.remove(obj,do_unlink=True)
shards=[]
for i in range(112):
    mesh=prototype_meshes['F3_VernierTickPrototype' if i<28 else 'F3_SwarfPrototype']
    obj=bpy.data.objects.new('FRevision_Solid_%03d'%i,mesh.copy());fxcol.objects.link(obj);obj.data.materials.clear();obj.data.materials.append(foilmat);obj.visible_shadow=False;shards.append(obj)
glints=[quad('FRevision_Glint_%03d'%i,2,(.17,.17)) for i in range(112)]
ribbons=[[quad('FRevision_Ribbon_%d_%02d'%(j,i),3,u_range=(i/28,(i+1)/28)) for i in range(28)] for j in range(3)]
filament=quad('FRevision_PlumbFilament',1,first_fx['filament']['size'])
seed=quad('FRevision_Writeback',2,first_fx['seed']['size'])
waves=[quad('FRevision_ReceiverWave_'+str(i),0,x['size']) for i,x in enumerate(first_fx['waves'])]
lights=[]
for i in range(4):
    d=bpy.data.lights.new('FRevision_FieldLight_'+str(i),'POINT');d.shadow_soft_size=.12
    obj=bpy.data.objects.new(d.name,d);fxcol.objects.link(obj);lights.append(obj)
lamp_root=bpy.data.objects['FCTRL_SettleLamp'];lamp=next(o for o in lamp_root.children_recursive if o.type=='MESH')
lamp_mat=lamp.data.materials[0].copy();lamp.data.materials[0]=lamp_mat;p=next(n for n in lamp_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Color'].default_value=(1,.4,.1,1)
lamp_path=p.inputs['Emission Strength'].path_from_id('default_value')
signal_sockets=[]
for mat in {slot.material for o in bpy.data.objects['F_MODULE'].children_recursive for slot in o.material_slots if slot.material and 'Signal' in slot.material.name}:
    mat.node_tree.animation_data_clear();p=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if p:signal_sockets.append((mat.node_tree,p.inputs['Emission Strength'].path_from_id('default_value')))
missing=set();last_stage=None
for sample in take['samples']:
    frame=sample['frame']
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj is None:missing.add(name);continue
        pose(obj,p,frame)
    for item in sample['widgets']:
        obj,moving=widgets[item['gesture']];pose(obj,item['pose'],frame)
        for name,p in zip(item['moving_names'],item['moving']):pose(moving[name],p,frame)
    put(lamp_mat.node_tree,lamp_path,0,frame,sample.get('settle_lamp',0.))
    stage=sample['state']['stage']
    if stage!=last_stage:scene.timeline_markers.new(stage,frame=frame);last_stage=stage
    if 'fx' not in sample:continue
    fx=sample['fx']
    for obj,item in zip(shards,fx['shards']):pose(obj,item,frame);gain(obj,item['glow'],frame,item['variant']);visible(obj,fx['visible'],frame)
    for obj,item in zip(glints,fx['glints']):pose(obj,item['pose'],frame);gain(obj,item['gain'],frame);visible(obj,item['visible'],frame)
    for objects,items in zip(ribbons,fx['ribbons']):
        for obj,item in zip(objects,items):pose(obj,item['pose'],frame);gain(obj,item['gain'],frame);visible(obj,item['visible'],frame)
    for obj,item in [(filament,fx['filament']),(seed,fx['seed'])]+list(zip(waves,fx['waves'])):
        pose(obj,item['pose'],frame);gain(obj,item['gain'],frame);visible(obj,item['visible'],frame)
    for obj,item in zip(lights,fx['lights']):
        for axis,v in enumerate(CI.to_3x3()@Vector(item['position'])):put(obj,'location',axis,frame,v)
        for axis,v in enumerate(item['color']):put(obj.data,'color',axis,frame,v)
        put(obj.data,'energy',0,frame,item['energy']*40.)
        obj['preview_energy_scale']=40.;obj['godot_energy_unit_note']='Recorded light energy scaled for Blender preview; no photometric/pixel parity claim.'
    for tree,path in signal_sockets:put(tree,path,0,frame,fx['hardware_gain'])
assert not missing,sorted(missing)
# Bulk curves avoid millions of per-key scene dependency updates.
curve_count=0;key_count=0
for datablock,channels in tracks.items():
    datablock.animation_data_clear();datablock.animation_data_create();action=bpy.data.actions.new('FRevision_'+datablock.name);datablock.animation_data.action=action
    for (path,index),items in channels.items():
        reduced=[item for i,item in enumerate(items) if i in [0,len(items)-1] or not (items[i-1][1]==item[1]==items[i+1][1])]
        fc=action.fcurve_ensure_for_datablock(datablock,path,index=index);fc.keyframe_points.add(len(reduced))
        fc.keyframe_points.foreach_set('co',[v for item in reduced for v in item])
        for key in fc.keyframe_points:key.interpolation='CONSTANT' if path.startswith('hide_') else 'LINEAR'
        fc.update();curve_count+=1;key_count+=len(reduced)
scene['animation_source']='revision_20260911/full_take/physical_take.json; recorded poses, exact field billboard transforms/gain and fitted engraved meshes'
scene['effect_scope']='Mechanical/UI 30Hz; optical/field15Hz samples with linear interpolation. Dedicated atlas planes and solid parts. Blender preview lights use energy scale40; hardware optical UV chase/post-processing are not pixel-identical.'
scene['status']='Isolated F revision bake. Awaiting pose/geometry/visual/native validation; not promoted.'
scene.frame_set(1);bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
assert sha(ORIGINAL)==original_hash
report={'frames':scene.frame_end,'fps':take['fps'],'fx_capture_fps':15,'curves':curve_count,'keys':key_count,'animated_datablocks':len(tracks),'glyph_vertices':glyph_vertices,'field_objects':len(fxcol.objects),'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256'],'controls_sha256':take['controls_sha256'],'source_sha256':sha(TARGET),'original_source_sha256':original_hash,'original_preserved':True,'scope':scene['effect_scope'],'accepted':False}
(OUT/'candidate_bake.json').write_text(json.dumps(report,indent=2)+'\n');print('F_REVISION_BAKED',json.dumps(report),flush=True)
