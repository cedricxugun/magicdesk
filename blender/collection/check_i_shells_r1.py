"""Check distinct moving/fixed porcelain shells over operating opening."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/r1';source=ROOT/'blender/collection/I_helix_r1.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
panels=[bpy.data.objects['IH1_FrontPanel'+str(i)] for i in range(6)]
for panel in panels:panel.animation_data_clear()
objects=[o for o in bpy.data.objects['IH1_UPPER'].children_recursive if o.type=='MESH' and any(s in o.name for s in ['FrontPorcelain','RearPorcelain'])]
geometry={}
for obj in objects:
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();geometry[obj.name]=([v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles]);ev.to_mesh_clear()
collisions=[];pairs=0
for step in range(21):
    amount=step/20
    for panel in panels:panel.location=Vector(panel['open_direction'])*panel['stroke']*amount
    bpy.context.view_layer.update();trees={}
    for obj in objects:
        points,faces=geometry[obj.name];trees[obj.name]=BVHTree.FromPolygons([obj.matrix_world@p for p in points],faces,all_triangles=True)
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            if a.parent==b.parent or (a.parent not in panels and b.parent not in panels):continue
            hits=trees[a.name].overlap(trees[b.name]);pairs+=1
            if hits:collisions.append({'opening':amount,'a':a.name,'b':b.name,'triangles':len(hits)})
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'positions':21,'pair_checks':pairs,'surface_intersections':collisions,'passed':not collisions,'scope':'Distinct moving/fixed porcelain components, including split mouth hood. Same rigid group joining interfaces and metal/inner hardware are excluded.'}
(OUT/'shell_clearance.json').write_text(json.dumps(result,indent=2)+'\n');print('I_SHELL_CLEARANCE',result['passed'],'collisions',len(collisions),flush=True)
if not result['passed']:raise SystemExit(1)
