"""Read-only swept porcelain versus pneumatic hardware check; never saves source."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/r2'
source=ROOT/'blender/collection/I_pneumatic_r2.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
panels=[bpy.data.objects['IH1_FrontPanel'+str(i)] for i in range(6)]
for panel in panels:panel.animation_data_clear()
shells=[o for o in bpy.data.objects['IH1_UPPER'].children_recursive if o.type=='MESH' and any(s in o.name for s in ['FrontPorcelain','RearPorcelain'])]
hardware=[o for o in bpy.data.objects['IH1_UPPER'].children_recursive if o.type=='MESH' and (o.name.startswith('IP2_') or 'BellowsFoldedWall' in o.name)]
def tree(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
    points=[obj.matrix_world@v.co for v in mesh.vertices];faces=[tuple(t.vertices) for t in mesh.loop_triangles];ev.to_mesh_clear()
    return BVHTree.FromPolygons(points,faces,all_triangles=True)
collisions=[];checks=0
# Rest and maximum reservoir compression; shell opening swept independently.
for frame in [1,88]:
    scene.frame_set(frame)
    for step in range(21):
        opening=step/20
        for panel in panels:panel.location=Vector(panel['open_direction'])*panel['stroke']*opening
        bpy.context.view_layer.update();shell_trees={o.name:tree(o) for o in shells}
        for obj in hardware:
            candidate=tree(obj)
            for shell in shells:
                hits=candidate.overlap(shell_trees[shell.name]);checks+=1
                if hits:collisions.append({'pressure_frame':frame,'opening':opening,'hardware':obj.name,'shell':shell.name,'intersections':len(hits)})
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'passed':not collisions,'pair_checks':checks,'hardware':[o.name for o in hardware],'shells':[o.name for o in shells],'surface_intersections':collisions,'scope':'21 shell openings at rest and near-full compression, all IP2 mesh hardware plus bellows wall against front/rear porcelain. Surface intersections only; containment, other old inner hardware, hardware-to-hardware, and continuous unsampled motion excluded.'}
(OUT/'hardware_shell_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_HARDWARE_SHELLS',result['passed'],'intersections',len(collisions),'pairs',checks,flush=True)
if collisions:raise SystemExit(1)
