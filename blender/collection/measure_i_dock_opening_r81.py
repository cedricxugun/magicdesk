"""Read actual saved Blender animation poses for independent Godot comparison."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r81'
s=json.loads((OUT/'opening_source.json').read_text());path=ROOT/s['source'];assert hashlib.sha256(path.read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(path));names=s['animated_nodes']+['ID80_Carrier','ID80_Stanchion0_PortRim','ID80_Stanchion1_PortRim']
points=[(0,0,0),(.1,0,0),(0,.1,0),(0,0,.1)];rows=[]
def cv(p):return [p.x,p.z,-p.y]
for frame in list(range(0,420,15))+[419]:
 bpy.context.scene.frame_set(frame+1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 row={'frame':frame,'points':{}}
 for name in names:
  matrix=bpy.data.objects[name].evaluated_get(dg).matrix_world
  row['points'][name]=[cv(matrix@Vector(p)) for p in points]
 rows.append(row)
assert rows[0]['points']==rows[-1]['points'],'Saved source does not exactly return'
(OUT/'opening_witnesses.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'body_source_sha256':s['body_source_sha256'],'local_points':[cv(Vector(p)) for p in points],'samples':rows,'exact_return':True},indent=2)+'\n');print('R81_ACTUAL_ANIMATION_WITNESSES',len(rows)*len(names)*4,flush=True)
