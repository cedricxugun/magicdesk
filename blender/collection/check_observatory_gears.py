"""Check actual evaluated tooth meshes through a full coupled revolution."""
import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
data=json.loads((ROOT/'app/assets/collection/components/G_observatory_r2.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_observatory_r2.blend'))
gears=data['gear_train'];hits=[];max_pairs=0
for frame in range(96):
    t=math.tau*frame/96
    for item in gears:bpy.data.objects[item['node']].rotation_euler.y=-(item['phase']+t*item['ratio'])
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();trees=[]
    for item in gears:
        obj=bpy.data.objects[item['wheel']];ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[tuple(tri.vertices) for tri in mesh.loop_triangles],all_triangles=True);trees.append(tree);ev.to_mesh_clear()
    for a,b in [(0,1),(1,2)]:
        pairs=trees[a].overlap(trees[b]);max_pairs=max(max_pairs,len(pairs))
        if pairs:hits.append({'sample':frame,'pair':[a,b],'triangle_pairs':len(pairs)})
report={'passed':not hits,'samples':96,'maximum_triangle_pairs':max_pairs,'collisions':hits[:20],'scope':'Three evaluated wheel tooth meshes and declared gear ratios; excludes whole-component clearance'}
(ROOT/'review/G_optical_curator/observatory_r2/gear_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('OBSERVATORY_GEAR_CLEARANCE',json.dumps(report),flush=True)
assert report['passed'],'Gear tooth overlap'
