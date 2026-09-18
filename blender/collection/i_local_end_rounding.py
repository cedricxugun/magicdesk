"""Round real end features independently, with measurable geometry change."""
import bmesh,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def apply(o,envelope):
    o.data.calc_loop_triangles();old_tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();initial_volume=bm.calc_volume(signed=True)
    def near(point,limit):
        hit=envelope.find_nearest(o.matrix_world@point);return hit[0] is not None and hit[3]<limit
    flat=[e for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].material_index==e.link_faces[1].material_index and e.calc_face_angle()<.0001 and near((e.verts[0].co+e.verts[1].co)/2,.010)]
    if flat:bmesh.ops.dissolve_edges(bm,edges=flat,use_verts=False,use_face_split=False)
    simplified=0
    for _ in range(3):
        redundant=[]
        for v in bm.verts:
            if len(v.link_edges)!=2 or not near(v.co,.010):continue
            a,b=[e.other_vert(v).co for e in v.link_edges];line=b-a
            if line.length<1e-9:continue
            t=(v.co-a).dot(line)/line.length_squared;distance=(v.co-(a+line*t)).length
            if 0.<t<1. and distance<.000003:redundant.append(v)
        if not redundant:break
        simplified+=len(redundant);bmesh.ops.dissolve_verts(bm,verts=redundant,use_face_split=False,use_boundary_tear=False)
    steps=[];skipped=set()
    for _ in range(128):
        bm.normal_update();candidates=[]
        for edge in bm.edges:
            if edge in skipped or len(edge.link_faces)!=2 or not edge.is_convex or edge.calc_face_angle()<math.radians(110):continue
            if not near((edge.verts[0].co+edge.verts[1].co)/2,.002):continue
            adjacent=[e.calc_length() for v in edge.verts for e in v.link_edges if e!=edge]
            width=min(.0015,.20*min(adjacent,default=0.))
            if width<.00003:skipped.add(edge);continue
            candidates.append((edge.calc_length(),edge,width))
        if not candidates:break
        _,edge,width=max(candidates,key=lambda r:r[0]);center=list((edge.verts[0].co+edge.verts[1].co)/2)
        bmesh.ops.bevel(bm,geom=[edge],offset=width,segments=4,profile=.5,affect='EDGES',clamp_overlap=False)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert not any(not e.is_manifold for e in bm.edges),('Local end rounding opened mesh',o.name,center)
        volume=bm.calc_volume(signed=True);assert volume>0 and abs(volume-initial_volume)/initial_volume<.001,('End rounding exceeded local material allowance',o.name)
        steps.append({'center':center,'actual_offset':width,'segments':4})
    bm.to_mesh(o.data);bm.free();o.data.update();o.data.calc_loop_triangles();maximum_change=0.
    for t in o.data.loop_triangles:
        p=sum((o.matrix_world@o.data.vertices[i].co for i in t.vertices),Vector())/3;hit=old_tree.find_nearest(p)
        if hit[0] is not None:maximum_change=max(maximum_change,hit[3])
    return {'collapsed_coplanar_edges':len(flat),'simplified_contour_vertices':simplified,'rounded_features':steps,'skipped_subprecision_features':len(skipped),'maximum_measured_surface_change':maximum_change,'meaningful_rounding':bool(steps) and maximum_change>.000003}
