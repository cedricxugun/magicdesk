"""Triangle checks for the actual separated service assemblies.

Initial press-fit/contact pairs are reported separately. A new crossing pair
during motion or any crossing pair at full separation fails this check.
"""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator.json').read_text())
take_path=ROOT/'review/G_optical_curator/curator_take.json'
if '--service-only' in sys.argv:take_path=ROOT/'review/G_optical_curator/service/service_take.json'
take=json.loads(take_path.read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator.{ext}').read_bytes()).hexdigest()==take[key],'Stale take'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_optical_curator.blend'))
for obj in bpy.data.objects:obj.animation_data_clear()
names=[p['name'] for p in data['parts']];parts=set(names);excluded={c['root'] for c in data['g_archive']['contents']}
def members(root):
    result=[]
    def walk(node):
        if node!=root and (node.name in parts or node.name in excluded):return
        if node.type in ['MESH','CURVE','FONT']:result.append(node)
        for child in node.children:walk(child)
    walk(root);return result
groups={name:members(bpy.data.objects[name]) for name in names};groups={k:v for k,v in groups.items() if v}
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
cache={}
def geometry(objects,deps):
    verts=[];faces=[]
    for obj in objects:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();start=len(verts)
        verts.extend(ev.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(start+i for i in t.vertices) for t in mesh.loop_triangles);ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts,faces,all_triangles=True),[min(v[k] for v in verts) for k in range(3)],[max(v[k] for v in verts) for k in range(3)]
def inspect(sample):
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:obj.matrix_basis=pose(p)
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();info={}
    for name,objects in groups.items():
        signature=tuple(tuple(v for row in o.matrix_world for v in row) for o in objects)
        if name not in cache or cache[name][0]!=signature:cache[name]=(signature,geometry(objects,deps))
        info[name]=cache[name][1]
    hits={}
    keys=list(info)
    for i,first in enumerate(keys):
        a,lo,hi=info[first]
        for second in keys[i+1:]:
            b,low,high=info[second]
            if any(hi[k]<low[k] or high[k]<lo[k] for k in range(3)):continue
            overlap=a.overlap(b)
            if overlap:hits[first+' / '+second]=len(overlap)
    return hits
start=next(i for i,s in enumerate(take['samples']) if s['explosion']>.001)
baseline=inspect(take['samples'][start-1]);new={};end={};count=0
samples=[s for s in take['samples'][start:] if s['explosion']>.001]
for sample in samples[::3]+[max(samples,key=lambda s:s['explosion'])]:
    hits=inspect(sample);count+=1
    for pair,triangles in hits.items():
        if pair not in baseline and pair not in new:new[pair]={'frame':sample['frame'],'explosion':sample['explosion'],'triangle_pairs':triangles}
    if sample['explosion']>.999:end=hits
    if count%15==0:print('SERVICE_SWEEP_PROGRESS',count,'new_pairs',len(new),flush=True)
report={'passed':not new and not end,'samples':count,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256'],'initial_contact_pairs':baseline,'new_crossings':new,'full_separation_crossings':end,'scope':'Every separate assembly; initial contacts are not a certificate of internal fabrication clearance'}
(ROOT/'review/G_optical_curator/service/sweep_report.json').write_text(json.dumps(report,indent=2));print('CURATOR_SERVICE_SWEEP',json.dumps(report),flush=True)
if not report['passed']:raise RuntimeError('Service assembly collision gate failed')
