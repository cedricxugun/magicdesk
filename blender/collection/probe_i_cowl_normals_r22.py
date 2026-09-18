"""Same geometry, automatic-normal control for the four R21 cowl skins."""
import bpy,json,hashlib,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_normals_r22';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
    h=hashlib.sha256();o.data.calc_loop_triangles()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for t in o.data.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world]]
before={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'};rows=[]
for name in s['cowl_finish']['modified_meshes']:
    o=bpy.data.objects[name];old=[n.vector.copy()for n in o.data.corner_normals]
    o.data.normals_split_custom_set([(0.,0.,0.)]*len(o.data.loops));o.data.update()
    values=[a.angle(b.vector,0.)for a,b in zip(old,o.data.corner_normals)]
    rows.append({'mesh':name,'mean_normal_change_radians':sum(values)/len(values),'maximum_normal_change_radians':max(values)})
assert all(fingerprint(bpy.data.objects[n])==v for n,v in before.items())
source=ROOT/'blender/collection/I_nautilus_cowl_normals_r22.blend';component=ROOT/'app/assets/collection/components/I_nautilus_cowl_normals_r22.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'normal_comparison':{'modified_meshes':s['cowl_finish']['modified_meshes'],'rows':rows,'all_source_render_triangles_and_positions_preserved':True},'status':'automatic_normal_diagnostic_not_art_acceptance'}
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('NORMAL_PROBE_SOURCE',d['source_sha256'],flush=True)
