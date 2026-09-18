"""Read the current mouth's attachment geometry for shell fitting, without edits."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/part_b_shell';OUT.mkdir(parents=True,exist_ok=True)
spec=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];inverse=mouth.matrix_world.inverted();meshes=[o for o in bpy.data.objects if o.type=='MESH']
layout=json.loads((ROOT/'app'/spec['music_optics_layout'].removeprefix('res://')).read_text())
assert layout['mouth_component_sha256']==spec['component_sha256']
assert hashlib.sha256((ROOT/layout['source']).read_bytes()).hexdigest()==layout['source_sha256']
with bpy.data.libraries.load(str(ROOT/layout['source']),link=False) as (src,dst):dst.objects=[name for name in src.objects if name.startswith('I_')]
loaded=[o for o in dst.objects if o is not None]
for o in loaded:bpy.context.collection.objects.link(o)
optics=next(o for o in loaded if o.name=='I_MusicOptics');optics.parent=mouth
optical_sheet=next(o for o in loaded if o.name==layout['sheet'])
optical_hardware=[o for o in loaded if o.type=='MESH' and o!=optical_sheet]
meshes.extend(optical_hardware);bpy.context.view_layer.update()
def points(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
    values=np.array([tuple(inverse@e.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear();return values
def bounds(values):
    return {'min':values.min(axis=0).tolist(),'max':values.max(axis=0).tolist(),'maximum_radius_xy':float(np.linalg.norm(values[:,:2],axis=1).max())}
interfaces={}
for o in meshes:
    if any(token in o.name for token in ['PorcelainUpper','PorcelainLower','EyelidFixedCarrier','RearMountFlange','DiaphragmFixedSeat','HeadAcousticNeck']):interfaces[o.name]=bounds(points(o))
states=[]
for frame,label in [(1,'rest'),(103,'opening_middle'),(181,'open'),(217,'source_pressure_peak'),(433,'closed_again')]:
    scene.frame_set(frame);bpy.context.view_layer.update();all_points=np.concatenate([points(o) for o in meshes])
    states.append({'frame':frame,'label':label,**bounds(all_points)})
result={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'optics_source_sha256':layout['source_sha256'],'optics_component_sha256':layout['component_sha256'],'base_sha256':hashlib.sha256((ROOT/'app/assets/helios_model.glb').read_bytes()).hexdigest(),'coordinate_system':'Current mouth-local Blender coordinates. Front is -Z; image-up is +Y. glTF conversion is (x,z,-y), giving front -Y and image-up -Z. This is not yet the full app world frame.','mouth_world_matrix':[list(row) for row in mouth.matrix_world],'fixed_interfaces':interfaces,'optical_hardware':{o.name:bounds(points(o)) for o in optical_hardware},'optical_display_surface':bounds(points(optical_sheet)),'sampled_whole_mouth_bounds':states,'scope':'Actual evaluated attachment/reference bounds including physical optics in five source states, clamps closed. Nonphysical staff surface reported separately; outgoing VFX envelope not included. Whole-conch placement/scale remains unlocked. Not a swept collision envelope, manufacturing dimensions or a match score against generated art.'}
(OUT/'mouth_attachment_reference.json').write_text(json.dumps(result,indent=2)+'\n');print('I_MOUTH_ATTACHMENT_REFERENCE',len(interfaces),len(states),flush=True)
