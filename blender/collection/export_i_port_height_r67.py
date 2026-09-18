"""Export actual candidate and local source skin triangles for envelope fitting."""
import bpy,json,collections,sys
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/collection/I_nautilus_port_rebuild_r66.blend'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
o=bpy.data.objects['IS18_Leg01_PortLiner'];F=bpy.data.objects['IS18_Leg01_PortFrame'].matrix_world;inv=F.inverted()
def geo(o):
 m=o.data;m.calc_loop_triangles();v=[o.matrix_world@p.co for p in m.vertices];t=[tuple(f.vertices)for f in m.loop_triangles];return v,t,BVHTree.FromPolygons(v,t,all_triangles=True)

v,t,tr=geo(o);payload={'source':'blender/collection/I_nautilus_port_rebuild_r66.blend','vertices':[list(inv@p)for p in v],'triangles':t,'skins':[]}
for name in ['IN1_PorcelainPanel_01','IN1_PorcelainPanel_02']:
 sv,st,sr=geo(bpy.data.objects[name]);local=[inv@p for p in sv];faces=[]
 for f in st:
  p=[local[i]for i in f]
  if any(max(v[k]for v in p)<-.042 or min(v[k]for v in p)>.042 for k in [0,1]):continue
  faces.append([list(v)for v in p])
 payload['skins'].append({'name':name,'triangles':faces})
P=R/'review/I_refinement/nautilus_r1/port_envelope_r67';P.mkdir(parents=True,exist_ok=True);(P/'height_source.json').write_text(json.dumps(payload))
print('HEIGHT_SOURCE',[(r['name'],len(r['triangles']))for r in payload['skins']])
