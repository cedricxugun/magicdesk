"""Independent BVH sweep of runtime-exported physical geometry and transforms."""
import json,collections,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/F_complete/revision_20260911/installation'
source=OUT/'selector_sweep_take.json';take=json.loads(source.read_text())
geo={key:([Vector(v) for v in g['vertices']],g['triangles']) for key,g in take['geometry'].items()}
def build(items,poses):
    points=[];faces=[];owners=[]
    for item in items:
        if item['id'] not in poses:continue
        matrix=Matrix(poses[item['id']]);vs,fs=geo[item['geometry']];offset=len(points)
        points.extend(matrix@v for v in vs);faces.extend(tuple(offset+i for i in f) for f in fs);owners.extend([item['id']]*len(fs))
    if not points:return None,[],None
    bounds=([min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)])
    return BVHTree.FromPolygons(points,faces,all_triangles=True),owners,bounds
controls=[n for n in take['nodes'] if n['group']=='F_controls'];selector=[n for n in take['nodes'] if n['group']=='selector']
control,control_owners,bounds=build(controls,take['samples'][0]['poses']);issues={};checked=0;minimum_gap=float('inf');closest=None
for sample in take['samples']:
    for node in selector:
        if node['id'] not in sample['poses']:continue
        matrix=Matrix(sample['poses'][node['id']]);vs,_=geo[node['geometry']]
        # Runtime arrays are retained; the broad phase does not substitute boxes for geometry.
        transformed=[matrix@v for v in vs];lo=[min(v[k] for v in transformed) for k in range(3)];hi=[max(v[k] for v in transformed) for k in range(3)]
        gap=math.sqrt(sum(max(0.,lo[k]-bounds[1][k],bounds[0][k]-hi[k])**2 for k in range(3)))
        if gap<minimum_gap:minimum_gap=gap;closest={'amount':sample['amount'],'selector_mesh':node['id']}
        if gap>0:continue
        tree,owners,_=build([node],sample['poses']);checked+=1
        for a,b in tree.overlap(control):
            pair=(owners[a],control_owners[b]);key=' | '.join(pair)
            if key not in issues:issues[key]={'objects':pair,'amounts':set(),'triangle_pairs':0}
            issues[key]['amounts'].add(sample['amount']);issues[key]['triangle_pairs']+=1
pairs=[{**item,'amounts':sorted(item['amounts'])} for item in issues.values()]
report={'passed':not pairs,'samples':len(take['samples']),'controls_meshes':len(controls),'selector_meshes':len(selector),'narrow_phase_mesh_samples':checked,'minimum_union_aabb_gap':minimum_gap,'closest_broad_phase':closest,'intersections':pairs,'controls_sha256':take['controls_sha256'],'selector_sha256':take['selector_sha256'],'take_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':take['scope']+' Triangle surface overlap, not a continuous-volume or manufacturing-clearance certificate.'}
(OUT/'selector_sweep_check.json').write_text(json.dumps(report,indent=2)+'\n');print('F_SELECTOR_CLEARANCE',json.dumps({'passed':not pairs,'pairs':len(pairs),'samples':len(take['samples']),'first':pairs[:5],'minimum_aabb_gap':minimum_gap}),flush=True)
if pairs:raise SystemExit(1)
