"""Finish the complete current front hood edge, preserving the rest of R29."""
import bpy,json,hashlib,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));from i_cowl_edge_finish import finish
graded='--graded' in sys.argv;adaptive='--adaptive' in sys.argv;planar='--planar' in sys.argv;suffix='front_cowl_rim_r33'if planar else 'front_cowl_rim_r32'if adaptive else 'front_cowl_rim_r31'if graded else 'front_cowl_rim_r30'
OUT=ROOT/'review/I_refinement/nautilus_r1'/suffix;OUT.mkdir(parents=True,exist_ok=True);parent=ROOT/'review/I_refinement/nautilus_r1/uniform_precision_r29';s=json.loads((parent/'build.json').read_text());p=json.loads((parent/'perimeter_probe.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']==p['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];name='IN1_PorcelainPanel_05'
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world]]
before={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name!=name};row=next(r for r in p['rows']if r['mesh']==name);loops=[c for c in row['chains']if c['closed']and c['length']>1];assert len(loops)==1
rim=finish(bpy.data.objects[name],loops[0],bpy.data.objects['IAM_MODULE'].matrix_world,clean_precision_edges=True,clamp_overlap=False,graded_cheek_edge=graded,adaptive_radius=adaptive,planar_cheek_retopology=planar)
assert all(fingerprint(bpy.data.objects[n])==v for n,v in before.items())
source=ROOT/'blender/collection'/('I_nautilus_'+suffix+'.blend');component=ROOT/'app/assets/collection/components'/('I_nautilus_'+suffix+'.glb');assert not source.exists(),'Preserve prior candidate and reports before rebuilding'
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'front_cowl_rim':rim,'status':'front_hood_complete_edge_candidate_checks_pending'};d['cowl_finish']={**s['cowl_finish'],'modified_meshes':[name]};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(before),'modified_meshes':[name]},indent=2)+'\n');print('FRONT_COWL_RIM_SOURCE',d['source_sha256'],json.dumps(rim),flush=True)
