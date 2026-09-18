"""Actual fair-skin triangle self intersections and inward ray thickness."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';s=json.loads((OUT/'build.json').read_text());problem=json.loads((OUT/'problem.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
def intersections(tree,faces):
    result=set()
    for i,j in tree.overlap(tree):
        if i>=j or set(faces[i])&set(faces[j]):continue
        result.add(tuple(sorted((tuple(sorted(faces[i])),tuple(sorted(faces[j]))))))
    return result
def thickness(tree,v,face):
    a,b,c=[v[i]for i in face];normal=(b-a).cross(c-a)
    if normal.length<1e-9:return None
    normal.normalize();p=(a+b+c)/3;hit=tree.ray_cast(p-normal*.00001,-normal,.15)[0]
    return (hit-p).length if hit is not None else None
for original in problem['meshes']:
    o=bpy.data.objects[original['mesh']];o.data.calc_loop_triangles();v=[o.matrix_world@p.co for p in o.data.vertices];f=[tuple(t.vertices)for t in o.data.loop_triangles];old=[Vector(p)for p in original['vertices']];old_faces=[tuple(t)for t in original['triangles']];tree=BVHTree.FromPolygons(v,f,all_triangles=True);before=BVHTree.FromPolygons(old,old_faces,all_triangles=True)
    current_intersections=intersections(tree,f);old_intersections=intersections(before,old_faces);new=current_intersections-old_intersections
    eligible=[face for face in f if all(original['free'][i]and original['outer_radial_surface'][i]for i in face)];stride=max(1,len(eligible)//800);samples=[]
    for face in eligible[::stride]:
        a=thickness(before,old,face);b=thickness(tree,v,face)
        if a is not None and .008<a<.075:samples.append({'vertices':face,'before':a,'after':b,'ratio':b/a if b is not None else None})
    failed=[r for r in samples if r['after']is None or r['after']<.008 or r['ratio']<.60]
    rows.append({'mesh':o.name,'source_self_intersection_pairs':len(old_intersections),'current_self_intersection_pairs':len(current_intersections),'new_self_intersection_pairs':len(new),'new_pairs':[list(r)for r in sorted(new)[:30]],'sample_count':len(samples),'minimum_new_ray_thickness':min((r['after']for r in samples if r['after']is not None),default=None),'failed_thickness_samples':failed,'passed':not new and bool(samples)and not failed})
    print('COWL_THICKNESS',o.name,len(new),len(failed),flush=True)
d={'source_sha256':s['source_sha256'],'passed':all(r['passed']for r in rows),'rows':rows,'scope':'New nonadjacent actual render-triangle self intersections relative to R21, and sampled inward thickness where source rays establish a thin wall. Requires at least 0.008 world thickness and 60 percent source thickness in those samples. Not a global minimum wall or final visual acceptance.'};(OUT/'thickness_check.json').write_text(json.dumps(d,indent=2)+'\n')
