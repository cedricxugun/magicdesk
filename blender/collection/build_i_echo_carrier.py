"""Standalone authored shallow optical wavefront carrier; never rebuilds the mouth."""
import bpy,math,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/echo_r2';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'blender/collection/I_echo_wavefront.blend'
if source.exists():
    previous=json.loads((OUT/'carrier.json').read_text());digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest==previous['source_sha256'],'Unrecorded wavefront edits'
    (source.parent/'checkpoints'/('I-echo-wavefront-'+digest[:12]+'.blend')).write_bytes(source.read_bytes())
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[];faces=[];uv=[];around=192;rows=24
for j in range(rows+1):
    v=j/rows;r=.40+.70*v
    for i in range(around+1):
        u=i/around;a=u*math.tau;verts.append((r*math.cos(a),r*math.sin(a),.12*(r*r-1)));uv.append((u,v))
for j in range(rows):
    for i in range(around):
        a=j*(around+1)+i;faces.append((a,a+1,a+around+2,a+around+1))
m=bpy.data.meshes.new('AcousticWavefrontMesh');m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new('I_EchoWavefront',m);bpy.context.collection.objects.link(o)
layer=m.uv_layers.new(name='WaveCrestUV')
for f in m.polygons:
    f.use_smooth=True
    for li in f.loop_indices:layer.data[li].uv=uv[m.loops[li].vertex_index]
bpy.ops.wm.save_as_mainfile(filepath=str(source))
bpy.context.view_layer.objects.active=o;o.select_set(True);component=ROOT/'app/assets/collection/art/I/echo_r2/wavefront.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'carrier.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'vertices':len(verts),'scope':'Open optical carrier with actual authored UV/curvature, not a physical solid. Sized and oriented in the runtime against the actual mouth.'},indent=2)+'\n')
