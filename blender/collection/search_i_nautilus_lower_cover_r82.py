"""Find a compact lower-cover path against saved peer motion and the actual saddle."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/mechanism_r6'
d=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));s=bpy.context.scene
p=d['panels'][1];o=bpy.data.objects[p['mesh']]
def extract(obj,local=False):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 M=(bpy.data.objects[p['node']].matrix_world.inverted()@obj.matrix_world)if local else obj.matrix_world
 vs=[M@v.co for v in me.vertices];ts=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();return vs,ts
def tree(vs,ts):
 return (BVHTree.FromPolygons(vs,ts,all_triangles=True),[min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)])
def overlap(a,b):return all(a[1][k]<=b[2][k] and b[1][k]<=a[2][k]for k in range(3))and bool(a[0].overlap(b[0]))
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
s.frame_set(1);verts,tris=extract(o,True);fixed=tree(*extract(bpy.data.objects['R82_R4_Forged_Saddle_-1']))
states=[]
for f in [1,27,34,44,50,53,67,85,115,145,195,230,250,260,300]:
 s.frame_set(f);others=[tree(*extract(bpy.data.objects[q['mesh']]))for q in d['panels']if q['id']!=2]
 t=(f-26.5)/82 if f<150 else 1-(f-180)/82;t=max(0,min(1,t))
 Q=Quaternion(Vector(p['axis']),p['angle']*smooth((t-.30)/.70));states.append((f,smooth(t/.30),Q,others))
results=[];best=None
for dy,dz in [(y,z)for y in [-.18,-.22,-.26,-.30]for z in [0.,.02,-.025,.04]]:
 D=Vector((p['translation'][0],dy,dz));hits=[]
 for f,lift,Q,others in states:
  M=Matrix.Translation(Vector(p['pivot'])+D*lift)@Q.to_matrix().to_4x4()
  current=tree([M@v for v in verts],tris)
  if overlap(current,fixed):hits.append((f,'saddle'));break
  for b in others:
   if overlap(current,b):hits.append((f,'peer'));break
  if hits:break
 results.append({'translation':list(D),'first_conflict':hits})
 print(results[-1],flush=True)
 if not hits:best=list(D);break
(OUT/'lower_cover_path_search.json').write_text(json.dumps({'scope':'15 poses lower cover vs five covers and front saddle only; guide system still must be rebuilt/rechecked','results':results,'first_feasible':best},indent=2)+'\n')
