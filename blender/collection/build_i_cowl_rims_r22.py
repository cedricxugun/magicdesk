"""Retain the useful closed-cover returns without the rejected fairing trial."""
import bpy,json,hashlib,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));from i_cowl_edge_finish import finish
OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_rims_r22';OUT.mkdir(parents=True,exist_ok=True);s=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json').read_text());p=json.loads((ROOT/'review/I_refinement/nautilus_r1/cowl_normals_r22/perimeter_probe.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']==p['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];allowed={'IN1_PorcelainPanel_03','IN1_PorcelainPanel_04'}
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world]]
before={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in allowed};rims=[]
for name in sorted(allowed):
    row=next(r for r in p['rows']if r['mesh']==name);chain=next(c for c in row['chains']if c['closed']and c['length']>1.);rims.append(finish(bpy.data.objects[name],chain,bpy.data.objects['IAM_MODULE'].matrix_world))
assert all(fingerprint(bpy.data.objects[n])==value for n,value in before.items())
source=ROOT/'blender/collection/I_nautilus_cowl_rims_r22.blend';component=ROOT/'app/assets/collection/components/I_nautilus_cowl_rims_r22.glb';bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'surface_finish':{'rims':rims,'modified_meshes':sorted(allowed),'fairing':'not incorporated; original neck requires clean reconstruction','art':'production/I_refinement/nautilus_r1/mouth_finish_r21/mouth_junction_close_open_r1.png'},'status':'two_formed_returns_original_cowl_still_unfinished'};d['cowl_finish']={**s['cowl_finish'],'modified_meshes':sorted(allowed)}
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(before),'modified_meshes':sorted(allowed)},indent=2)+'\n');print('RIMS_ONLY_SOURCE',d['source_sha256'],flush=True)
