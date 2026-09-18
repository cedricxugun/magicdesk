"""Check actual saved wing meshes through the independent source animation."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'blender/collection/G_butterfly_r2.blend'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if args:source=Path(args[0])
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene;root=bpy.data.objects['GB2_Butterfly'];objects=list(root.children_recursive)
wings=[o for o in objects if 'DomedWingEnamel' in o.name]
body=[o for o in objects if any(k in o.name for k in ['AbdomenSegment','GarnetHead','OpticalEye','SpringAntenna','LegFemur','LegTibia','LegCoxa'])]
assert len(wings)==4
def tree(items):
    verts=[];triangles=[];deps=bpy.context.evaluated_depsgraph_get()
    for obj in items:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();offset=len(verts)
        verts.extend(obj.matrix_world@v.co for v in mesh.vertices)
        triangles.extend(tuple(offset+i for i in p.vertices) for p in mesh.loop_triangles);ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts,triangles,all_triangles=True),verts,len(triangles)
collisions=[];span=0.;height=0.;sampled=[]
for frame in range(1,542,15):
    scene.frame_set(frame);bpy.context.view_layer.update();fixed,_,_=tree(body);surfaces=[]
    for obj in wings:
        surface,vertices,_=tree([obj]);surfaces.append(surface)
        span=max(span,max(abs(v.x) for v in vertices)*2);height=max(height,max(v.z for v in vertices))
        hit=surface.overlap(fixed)
        if hit:
            details=[part.name for part in body if surface.overlap(tree([part])[0])]
            collisions.append({'frame':frame,'wing':obj.parent.name,'against':'head/abdomen/antennae/legs','objects':details,'triangle_pairs':len(hit)})
    for i in range(4):
        for j in range(i+1,4):
            hit=surfaces[i].overlap(surfaces[j])
            if hit:collisions.append({'frame':frame,'wing':wings[i].parent.name,'against':wings[j].parent.name,'triangle_pairs':len(hit)})
    sampled.append(frame)
scene.frame_set(120);bpy.context.view_layer.update();_,_,triangles=tree([o for o in objects if o.type in ['MESH','CURVE','FONT']])
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sampled_frames':sampled,'collisions':collisions,'passed':not collisions,'max_wing_span':span,'wing_height':height,'component_triangles':triangles,'scope':'Wing enamel shells vs each other and head/abdomen/antennae/legs. Does not certify linkage hardware, exact tangencies, record/player clearance or runtime integration.'}
(ROOT/'review/G_optical_curator/butterfly_r2/wing_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('BUTTERFLY_WING_CLEARANCE',json.dumps(report),flush=True)
