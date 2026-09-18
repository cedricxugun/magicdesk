"""Rotate the candidate and its original disc together against the real machine."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
stem=ROOT/'app/assets/collection/models/G_optical_curator_observatory_candidate'
data=json.loads(stem.with_suffix('.json').read_text());take=json.loads((ROOT/'review/G_optical_curator/observatory_r2/app/curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256(stem.with_suffix('.'+ext).read_bytes()).hexdigest()==take[key],'Stale candidate take'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/data['source_blend']))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
for obj in bpy.data.objects:obj.animation_data_clear()
sample=next(s for s in take['samples'] if s['state']['stage']=='playing' and s['state']['loaded_index']==0)
for name,p in sample['poses'].items():
    obj=bpy.data.objects.get(name)
    if obj:obj.matrix_basis=pose(p)
content=bpy.data.objects[data['g_archive']['contents'][0]['root']]
for obj in [content]+list(content.children_recursive):obj.hide_set(False);obj.hide_viewport=False
parts={p['name'] for p in data['parts']};excluded={c['root'] for c in data['g_archive']['contents']}
def members(root,prune=False):
    result=[]
    def walk(node):
        if prune and node!=root and (node.name in parts or node.name in excluded):return
        if node.type in ['MESH','CURVE','FONT']:result.append(node)
        for child in node.children:walk(child)
    walk(root);return result
groups={name:members(bpy.data.objects[name],True) for name in parts};groups={k:v for k,v in groups.items() if v}
def mesh_tree(objects):
    deps=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
    for obj in objects:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();start=len(verts)
        verts.extend(ev.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(start+i for i in t.vertices) for t in mesh.loop_triangles);ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts,faces,all_triangles=True),[min(v[k] for v in verts) for k in range(3)],[max(v[k] for v in verts) for k in range(3)]
platter=bpy.data.objects[data['record_player']['platter']];record=bpy.data.objects[data['record_player']['records'][0]]
platter_home=platter.matrix_basis.copy();record_home=record.matrix_basis.copy();hits=[];cache={}
for i in range(24):
    angle=i*math.tau/24
    platter.matrix_basis=platter_home@Matrix.Rotation(angle,4,'Z');record.matrix_basis=record_home@Matrix.Rotation(angle,4,'Z')
    bpy.context.view_layer.update();a,low,high=mesh_tree(members(content))
    for name,objects in groups.items():
        signature=tuple(tuple(x for row in obj.matrix_world for x in row) for obj in objects)
        if name not in cache or cache[name][0]!=signature:cache[name]=(signature,mesh_tree(objects))
        b,lo,hi=cache[name][1]
        if any(high[k]<lo[k] or hi[k]<low[k] for k in range(3)):continue
        pairs=a.overlap(b)
        if pairs:hits.append({'angle':angle,'other':name,'triangle_pairs':len(pairs)})
report={'passed':not hits,'rotation_samples':24,'collisions':hits,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256'],'scope':'Whole observatory versus actual upper-machine parts and records through one display turn; own internal contacts are not certified'}
(ROOT/'review/G_optical_curator/observatory_r2/external_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('OBSERVATORY_EXTERNAL_CLEARANCE',json.dumps(report),flush=True)
assert report['passed'],'Observatory intersects surrounding machine'
