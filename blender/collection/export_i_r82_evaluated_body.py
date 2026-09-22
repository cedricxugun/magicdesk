"""Export the evaluated static upper body, including real bevels and normals.
The functional morph-driven mouth remains a separate, already verified asset.
"""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];BASE=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
old=json.loads((BASE/'installed_r3/build.json').read_text());OUT=BASE/'installed_r4';OUT.mkdir(exist_ok=True)
COMP=R/'app/assets/collection/components/I_r82_music_body_r4.glb';assert not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];objects=[o for o in root.children_recursive if o.type in ['MESH','CURVE']]
receipts=[]
for o in objects:
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 n=len(me.vertices);ids=sorted(set([0,n-1]+[int((n-1)*k/7)for k in range(8)]))
 if o.type=='MESH' and n>len(o.data.vertices):ids=sorted(set(ids+[len(o.data.vertices),n-2]))
 receipts.append({'name':o.name,'kind':o.type,'raw_vertices':len(o.data.vertices)if o.type=='MESH'else None,'evaluated_vertices':n,'evaluated_triangles':len(me.loop_triangles),'modifiers':[m.type for m in o.modifiers if m.show_render],'local_samples_blender':[list(me.vertices[i].co)for i in ids]})
 ev.to_mesh_clear()
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=True,export_extras=True,export_tangents=True)
report={**old,'component':COMP.relative_to(R).as_posix(),'component_sha256':hashlib.sha256(COMP.read_bytes()).hexdigest(),'parent_component':old['component'],'export_settings':{'apply_static_modifiers':True,'export_morph':False,'export_animations':False,'export_tangents':True},'scope':'Same editable source and body geometry, correctly exported with evaluated bevel/normal modifiers. Morph-driven acoustic core remains separate. Geometry equivalence, runtime and art review must use this component, not omitted-modifier r3.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'evaluated_geometry.json').write_text(json.dumps({'source':old['source'],'source_sha256':old['source_sha256'],'objects':receipts,'scope':'Independent evaluated-source triangle counts and sampled local vertices, including added bevel vertices.'},indent=2)+'\n')
print('R83_EVALUATED_BODY',len(receipts),sum(bool(r['modifiers'])for r in receipts),flush=True)
