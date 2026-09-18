"""Independent dense engagement sweep of actual evaluated, relieved involute wheels."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from ship_wave_kinematics import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_ship_r3.blend'));bpy.context.scene.frame_set(1)
shaft=bpy.data.objects['GS3_CommonShaft'];pinion=bpy.data.objects['GS3_Pinion']
shaft.animation_data_clear();pinion.animation_data_clear()
gear=next(o for o in bpy.data.objects if 'Driven36Involute_' in o.name)
small=next(o for o in bpy.data.objects if 'Input18Involute_' in o.name)
def geom(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    pts=[v.co.copy() for v in me.vertices];tris=[tuple(p.vertices) for p in me.loop_triangles];ev.to_mesh_clear();return pts,tris
large_points,large_faces=geom(gear);small_points,small_faces=geom(small)
collisions=[];gaps=[]
# One main-wheel tooth pitch spans every unique involute contact configuration.
for i in range(201):
    phase=i/200*math.tau/36
    shaft.rotation_euler.y=-phase;pinion.rotation_euler.y=-(GEAR_ANGLE+math.pi+math.pi/18-2*phase);bpy.context.view_layer.update()
    a=BVHTree.FromPolygons([gear.matrix_world@p for p in large_points],large_faces,all_triangles=True)
    b=BVHTree.FromPolygons([small.matrix_world@p for p in small_points],small_faces,all_triangles=True)
    hits=a.overlap(b)
    if hits:collisions.append({'phase':phase,'triangles':len(hits)})
    gap=min(b.find_nearest(gear.matrix_world@Vector((x,0,z)))[3] for x,z in gear_outline(36))
    gaps.append(gap)
report={'source_sha256':hashlib.sha256((ROOT/'blender/collection/G_ship_r3.blend').read_bytes()).hexdigest(),'samples':201,'main_angle_degrees':[0,10],'teeth':[36,18],'module':.003,'center_distance':.081,'surface_intersections':collisions,'closest_flank_gap':[min(gaps),max(gaps)],'passed':not collisions and max(gaps)<.00035,'scope':'Evaluated gear teeth, 201 phases per repeating tooth sector. Backlash means a small deliberate mesh gap; no dynamic force/friction simulation.'}
(ROOT/'review/G_optical_curator/ship_r3/gear_mesh_check.json').write_text(json.dumps(report,indent=2)+'\n');print('R3_GEARS',json.dumps(report),flush=True)
if not report['passed']:raise SystemExit(1)
