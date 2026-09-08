import pathlib,json
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=(ROOT/'blender/inspect_center_clearance.py').read_text(encoding='utf8');exec(s[:s.index('names=')])
name='P_Thermal_Valve_0';others=[p['name']for p in M['parts']if p['name']!=name]
pose(0,0,0)
ob=next(c for c in bpy.data.objects[name].children if c.type=='MESH')
verts=[ob.matrix_world@v.co for v in ob.data.vertices];faces=[tuple(p.vertices)for p in ob.data.polygons]
candidates={x:BVHTree.FromPolygons([v+Vector((x-.89,-.10,0))for v in verts],faces)for x in [1.12,1.15,1.18]}
results={x:[]for x in candidates}
for op in [i/10 for i in range(11)]:
 pose(op,1.3,0);trees={n:tree(n)[0]for n in others}
 for x,t in candidates.items():
  pairs=[]
  for n,other in trees.items():
   count=len(t.overlap(other))
   if count:pairs.append([n,count])
  results[x].append({'openness':op,'pairs':pairs})
  if pairs:print('HIGH_VALVE_CANDIDATE_COLLISION',x,op,pairs,flush=True)
summary={x:sum(len(row['pairs'])for row in rows)for x,rows in results.items()}
print('HIGH_VALVE_SUMMARY',summary,flush=True)
(ROOT/'tests/high_valve_static_candidates.json').write_text(json.dumps({'colliding_pairs_by_candidate':summary,'states':results},indent=2))
