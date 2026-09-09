"""Check the actual Godot focus solver poses against Blender surface geometry."""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/L.blend'))
for obj in bpy.data.objects:obj.animation_data_clear()
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('L_') and any(m and m.name.startswith('Collection_Ivory') for m in o.data.materials)]
def depth(obj):return 0 if obj.parent is None else 1+depth(obj.parent)
frames=json.loads((ROOT/'tests/collection/focus_rig_samples.json').read_text());intersections=[]
for frame in frames:
    for name,pose in sorted(frame['poses'].items(),key=lambda p:depth(bpy.data.objects[p[0]])):
        matrix=Matrix(pose['basis']).transposed().to_4x4();matrix.translation=Vector(pose['p'])
        bpy.data.objects[name].matrix_world=C.inverted()@matrix@C
        bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();trees=[]
    for obj in objects:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
        trees.append(BVHTree.FromPolygons([evaluated.matrix_world@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True,epsilon=0));evaluated.to_mesh_clear()
    for i in range(len(objects)):
        for j in range(i+1,len(objects)):
            hits=trees[i].overlap(trees[j])
            if hits:intersections.append({'time':frame['time'],'a':objects[i].name,'b':objects[j].name,'triangle_pairs':len(hits)})
report={'model':'L','source':'actual runtime focus solver poses, including interrupted motion','samples':len(frames),'all_clear':len(intersections)==0,'intersections':intersections}
(ROOT/'tests/collection/focus_clearance.json').write_text(json.dumps(report,indent=2));print('FOCUS_CLEARANCE',report['all_clear'],len(intersections),flush=True)
