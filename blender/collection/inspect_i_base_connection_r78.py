"""Read-only installed support audit after user rejected the R76 support depiction."""
import bpy,json,hashlib,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/base_connection_r78';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot']
def geo(objects):
    verts=[];faces=[];names=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();offset=len(verts)
        verts.extend(e.matrix_world@v.co for v in m.vertices)
        faces.extend(tuple(offset+i for i in t.vertices) for t in m.loop_triangles)
        names.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
    return verts,faces,names
def bounds(o):
    v,_,_=geo([o]);return [[min(p[k] for p in v) for k in range(3)],[max(p[k] for p in v) for k in range(3)]]
skins=[o for o in body.children_recursive if o.type=='MESH' and o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_','IN1_FixedMouthCheek'))]
sv,sf,sn=geo(skins);tree=BVHTree.FromPolygons(sv,sf,all_triangles=True)
rows=[]
for i in range(1,5):
    gasket=bpy.data.objects[f'IN1_FittedSaddleGasket_{i}'];v,f,n=geo([gasket])
    gt=BVHTree.FromPolygons(v,f,all_triangles=True);hits=gt.overlap(tree);top=[]
    for tri in f:
        a,b,c=[v[k] for k in tri]
        if (b-a).cross(c-a).normalized().z<.25:continue
        p=(a+b+c)/3;near=tree.find_nearest(p)
        top.append({'gap':near[3],'skin':sn[near[2]] if near[2] is not None else None})
    rows.append({'id':i,'gasket_bounds':bounds(gasket),'seat_bounds':bounds(bpy.data.objects[f'IN1_FittedSaddleSeat_{i}']),
        'surface_contacts':len(hits),'contact_owners':dict(collections.Counter(sn[b] for a,b in hits)),
        'top_face_centroid_samples':len(top),'min_nearest_gap':min(r['gap'] for r in top),'max_nearest_gap':max(r['gap'] for r in top),
        'nearest_owners':dict(collections.Counter(r['skin'] for r in top))})
names=['IN1_DeckFoot','IN1_LowSaddle','IN3_ContinuousThroat','IN1_SpiralHub']
support_names=[o.name for o in body.children_recursive if o.name.startswith(('IS18_','IN1_FittedSaddle','IN1_DeckFoot','IN1_LowSaddle')) and o.type=='MESH']
r={'source_sha256':s['source_sha256'],'state':'ordinary installed, source frame 1, no .45 lift or parked service parts',
   'seats':rows,'bounds':{n:bounds(bpy.data.objects[n]) for n in names if n in bpy.data.objects},'support_parts':support_names,
   'fixed_panels':[row['mesh'] for row in s['form_panels'] if not row['active']],
   'scope':'Surface fit observations only. Touching a shell does not certify a load-bearing joint or locking/retention. Source construction explicitly labels the original saddle as a shape-study interface.'}
(OUT/'installed_audit.json').write_text(json.dumps(r,indent=2)+'\n')
print('R78_INSTALLED_AUDIT',[(r['id'],r['surface_contacts'],r['min_nearest_gap'],r['max_nearest_gap'],r['nearest_owners']) for r in rows],flush=True)
