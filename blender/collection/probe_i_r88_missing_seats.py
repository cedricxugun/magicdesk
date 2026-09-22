"""Compare authored bolt seat rays with current forged and original feet."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/back_hardware_r88/built_r2';s=json.loads((OUT/'build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def tree(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@q.co for q in me.vertices];t=[tuple(q.vertices)for q in me.loop_triangles];ev.to_mesh_clear();return BVHTree.FromPolygons(v,t,all_triangles=True)
rows=[]
for row in s['forged_supports']:
 if (row['id'],row['side']) not in [(4,1),(6,1),(5,1)]:continue
 foot=bpy.data.objects[row['shoe']];bvh=tree(foot)
 for name in row['fasteners']:
  bolt=bpy.data.objects[name];matrix=bolt.matrix_world.copy();inv=matrix.inverted();direction=(matrix.to_3x3()@Vector((0,0,-1))).normalized();point=matrix@Vector((.0028,0,-.002));near=bvh.find_nearest(point)
  ray=bvh.ray_cast(matrix@Vector((.0028,0,.05)),direction,.2)
  rows.append({'bolt':name,'shoe':foot.name,'bolt_matrix':[list(v)for v in matrix],'current_nearest':near[3],'nearest_local':list(inv@near[0]) if near[0]else None,'current_ray_local':list(inv@ray[0])if ray[0]else None,'foot_vertices':len(foot.data.vertices),'foot_world_matrix':[list(v)for v in foot.matrix_world]})
parent=json.loads((R/'review/I_refinement/nautilus_reset_r82/oblique_hinge_r87/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/parent['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
for row in rows:
 matrix=Matrix(row['bolt_matrix']);inv=matrix.inverted();bvh=tree(bpy.data.objects[row['shoe']]);direction=(matrix.to_3x3()@Vector((0,0,-1))).normalized();ray=bvh.ray_cast(matrix@Vector((.0028,0,.05)),direction,.2);near=bvh.find_nearest(matrix@Vector((.0028,0,-.002)))
 row['original_ray_local']=list(inv@ray[0])if ray[0]else None;row['original_nearest']=near[3]
(OUT/'missing_seat_diagnosis.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:print({k:v for k,v in row.items()if 'matrix'not in k},flush=True)
