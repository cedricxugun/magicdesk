"""Actual bored porcelain surface BVHs over continuous animation, not AABBs."""
import bpy,json,pathlib,itertools
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_complete.blend'))
scene=bpy.context.scene
shells=[o for o in bpy.data.objects if o.type=='MESH' and ('GlazedLamina' in o.name or 'CoverPorcelain' in o.name)]
assert len(shells)==8,len(shells)
frames=sorted(set(range(1,1442,12))|set(range(30,136,3))|{1441,211,291,341,396,781,941,1061,1181,1206})
failures=[]
for frame in frames:
    scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();trees={}
    for o in shells:
        ev=o.evaluated_get(deps);mesh=ev.to_mesh();trees[o.name]=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons],epsilon=.00002);ev.to_mesh_clear()
    for a,b in itertools.combinations(shells,2):
        hits=trees[a.name].overlap(trees[b.name])
        if hits:failures.append({'frame':frame,'a':a.name,'b':b.name,'triangle_pairs':len(hits)})
report={'all_passed':not failures,'frames':len(frames),'actual_porcelain_meshes':len(shells),'method':'evaluated world-space triangle BVH, epsilon 0.02 mm','scope':'leaf/leaf and cover/leaf through unfold, selected fold, rewind, extraction and reassembly; intentional metal bearings excluded','failures':failures}
(ROOT/'review/G_complete/clearance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('G_CLEARANCE',len(frames),'frames',len(failures),'intersections',flush=True)
