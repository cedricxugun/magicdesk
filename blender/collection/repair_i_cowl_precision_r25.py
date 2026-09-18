"""Stitch demonstrated neighboring precision contacts, bounded by one float32 ULP."""
import bpy,bmesh,json,hashlib,struct,sys,shutil
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];config_path=next((a.split('=',1)[1]for a in args if a.startswith('--config=')),None);config=json.loads((ROOT/config_path).read_text())if config_path else {};PARENT=(ROOT/config.get('base_report','review/I_refinement/nautilus_r1/clean_cowl_r24/build.json')).parent;OUT=ROOT/config.get('out','review/I_refinement/nautilus_r1/cowl_precision_r25');OUT.mkdir(parents=True,exist_ok=True);s=json.loads((PARENT/'build.json').read_text());raw=json.loads((PARENT/'self_contacts.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']==raw['source_sha256'];assert not config.get('expected_parent_source_sha256')or s['source_sha256']==config['expected_parent_source_sha256']
target_path=ROOT/config.get('source','blender/collection/I_nautilus_cowl_precision_r25.blend')
if target_path.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(target_path)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(target_path,target_path.parent/'checkpoints'/('I-cowl-precision-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];names=[r['mesh']for r in raw['rows']if r['contacts']]
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world]]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in names};changes=[]
for row in raw['rows']:
    if not row['contacts']:continue
    o=bpy.data.objects[row['mesh']];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();seeds={bm.verts[i]for r in row['contacts']for face in r['vertices']for i in face};region=seeds|{e.other_vert(v)for v in seeds for e in v.link_edges};positions={v:o.matrix_world@v.co for v in region}
    def ulp(p):return float(np.spacing(np.float32(max(abs(x)for x in p))))
    parents={v:v for v in region};members={v:{v}for v in region}
    def representative(v):
        if parents[v]!=v:parents[v]=representative(parents[v])
        return parents[v]
    edges=[e for e in bm.edges if all(v in region for v in e.verts)and (positions[e.verts[0]]-positions[e.verts[1]]).length<=max(ulp(positions[v])for v in e.verts)]
    for e in edges:
        a,b=[representative(v)for v in e.verts]
        if a==b:continue
        chosen=next((r for r in [a,b]if all((positions[v]-positions[r]).length<=ulp(positions[r])for v in members[a]|members[b])),None)
        if chosen is None:continue
        other=b if chosen==a else a;parents[other]=chosen;members[chosen]|=members[other]
    targets={v:representative(v)for v in region if representative(v)!=v};coordinates={v:v.co.copy()for v in set(targets.values())};witnesses=[{'from_world':list(positions[v]),'to_world':list(positions[t]),'distance':(positions[v]-positions[t]).length,'float32_ulp':ulp(positions[t])}for v,t in targets.items()];assert all(w['distance']<=w['float32_ulp']for w in witnesses)
    if targets:
        bmesh.ops.weld_verts(bm,targetmap=targets)
        for v,co in coordinates.items():
            if v.is_valid:v.co=co
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts)
    bm.to_mesh(o.data);bm.free();o.data.update();o.data.normals_split_custom_set([(0.,0.,0.)]*len(o.data.loops));changes.append({'mesh':o.name,'welded_vertices':len(targets),'maximum_world_displacement':max((w['distance']for w in witnesses),default=0.),'witnesses':witnesses})
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
source=ROOT/config.get('source','blender/collection/I_nautilus_cowl_precision_r25.blend');component=ROOT/config.get('component','app/assets/collection/components/I_nautilus_cowl_precision_r25.glb');bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'precision_stitching':changes,'status':'bounded_precision_stitch_candidate_checks_pending'};rebuilt=config.get('all_rebuilt_meshes',['IN1_PorcelainPanel_01','IN1_PorcelainPanel_06']);d['clean_cowl']={**s['clean_cowl'],'modified_meshes':rebuilt};d['cowl_finish']={**s['cowl_finish'],'modified_meshes':rebuilt};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'changes':changes},indent=2)+'\n');print('PRECISION_STITCH_SOURCE',d['source_sha256'],[(r['mesh'],r['welded_vertices'],r['maximum_world_displacement'])for r in changes],flush=True)
