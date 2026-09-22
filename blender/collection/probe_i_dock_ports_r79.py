import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r79'
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_'))]
v=[];f=[];names=[]
for o in objects:
 o.data.calc_loop_triangles();start=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices);f.extend(tuple(start+k for k in t.vertices) for t in o.data.loop_triangles);names.extend([o.name]*len(o.data.loop_triangles))
tree=BVHTree.FromPolygons(v,f,all_triangles=True);rows=[]
for x in [-.24,-.20,-.18,-.16,-.12,-.08,.12,.16,.18,.20,.24,.28,.32]:
 for y in [-.04,0.,.04,.08,.10,.12,.14,.18,.22,.26]:
  hits=[]
  for radius in [.037,.074]:
   for i in range(64):
    a=math.tau*i/64;p=Vector((x+radius*math.cos(a),y+radius*math.sin(a),.68));hit=tree.ray_cast(p,Vector((0,0,1)),.7)
    hits.append(None if hit[2] is None else names[hit[2]])
  if all(n=='IN1_PorcelainPanel_02' for n in hits):rows.append({'xy':[x,y],'radius':.074})
(OUT/'port_candidates.json').write_text(json.dumps(rows,indent=2)+'\n');print('R79_PORT_CANDIDATES',rows,flush=True)
