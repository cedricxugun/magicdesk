"""Surgical cleanup of the already built R13, preserving every other mesh."""
import bpy,bmesh,json,hashlib,sys,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_boolean_residue as residue
OUT=ROOT/'review/I_refinement/nautilus_r1/throat_sockets_r13';spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];component=ROOT/spec['component'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(source)==spec['source_sha256']
topology=json.loads((OUT/'topology_check.json').read_text());assert topology['source_sha256']==spec['source_sha256']
allowed=set(spec['front_sockets']['audit_socket_meshes']+spec['front_sockets']['modified_meshes'])
targets=[r['name'] for r in topology['failures'] if r['name'] in allowed and (r['nonmanifold_edges'] or r['tiny_faces'])];assert targets
archive=OUT/'iterations'/spec['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
saved_source=source.parent/'checkpoints'/('I-throat-sockets-'+spec['source_sha256'][:12]+'.blend');shutil.copy2(source,saved_source)
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return d.hexdigest(),[list(r) for r in o.matrix_world]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in targets};rows=[]
for name in targets:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);fix=residue.repair(bm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges);tiny=sum(f.calc_area()<1e-12 for f in bm.faces);assert not bad and not tiny,(name,bad,tiny)
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    assert bm.calc_volume(signed=True)>0,(name,'Zero-volume closed solid');bm.to_mesh(o.data);bm.free();rows.append({'mesh':name,**fix})
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
previous=spec['source_sha256'];spec['source_sha256']=sha(source);spec['component_sha256']=sha(component);spec['boolean_residue_repair']={'parent_source_sha256':previous,'saved_source':str(saved_source.relative_to(ROOT)),'targets':rows,'other_meshes_preserved':len(protected)}
(OUT/'build.json').write_text(json.dumps(spec,indent=2)+'\n');protection=json.loads((OUT/'protected_geometry.json').read_text());protection['source_sha256']=spec['source_sha256'];protection['residue_repair_targets']=targets;(OUT/'protected_geometry.json').write_text(json.dumps(protection,indent=2)+'\n')
print('R13_RESIDUE_REPAIRED',spec['source_sha256'],json.dumps(rows),flush=True)
