"""Bounded geometry search; records failures rather than weakening clearance rules."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/mechanism_r5'
d=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));bpy.context.scene.frame_set(1)
parts=[]
for p in d['panels']:
 o=bpy.data.objects[p['mesh']];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 # Exact evaluated surface triangles in the current node coordinates.
 inv=bpy.data.objects[p['node']].matrix_world.inverted()
 vs=[inv@o.matrix_world@v.co for v in me.vertices];ts=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();parts.append((p,vs,ts))
results=[];best=None
for radial,depth,ang,inner_depth,inner_angle in [(r,.18,.65,iy,ia)for r in [.10,.12]for iy in [.18,.24,.30]for ia in [.20,.35,.65]]:
 vals=[]
 for p,vs,ts in parts:
  t=(p['ta']+p['tb'])/2;a=d['shape_parameters']['END']+t-d['shape_parameters']['T']
  D=Vector((math.cos(a)*radial,-depth,math.sin(a)*radial))
  if p['id']==1:D=Vector((0,-inner_depth,0))
  vals.append((p,vs,ts,D))
 pairs=0
 for f in [.33,.55,.78,1.0]:
  ts=[]
  for p,vs,tri,D in vals:
   rot=max(0,min(1,(f-.3)/.7));rot=rot**3*(rot*(rot*6-15)+10)
   Q=Quaternion(Vector(p['axis']),p['angle']*(inner_angle if p['id']==1 else ang)*rot)
   M=Matrix.Translation(Vector(p['pivot'])+D)@Q.to_matrix().to_4x4()
   world=[M@v for v in vs];lo=[min(v[k]for v in world)for k in range(3)];hi=[max(v[k]for v in world)for k in range(3)]
   ts.append((BVHTree.FromPolygons(world,tri,all_triangles=True),lo,hi))
  for i,a in enumerate(ts):
   for b in ts[i+1:]:
    if all(a[1][k]<=b[2][k] and b[1][k]<=a[2][k]for k in range(3)):
     hit=a[0].overlap(b[0]);pairs+=bool(hit)
  if pairs:break
 rec={'radial':radial,'depth':depth,'angle_multiplier':ang,'inner_depth':inner_depth,'inner_angle_multiplier':inner_angle,'intersecting_pair_states':pairs}
 results.append(rec);print('SEARCH',rec,flush=True)
 if not pairs:
  best={**rec,'translations':[list(v[3])for v in vals]};break
(OUT/'opening_search_compact.json').write_text(json.dumps({'scope':'Four staged open fractions, ceramic/ceramic only, saved evaluated meshes. Not final motion/guide/appearance acceptance.','results':results,'first_feasible':best},indent=2)+'\n')
print('R82_OPEN_SEARCH_DONE',bool(best),flush=True)
