"""Exact locations and double-precision separation for the residual rim pair."""
import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/geometry'))
from i_triangle_separation import separation,self_check
self_check();OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r89/built_r2';s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));bpy.context.scene.frame_set(175);bpy.context.view_layer.update()
def geo(name):
 o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@p.co for p in me.vertices];t=[tuple(p.vertices)for p in me.loop_triangles];ev.to_mesh_clear();return BVHTree.FromPolygons(v,t,all_triangles=True),v,t
a,va,fa=geo('I84_Cell_01_Frame');b,vb,fb=geo('R82_Acoustic_Chamber_Liner');rows=[]
for i,j in a.overlap(b):
 pa=[va[k]for k in fa[i]];pb=[vb[k]for k in fb[j]];row={'triangles':[i,j],'frame_vertices':fa[i],'frame_profile_rings':[k//96 for k in fa[i]],'points_a':[list(p)for p in pa],'points_b':[list(p)for p in pb],'separation':separation(pa,pb,tolerance=1e-10)};rows.append(row);print(row,flush=True)
(OUT/'rim_contact_diagnosis.json').write_text(json.dumps(rows,indent=2)+'\n')
