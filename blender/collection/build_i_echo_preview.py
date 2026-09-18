"""Compose authored outgoing/return assets over the recorded pneumatic source."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/r2'
source=ROOT/'blender/collection/I_pneumatic_r2.blend';target=ROOT/'blender/collection/I_echo_r2.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
take=json.loads((OUT/'pneumatic_take.json').read_text());mouth=bpy.data.objects['IH1_Mouth'];upper=bpy.data.objects['IH1_UPPER']
collection=bpy.data.collections.new('I_AUTHORED_ECHO_PREVIEW');scene.collection.children.link(collection)
atlas=bpy.data.images.load(str(ROOT/'app/assets/collection/art/I/acoustic_atlas_r1.png'),check_existing=True)
def material(name,tile,color,flow=False):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
    uv=nt.nodes.new('ShaderNodeTexCoord');separate=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(uv.outputs['UV'],separate.inputs[0])
    head=nt.nodes.new('ShaderNodeValue');head.name='PacketHead';head.outputs[0].default_value=1.
    gain=nt.nodes.new('ShaderNodeValue');gain.name='OpticalGain';gain.outputs[0].default_value=0.
    def mathnode(op,a,b=None):
        n=nt.nodes.new('ShaderNodeMath');n.operation=op
        if hasattr(a,'node'):nt.links.new(a,n.inputs[0])
        else:n.inputs[0].default_value=a
        if b is not None:
            if hasattr(b,'node'):nt.links.new(b,n.inputs[1])
            else:n.inputs[1].default_value=b
        return n.outputs[0]
    u=separate.outputs['X'];window=None
    if flow:
        distance=mathnode('SUBTRACT',u,head.outputs[0]);u=mathnode('ADD',mathnode('MULTIPLY',distance,4.),.5)
        window=mathnode('LESS_THAN',mathnode('ABSOLUTE',distance),.125)
    vector=nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(mathnode('ADD',mathnode('MULTIPLY',u,.5),tile[0]*.5),vector.inputs[0])
    nt.links.new(mathnode('ADD',mathnode('MULTIPLY',separate.outputs['Y'],.5),(1-tile[1])*.5),vector.inputs[1])
    texture=nt.nodes.new('ShaderNodeTexImage');texture.image=atlas;texture.extension='CLIP';nt.links.new(vector.outputs[0],texture.inputs[0])
    mono=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(texture.outputs['Color'],mono.inputs[0])
    mask=mathnode('MULTIPLY',mono.outputs[0],texture.outputs['Alpha']);mask=mathnode('MULTIPLY',mask,gain.outputs[0])
    if window:mask=mathnode('MULTIPLY',mask,window)
    transparent=nt.nodes.new('ShaderNodeBsdfTransparent');emission=nt.nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(*color,1);emission.inputs['Strength'].default_value=1.5
    mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(mask,mix.inputs[0]);nt.links.new(transparent.outputs[0],mix.inputs[1]);nt.links.new(emission.outputs[0],mix.inputs[2])
    output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(mix.outputs[0],output.inputs[0])
    return mat,gain,head
def mesh(name,verts,faces,uv,mat):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.materials.append(mat);layer=data.uv_layers.new(name='AuthoredUV')
    for p in data.polygons:
        for li in p.loop_indices:layer.data[li].uv=uv[data.loops[li].vertex_index]
    obj=bpy.data.objects.new(name,data);collection.objects.link(obj)
    obj.visible_diffuse=False;obj.visible_glossy=False;obj.visible_shadow=False;obj.visible_transmission=False
    return obj
events=[e for sample in take['samples'] for e in sample['events']]
waves=[];returns=[];receivers=[]
for index,event in enumerate(events):
    if event['kind']=='outgoing':
        mat,gain,head=material('I_Outgoing_'+str(index),(0,0),(1.,.38,.065))
        verts=[];uv=[];faces=[];n=24
        for y in range(n+1):
            for x in range(n+1):
                a=x/n*2-1;b=y/n*2-1;verts.append((a,b,.04*(a*a+b*b)));uv.append((x/n,y/n))
        for y in range(n):
            for x in range(n):a=y*(n+1)+x;faces.append((a,a+1,a+n+2,a+n+1))
        waves.append((event,mesh('I_OutgoingPacket_'+str(index),verts,faces,uv,mat),gain))
    elif event['kind']=='return':
        mat,gain,head=material('I_Return_'+str(index),(1,0),(.12,.54,1.),True)
        conductor=sorted([o for o in upper.children_recursive if o.type=='CURVE' and 'BrassReturnConductor' in o.name],key=lambda o:o.name)[-1]
        points=[conductor.matrix_world@Vector(p.co[:3]) for p in conductor.data.splines[0].points]
        lengths=[0.]
        for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+(b-a).length)
        verts=[];uv=[];faces=[]
        for j,p in enumerate(points):
            tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized()
            normal=Vector((0,-1,0))-tangent*tangent.dot(Vector((0,-1,0)))
            if normal.length<.1:normal=Vector((0,0,1))-tangent*tangent.z
            normal.normalize();side=normal.cross(tangent).normalized()
            for sign in [-1,1]:verts.append(p+normal*.010+side*sign*.023);uv.append((lengths[j]/lengths[-1],(sign+1)/2))
            if j<len(points)-1:a=2*j;faces.append((a,a+1,a+3,a+2))
        returns.append((event,mesh('I_ReturnPacket_'+str(index),verts,faces,uv,mat),gain,head))
        receiver_mat,receiver_gain,_=material('I_Receiver_'+str(index),(0,0),(.12,.54,1.))
        receiver=mesh('I_ReceiverHalo_'+str(index),[(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)],receiver_mat)
        light_data=bpy.data.lights.new('I_ReceiverLight_'+str(index),'POINT');light_data.color=(.12,.54,1.);light_data.shadow_soft_size=.04
        receiver_light=bpy.data.objects.new(light_data.name,light_data);collection.objects.link(receiver_light);receiver_light.location=mouth.matrix_world@Vector((0,0,-.11))
        receivers.append((event,receiver,receiver_gain,light_data))
lamp=bpy.data.lights.new('I_EchoLocalLight','POINT');lamp.color=(1.,.38,.10);lamp.shadow_soft_size=.055
light=bpy.data.objects.new(lamp.name,lamp);collection.objects.link(light);light.location=mouth.matrix_world@Vector((0,0,-.14))
def envelope(age,duration):
    if age<0 or age>duration:return 0.
    t=age/duration;return math.sin(math.pi*t)**1.2
for sample in take['samples']:
    frame=sample['frame'];time=sample['time']+1/take['fps'];scene.frame_set(frame);global_gain=sample['state']['gain'];illumination=0.
    for event,obj,gain in waves:
        age=time-event['time'];progress=max(0.,min(1.,age/1.1));amount=event['gain']*envelope(age,1.1)*global_gain
        radius=(.34+.51*progress)/.82;obj.matrix_world=mouth.matrix_world@Matrix.Translation((0,0,-.14-.75*progress))@Matrix.Diagonal((radius,radius,radius,1.))
        obj.keyframe_insert('location',frame=frame);obj.keyframe_insert('rotation_euler',frame=frame);obj.keyframe_insert('scale',frame=frame)
        gain.outputs[0].default_value=amount;gain.outputs[0].keyframe_insert('default_value',frame=frame);illumination+=amount*8.
    for event,obj,gain,head in returns:
        age=time-(event['time']-.45);progress=max(0.,min(1.,age/.45));amount=event['gain']*envelope(age,.45)*global_gain
        gain.outputs[0].default_value=amount;gain.outputs[0].keyframe_insert('default_value',frame=frame);head.outputs[0].default_value=1.-progress;head.outputs[0].keyframe_insert('default_value',frame=frame);illumination+=amount*4.
    for event,obj,gain,receiver_light in receivers:
        age=time-event['time'];amount=event['gain']*envelope(age,.70)*global_gain
        radius=(.49+.035*math.exp(-max(0.,age)*7.))/.82
        obj.matrix_world=mouth.matrix_world@Matrix.Translation((0,0,-.119))@Matrix.Diagonal((radius,radius,radius,1.))
        obj.keyframe_insert('location',frame=frame);obj.keyframe_insert('rotation_euler',frame=frame);obj.keyframe_insert('scale',frame=frame)
        gain.outputs[0].default_value=amount;gain.outputs[0].keyframe_insert('default_value',frame=frame)
        receiver_light.energy=amount*4.;receiver_light.keyframe_insert('energy',frame=frame)
    lamp.energy=illumination;lamp.keyframe_insert('energy',frame=frame)
scene.frame_set(1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(target.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(target))
scene.render.resolution_x=1200;scene.render.resolution_y=1050;scene.cycles.samples=32
# Opaque camera-only background avoids mistaking unpremultiplied PNG edge RGB for visible light.
world=scene.world.node_tree;output=next(n for n in world.nodes if n.type=='OUTPUT_WORLD');original=output.inputs['Surface'].links[0].from_socket
light_path=world.nodes.new('ShaderNodeLightPath');flat=world.nodes.new('ShaderNodeBackground');flat.inputs['Color'].default_value=(.018,.021,.025,1);flat.inputs['Strength'].default_value=1.
mix=world.nodes.new('ShaderNodeMixShader');world.links.new(light_path.outputs['Is Camera Ray'],mix.inputs[0]);world.links.new(original,mix.inputs[1]);world.links.new(flat.outputs[0],mix.inputs[2]);world.links.new(mix.outputs[0],output.inputs['Surface']);scene.render.film_transparent=False
camera=scene.camera;camera.location=(.95,-6.2,3.55);camera.rotation_euler=(Vector((0,0,1.70))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=35
for frame,label in [(82,'charge'),(99,'outgoing'),(121,'return'),(226,'quiet')]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/('echo_'+label+'.png'));bpy.ops.render.render(write_still=True)
result={'source':str(target.relative_to(ROOT)),'source_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'pneumatic_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'atlas':'app/assets/collection/art/I/acoustic_atlas_r1.png','events':events,'scope':'Source-only authored outgoing meshes, returning conductor ribbon, arrival receiver halo and explicit local light driven by recorded pressure events. Review images use opaque camera background; source keeps transparent rendering. Not Godot/runtime integration or full visual acceptance.'}
(OUT/'echo_preview.json').write_text(json.dumps(result,indent=2)+'\n');print('I_ECHO_PREVIEW',json.dumps(result),flush=True)
