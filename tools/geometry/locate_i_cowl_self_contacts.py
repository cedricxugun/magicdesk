import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';s=json.loads((OUT/'problem.json').read_text());inverse=Matrix(s['mouth_matrix_blender']).inverted();rows=[]
for m in s['meshes']:
    v=[Vector(p)for p in m['vertices']];faces=[tuple(f)for f in m['triangles']];tree=BVHTree.FromPolygons(v,faces,all_triangles=True);pairs=[];all_points=[]
    for i,j in tree.overlap(tree):
        a=faces[i];b=faces[j]
        if i>=j or set(a)&set(b):continue
        p=[v[k]for k in a];q=[v[k]for k in b];na=(p[1]-p[0]).cross(p[2]-p[0]).normalized();nb=(q[1]-q[0]).cross(q[2]-q[0]).normalized();common=sum(any((x-y).length<2e-7 for y in q)for x in p);plane=max(abs((x-p[0]).dot(na))for x in q);points=[inverse@x for x in p+q];all_points+=points
        if len(pairs)<40:pairs.append({'faces':[i,j],'vertices':[a,b],'points_mouth':[list(x)for x in points],'normal_dot':na.dot(nb),'plane_distance':plane,'geometrically_common_vertices':common})
    rows.append({'mesh':m['mesh'],'bounds_mouth':[[min(p[k]for p in all_points)for k in range(3)],[max(p[k]for p in all_points)for k in range(3)]]if all_points else None,'sample_pairs':pairs})
    print(m['mesh'],rows[-1]['bounds_mouth'],[{k:r[k]for k in ['faces','normal_dot','plane_distance','geometrically_common_vertices']}for r in pairs[:5]],flush=True)
(OUT/'source_self_contact_locations.json').write_text(json.dumps(rows,indent=2)+'\n')
