"""Measure actual lower cover clearance above the existing mounting footprint."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import math
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1';spec=json.loads((OUT/'build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();v=[];t=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_')):continue
    e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(v);v += [e.matrix_world@p.co for p in m.vertices];t += [tuple(offset+i for i in f.vertices) for f in m.loop_triangles];e.to_mesh_clear()
tree=BVHTree.FromPolygons(v,t,all_triangles=True);rows=[];z0=spec['deck_sample']['max']+.07
for ring in range(21):
    radius=.48*ring/20
    for k in range(96 if ring else 1):
        a=math.tau*k/96;x=.08+radius*math.cos(a);y=.13+radius*math.sin(a);hit=tree.ray_cast(Vector((x,y,z0)),Vector((0,0,1)),3.)
        if hit[0] is not None:rows.append({'x':x,'y':y,'z':hit[0].z,'r':radius})
values=[r['z'] for r in rows];result={'source_sha256':spec['source_sha256'],'samples':rows,'minimum':min(values),'maximum':max(values),'scope':'Closed source cover underside over radius .48 mounting footprint; actual triangle ray hits, not moving-cover clearance or final contact proof.'};(OUT/'seat_envelope.json').write_text(json.dumps(result,indent=2)+'\n');print('SEAT_ENVELOPE',len(rows),min(values),max(values),flush=True)
