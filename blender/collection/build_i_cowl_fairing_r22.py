"""Apply the solved transition and complete 03/04 solid metal returns."""
import bpy,json,hashlib,struct,sys,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));from i_cowl_edge_finish import finish
OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';s=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json').read_text());solution=json.loads((OUT/'solution.json').read_text());problem=json.loads((OUT/'problem.json').read_text());perimeters=json.loads((ROOT/'review/I_refinement/nautilus_r1/cowl_normals_r22/perimeter_probe.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/s['source'])==s['source_sha256']==solution['source_sha256']==problem['source_sha256']==perimeters['source_sha256']
TARGET=ROOT/'blender/collection/I_nautilus_cowl_fairing_r22.blend';COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_cowl_fairing_r22.glb'
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-cowl-fairing-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];allowed={'IN1_PorcelainPanel_%02d'%n for n in [1,3,4,5,6]}
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world],o.parent.name if o.parent else None]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed};fixed=[]
for row,original in zip(solution['meshes'],problem['meshes']):
    assert row['mesh']==original['mesh'];o=bpy.data.objects[row['mesh']];inverse=o.matrix_world.inverted();assert len(o.data.vertices)==len(row['vertices']);old=[v.co.copy()for v in o.data.vertices]
    for index,(v,p,is_free)in enumerate(zip(o.data.vertices,row['vertices'],original['free'])):
        if is_free:v.co=inverse@Vector(p)
        else:assert list(p)==original['vertices'][index]
    o.data.update();o.data.normals_split_custom_set([(0.,0.,0.)]*len(o.data.loops))
    assert all(tuple(v.co)==tuple(old[i])for i,v in enumerate(o.data.vertices)if not original['free'][i]);fixed.append({'mesh':o.name,'fixed_vertices':len(old)-sum(original['free']),'fixed_vertices_exact':True,'maximum_world_displacement':row['maximum_displacement']})
rims=[]
for number in [3,4]:
    name='IN1_PorcelainPanel_%02d'%number;row=next(r for r in perimeters['rows']if r['mesh']==name);loops=[c for c in row['chains']if c['closed']and c['length']>1.];assert len(loops)==1
    rims.append(finish(bpy.data.objects[name],loops[0],bpy.data.objects['IAM_MODULE'].matrix_world))
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
r={**s,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':s['source_sha256'],'surface_finish':{'fairing':fixed,'rims':rims,'solver':solution.get('solver','cartesian_biharmonic'),'problem_sha256':sha(OUT/'problem.json'),'solution_sha256':sha(OUT/'solution.json'),'protected_geometry':True,'art':'production/I_refinement/nautilus_r1/mouth_finish_r21/mouth_junction_close_open_r1.png'},'status':'constrained_fairing_and_two_complete_rims_candidate_checks_pending'}
used=OUT/'inputs'/r['source_sha256'][:12];used.mkdir(parents=True,exist_ok=True)
for name in ['problem.json','solution.json','mouth_obstacle.json']:
    if (OUT/name).exists():shutil.copy2(OUT/name,used/name)
r['cowl_finish']={**s['cowl_finish'],'modified_meshes':sorted(allowed|{'IN1_FixedMouthCheek05'})};(OUT/'build.json').write_text(json.dumps(r,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'fixed_vertices':fixed},indent=2)+'\n');print('COWL_FAIRING_SOURCE',r['source_sha256'],json.dumps(rims),flush=True)
