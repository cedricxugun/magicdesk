"""Clip real mesh triangles for conforming shoes; no scene clearing or saving."""
import bpy,bmesh,math
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

def clipped_surface(objects,outline,frame=None,from_positive=False,z_limit=None,allow_partial=False,normal_limit=.15,with_planes=False,ray_from_positive=None,visible_layer=0,strict_visible_triangle=False):
    frame=frame or Matrix.Identity(4);inverse=frame.inverted();vertices=[];triangles=[]
    deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(vertices)
        vertices += [inverse@e.matrix_world@v.co for v in m.vertices]
        triangles += [tuple(offset+i for i in t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    tree=BVHTree.FromPolygons(vertices,triangles,all_triangles=True)
    lo=[min(p[i] for p in outline) for i in range(2)];hi=[max(p[i] for p in outline) for i in range(2)]
    def clip(poly,a,b):
        out=[];previous=poly[-1];fp=(b[0]-a[0])*(previous.y-a[1])-(b[1]-a[1])*(previous.x-a[0])
        for current in poly:
            fc=(b[0]-a[0])*(current.y-a[1])-(b[1]-a[1])*(current.x-a[0])
            if (fc>=-1e-10)!=(fp>=-1e-10):out.append(previous.lerp(current,fp/(fp-fc)))
            if fc>=-1e-10:out.append(current)
            previous=current;fp=fc
        return out
    vv=[];ff=[];source_planes=[]
    for triangle_index,indices in enumerate(triangles):
        poly=[vertices[i] for i in indices]
        original=[tuple(p) for p in poly]
        if any(max(p[i] for p in poly)<lo[i] or min(p[i] for p in poly)>hi[i] for i in range(2)):continue
        normal=(poly[1]-poly[0]).cross(poly[2]-poly[0]).normalized()
        if (normal.z<normal_limit if from_positive else normal.z>-normal_limit):continue
        center=sum(poly,Vector())/3
        if z_limit is not None and center.z>z_limit:continue
        for i,a in enumerate(outline):
            poly=clip(poly,a,outline[(i+1)%len(outline)])
            if len(poly)<3:break
        if len(poly)<3:continue
        projected_area=abs(sum(p.x*poly[(i+1)%len(poly)].y-p.y*poly[(i+1)%len(poly)].x for i,p in enumerate(poly)))/2.
        if projected_area<1e-14:continue
        center=sum(poly,Vector())/len(poly)
        ray_positive=from_positive if ray_from_positive is None else ray_from_positive
        ray_direction=Vector((0,0,-1 if ray_positive else 1))
        hit=tree.ray_cast(Vector((center.x,center.y,5. if ray_positive else -5.)),ray_direction,10.)
        for _ in range(visible_layer):
            if hit[0] is None:break
            hit=tree.ray_cast(hit[0]+ray_direction*.00001,ray_direction,10.)
        if hit[0] is None or abs(center.z-hit[0].z)>.0001:continue
        if strict_visible_triangle and hit[2]!=triangle_index:continue
        if with_planes:
            a,b,c=original;u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);d=-sum(n[i]*a[i] for i in range(3))
            source_planes.append({'region':[(p.x,p.y) for p in poly],'plane':[*n,d]})
        offset=len(vv);vv.extend(poly)
        for j in range(1,len(poly)-1):ff.append((offset,offset+j,offset+j+1))
    temporary=bpy.data.meshes.new('ActualTriangleShoePatch');temporary.from_pydata(vv,[],ff);temporary.update()
    bm=bmesh.new();bm.from_mesh(temporary);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    points=[v.co.copy() for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];boundary=[tuple(v.index for v in e.verts) for e in bm.edges if e.is_boundary]
    # Degenerate-edge cleanup can merge clipped triangles into n-gons.
    area=sum(abs(sum(points[a].x*points[p[(i+1)%len(p)]].y-points[a].y*points[p[(i+1)%len(p)]].x for i,a in enumerate(p)))/2 for p in faces)
    expected=abs(sum(a[0]*outline[(i+1)%len(outline)][1]-a[1]*outline[(i+1)%len(outline)][0] for i,a in enumerate(outline)))/2
    bm.free();bpy.data.meshes.remove(temporary)
    assert faces and boundary and (0.<area/expected<1.005 if allow_partial else .995<area/expected<1.005),('Incomplete source footprint',area,expected)
    return (points,faces,boundary,source_planes,outline) if with_planes else (points,faces,boundary)

def extruded_patch(points,polygons,edges,top_offset,bottom_offset=None,bottom_z=None):
    count=len(points);top=[(p.x,p.y,p.z+top_offset) for p in points]
    if bottom_z is not None:
        # A flat sole needs its own perimeter cap. Flattening every vertex of
        # the curved top can fold separate triangles onto the same bottom edge.
        adjacency={}
        for a,b in edges:
            adjacency.setdefault(a,[]).append(b);adjacency.setdefault(b,[]).append(a)
        assert all(len(v)==2 for v in adjacency.values()),'Invalid shoe perimeter'
        first=next(iter(adjacency));loop=[first];previous=None;current=first
        while True:
            following=next(v for v in adjacency[current] if v!=previous)
            if following==first:break
            assert following not in loop
            loop.append(following);previous,current=current,following
        assert len(loop)==len(adjacency),'A flat saddle shoe must have one complete perimeter'
        lower=[(points[i].x,points[i].y,bottom_z) for i in loop]
        mapping={v:count+i for i,v in enumerate(loop)}
        faces=[tuple(reversed(p)) for p in polygons]+[tuple(range(count,count+len(loop)))]+[(a,b,mapping[b],mapping[a]) for a,b in edges]
        return top+lower,faces
    lower=[(p.x,p.y,bottom_z if bottom_z is not None else p.z+bottom_offset) for p in points]
    faces=[tuple(reversed(p)) for p in polygons]+[tuple(v+count for v in p) for p in polygons]+[(a,b,b+count,a+count) for a,b in edges]
    return top+lower,faces
