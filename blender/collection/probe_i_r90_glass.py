"""Locate optical-channel contact before changing any authored dimensions."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/network_r90/built_r4';s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));bpy.context.scene.frame_set(175);bpy.context.view_layer.update()
def geo(name):
 o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@x.co for x in me.vertices];tri=[tuple(x.vertices)for x in me.loop_triangles];regions=[me.attributes['surface_region'].data[x.polygon_index].value if 'surface_region'in me.attributes else None for x in me.loop_triangles];uvh=[list(x.vector)for x in me.attributes['surface_param'].data]if 'surface_param'in me.attributes else None;ev.to_mesh_clear();return BVHTree.FromPolygons(v,tri,all_triangles=True),v,tri,regions,uvh
a=geo('I90_OpalPath_26');b=geo('I90_CastBackbone');rows=[]
for i,j in a[0].overlap(b[0]):
 rows.append({'glass_triangle':i,'glass_rings':[k//16 for k in a[2][i]],'region':b[3][j],'glass_points':[list(a[1][k])for k in a[2][i]],'body_points':[list(b[1][k])for k in b[2][j]],'body_parameters':[b[4][k]for k in b[2][j]]})
(OUT/'glass_contact_diagnosis.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows[:4]:print(row,flush=True)
