"""Actual triangle intersections for source geometry driven by runtime take.

Records against one another, support banks, arms, and the independent AI head.
Designed rest contacts are not counted as clearance; unexpected crossings are.
"""
import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator.json').read_text())
take=json.loads((ROOT/'review/G_optical_curator/curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:
    assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator.{ext}').read_bytes()).hexdigest()==take[key],'Stale motion take: '+ext
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_optical_curator.blend'))
for obj in bpy.data.objects:obj.animation_data_clear()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
spec=data['record_player'];groups={}
names=spec['records']+spec['cradles']+[spec['upper_arm'],spec['forearm'],spec['wrist'],spec['tonearm']]
for name in names:
    root=bpy.data.objects[name];groups[name]=[o for o in root.children_recursive if o.type in ['MESH','CURVE','FONT']]
def bvh(objects,deps):
    verts=[];faces=[]
    for obj in objects:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();start=len(verts)
        verts.extend(ev.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(start+i for i in tri.vertices) for tri in mesh.loop_triangles);ev.to_mesh_clear()
    lo=[min(v[k] for v in verts) for k in range(3)];hi=[max(v[k] for v in verts) for k in range(3)]
    return BVHTree.FromPolygons(verts,faces,all_triangles=True),lo,hi
hits={};samples=0;cache={}
for sample in take['samples'][::8]:
    if sample['explosion']>.001:continue
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:obj.matrix_basis=pose(p)
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();info={};samples+=1
    for name,objects in groups.items():
        signature=tuple(tuple(v for row in obj.matrix_world for v in row) for obj in objects)
        if name not in cache or cache[name][0]!=signature:cache[name]=(signature,bvh(objects,deps))
        info[name]=cache[name][1]
    if samples%50==0:print('SWEEP_PROGRESS',samples,'crossing_pairs',len(hits),flush=True)
    for i,record in enumerate(spec['records']):
        a,low,high=info[record]
        for other in names:
            if other==record or other==spec['cradles'][i]:continue
            if other in spec['records'] and spec['records'].index(other)<i:continue
            b,lo,hi=info[other]
            if any(high[k]<lo[k] or low[k]>hi[k] for k in range(3)):continue
            pairs=a.overlap(b)
            if pairs:
                key=record+' / '+other
                if key not in hits:
                    detail=[]
                    for obj in groups[other]:
                        tree,_,_=bvh([obj],deps)
                        if a.overlap(tree):detail.append(obj.name)
                    hits[key]={'record':record,'other':other,'first_frame':sample['frame'],'stage':sample['state']['stage'],'samples':0,'max_triangle_pairs':0,'other_surfaces':detail}
                hits[key]['samples']+=1;hits[key]['max_triangle_pairs']=max(hits[key]['max_triangle_pairs'],len(pairs))
report={'all_clear':not hits,'samples':samples,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256'],'scope':'six records against other records, other cradles, arm links, AI wrist and reader assembly; evaluated meshes/curves/text; own cradle designed contact excluded','intersections':list(hits.values())}
(ROOT/'review/G_optical_curator/sweep_report.json').write_text(json.dumps(report,indent=2));print('CURATOR_SWEEP',json.dumps(report),flush=True)
if hits:raise RuntimeError('Record transfer geometry gate failed')
