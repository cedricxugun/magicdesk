import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r80';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('IN1_Cell','IN1_ChamberRib','IN3_ContinuousThroat','IN1_Porcelain','IN1_FixedRear'))]
v=[];f=[];names=[]
for o in objects:
 o.data.calc_loop_triangles();start=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices);f.extend(tuple(start+k for k in t.vertices) for t in o.data.loop_triangles);names.extend([o.name]*len(o.data.loop_triangles))
t=BVHTree.FromPolygons(v,f,all_triangles=True)
def layers(x,y):
 p=Vector((x,y,.7));out=[]
 for k in range(20):
  hit=t.ray_cast(p,Vector((0,0,1)),.8)
  if hit[2] is None or hit[0].z>1.5:break
  out.append([names[hit[2]],hit[0].z]);p=hit[0]+Vector((0,0,.00001))
 return out
rows=[]
for x,y in [(-.2,.14),(-.2,.15),(.26,.14),(.26,.10),(.24,.08),(.18,.05),(.28,.08)]:
 row={'xy':[x,y],'center_layers':layers(x,y),'rings':{}}
 for r in [.024,.030,.038,.044,.05]:
  samples=[layers(x+r*math.cos(math.tau*i/32),y+r*math.sin(math.tau*i/32)) for i in range(32)]
  row['rings'][str(r)]={'skins':sorted(set(a[0] for sample in samples for a in sample if a[0].startswith(('IN1_Porcelain','IN1_Fixed')))), 'first_acoustic':sorted(set(next((a[0] for a in sample if a[0].startswith('IN1_Cell')), 'none') for sample in samples))}
 rows.append(row)
(OUT/'frame_mount_survey.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
