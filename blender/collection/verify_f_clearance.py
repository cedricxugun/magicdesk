"""Sample actual evaluated meshes, excluding intended bearing contacts."""
import bpy,json,pathlib
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/F_complete.blend'))
scene=bpy.context.scene
def belongs(obj,names):
    while obj:
        if obj.name in names:return True
        obj=obj.parent
    return False
frame_parts={'F_P_ContinuousSpine'}|{'F_P_SpineCover'+str(i) for i in range(6)}
frame_mesh=[o for o in bpy.data.objects if o.type in ['MESH','CURVE'] and belongs(o,frame_parts)]
plumb=[o for o in bpy.data.objects if o.type in ['MESH','CURVE'] and belongs(o,{'F3_PlumbPendulum'})]
prism=[o for o in bpy.data.objects if o.type in ['MESH','CURVE'] and belongs(o,{'F3_PrismPendulum'})]
receiver=[o for o in bpy.data.objects if o.type in ['MESH','CURVE'] and belongs(o,{'F3_ReceiverDish'})]
def tree(objects):
    dg=bpy.context.evaluated_depsgraph_get();vertices=[];polygons=[]
    for obj in objects:
        evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh();offset=len(vertices)
        vertices.extend(evaluated.matrix_world@v.co for v in mesh.vertices)
        polygons.extend(tuple(offset+i for i in p.vertices) for p in mesh.polygons)
        evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices,polygons,all_triangles=False,epsilon=0)
failures=[];frames=list(range(1,960,24))+[30,60,95,174,188,360,390,440,835,840,860,900,950,1321]
for f in sorted(set(frames)):
    scene.frame_set(f);bpy.context.view_layer.update();fixed=tree(frame_mesh)
    for name,objects in [('plumb',plumb),('prism',prism),('receiver',receiver)]:
        overlap=tree(objects).overlap(fixed)
        if overlap:failures.append({'frame':f,'group':name,'intersecting_triangle_pairs':len(overlap)})
report={'sampled_frames':len(set(frames)),'all_passed':not failures,'failures':failures,'scope':'Both suspended masses and receiver dish against actual fixed crescent meshes during operation/parking; intended bearings excluded. Disassembly is reviewed separately.'}
(ROOT/'review/F_complete/clearance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('F_CLEARANCE',report,flush=True)
