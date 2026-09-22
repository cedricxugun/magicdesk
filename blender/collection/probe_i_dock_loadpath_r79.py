"""Find metal structural landing regions without crossing any acoustic membrane."""
import bpy,json,math,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r79'
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('IN1_Cell','IN1_ChamberRib','IN3_ContinuousThroat','IF','IS9_','IC10_'))]
v=[];f=[];names=[]
for o in objects:
 o.data.calc_loop_triangles();start=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices);f.extend(tuple(start+k for k in t.vertices) for t in o.data.loop_triangles);names.extend([o.name]*len(o.data.loop_triangles))
tree=BVHTree.FromPolygons(v,f,all_triangles=True);rows=[]
for ix in range(41):
 x=-.4+ix*.02
 for iy in range(39):
  y=-.25+iy*.02;p=Vector((x,y,.75));hit=tree.ray_cast(p,Vector((0,0,1)),.75)
  if hit[2] is None:continue
  owner=names[hit[2]]
  if 'CellFrame' not in owner and 'ChamberRib' not in owner:continue
  radius=0.
  for r in [.01,.015,.02,.025,.03,.04]:
   hits=[]
   for j in range(24):
    a=math.tau*j/24;h=tree.ray_cast(Vector((x+r*math.cos(a),y+r*math.sin(a),.75)),Vector((0,0,1)),.75)
    hits.append(h[2] is not None and names[h[2]]==owner)
   if all(hits):radius=r
   else:break
  rows.append({'point':list(hit[0]),'normal':list(hit[1]),'owner':owner,'circular_patch_radius':radius})
(OUT/'loadpath_candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
print('R79_METAL_LANDINGS',len(rows),collections.Counter(r['owner'] for r in rows),flush=True)
for row in sorted(rows,key=lambda r:r['circular_patch_radius'],reverse=True)[:35]:print(row,flush=True)
