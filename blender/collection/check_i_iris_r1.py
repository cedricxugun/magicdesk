"""Measure the actual six-leaf projected opening and housing clearance."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'blender/collection/I_helix_r1.blend';OUT=ROOT/'review/I_refinement/r1'
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);mouth=bpy.data.objects['IH1_Mouth']
leaves=[bpy.data.objects['IH1_IrisLeaf'+str(i)] for i in range(6)];geometry=[]
for leaf in leaves:
    leaf.animation_data_clear();obj=next(c for c in leaf.children if 'IrisLeafSheet' in c.name)
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
    geometry.append((obj,[v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles]));ev.to_mesh_clear()
rows=[];collisions=[];uncovered=[];maximum_radius=0.
for step in range(21):
    fraction=step/20
    for leaf in leaves:leaf.rotation_euler.z=leaf['home_angle']-1.05*fraction
    bpy.context.view_layer.update();trees=[];all_v=[];all_f=[]
    for obj,points,faces in geometry:
        transform=mouth.matrix_world.inverted()@obj.matrix_world;points=[transform@p for p in points]
        maximum_radius=max(maximum_radius,max(math.hypot(p.x,p.y) for p in points));offset=len(all_v);all_v+=points;all_f += [tuple(i+offset for i in face) for face in faces]
        trees.append(BVHTree.FromPolygons(points,faces,all_triangles=True))
    for i in range(6):
        for j in range(i+1,6):
            if trees[i].overlap(trees[j]):collisions.append([fraction,i,j])
    tree=BVHTree.FromPolygons(all_v,all_f,all_triangles=True);radii=[]
    for ray in range(72):
        a=ray*math.tau/72
        def blocked(radius):return tree.ray_cast(Vector((radius*math.cos(a),radius*math.sin(a),-1)),Vector((0,0,1)),2)[0] is not None
        if not blocked(.50):uncovered.append([fraction,ray]);continue
        lo=0.;hi=.50
        for _ in range(15):
            mid=(lo+hi)/2
            if blocked(mid):hi=mid
            else:lo=mid
        radii.append(hi)
    rows.append({'opening':fraction,'minimum_clear_radius':min(radii) if radii else 0.,'maximum_clear_radius':max(radii) if radii else 0.})
monotonic=all(b['minimum_clear_radius']>=a['minimum_clear_radius']-.001 for a,b in zip(rows,rows[1:]))
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'poses':rows,'sheet_intersections':collisions,'uncovered_outer_rays':uncovered,'maximum_sheet_radius':maximum_radius,'passed':not collisions and not uncovered and monotonic and maximum_radius<.833 and rows[-1]['minimum_clear_radius']>.32 and rows[0]['maximum_clear_radius']<.09,'scope':'Actual sheet meshes in mouth frame:21 openings,72 angular rays, pair intersections and radial housing bound. Excludes central piston and fixed carriers; cam drive checked separately; does not certify the whole apparatus.'}
(OUT/'iris_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_IRIS_CHECK',result['passed'],'uncovered',len(uncovered),'collisions',len(collisions),'radius',maximum_radius,rows[0],rows[-1],flush=True)
if not result['passed']:raise SystemExit(1)
