"""Read-only survey of real pedestal, shell and inner-housing installation room."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r79';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def geo(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@p.co for p in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return v,f
def record(o):
 v,f=geo(o);return {'name':o.name,'parent':o.parent.name if o.parent else None,'bounds':[[min(p[k] for p in v) for k in range(3)],[max(p[k] for p in v) for k in range(3)]],'triangles':len(f)}
base=bpy.data.objects['BASE_FIXED'];base_rows=[record(o) for o in [base,*base.children_recursive] if o.type=='MESH']
body=bpy.data.objects['IN1_BodyRoot'];meshes=[o for o in body.children_recursive if o.type=='MESH'];inside=[record(o) for o in meshes if any(k in o.name for k in ['Hub','ContinuousThroat','Saddle','DeckFoot','CouplingSeal'])]
trees={}
for o in meshes:
 if o.name=='IN3_ContinuousThroat' or o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_')):
  v,f=geo(o);trees[o.name]=BVHTree.FromPolygons(v,f,all_triangles=True)
columns=[]
for x in [-.24,-.16,.0,.16,.24,.32]:
 for y in [.02,.14,.26,.38]:
  hits=[]
  for name,tree in trees.items():
   hit=tree.ray_cast(Vector((x,y,.68)),Vector((0,0,1)),1.)
   if hit[0] is not None:hits.append({'mesh':name,'z':hit[0].z,'normal':list(hit[1])})
  columns.append({'xy':[x,y],'hits':sorted(hits,key=lambda r:r['z'])})
import math
v,f=geo(bpy.data.objects['BASE_FIXED_DisplayMesh']);bt=BVHTree.FromPolygons(v,f,all_triangles=True)
deck=[]
for i in range(6):
 a=math.tau*i/6+.18;x=.08+.505*math.cos(a);y=.13+.505*math.sin(a);heights=[];origin=Vector((x,y,.72))
 for _ in range(16):
  hit=bt.ray_cast(origin,Vector((0,0,-1)),1.)
  if hit[0] is None:break
  heights.append(hit[0].z);origin=hit[0]+Vector((0,0,-.00001))
 deck.append({'xy':[x,y],'layers':heights})
(OUT/'survey.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'base':base_rows,'inside':inside,'columns':columns,'deck_bolt_layers':deck},indent=2)+'\n')
print('R79_BASE',base_rows,flush=True);print('R79_INSIDE',inside,flush=True)
