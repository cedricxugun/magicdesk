"""Remove isolated CSG fins and collapse subprecision coplanar face fragments."""
import bmesh

def repair(bm):
    fins=[]
    for f in bm.faces:
        if len(f.edges)!=3 or sorted(len(e.link_faces) for e in f.edges)!=[1,1,3]:continue
        shared=next(e for e in f.edges if len(e.link_faces)==3)
        # The fin has two free edges and touches the otherwise closed surface
        # along one edge only; removing it leaves those two wall faces intact.
        if max(e.calc_length() for e in f.edges)<.01:
            fins.append(f)
    removed=[{'vertices':[list(v.co) for v in f.verts],'area':f.calc_area()} for f in fins]
    if fins:bmesh.ops.delete(bm,geom=fins,context='FACES_ONLY')
    loose=[e for e in bm.edges if not e.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
    loose_vertices=[v for v in bm.verts if not v.link_edges]
    if loose_vertices:bmesh.ops.delete(bm,geom=loose_vertices,context='VERTS')
    dissolved=0
    for _ in range(64):
        bm.normal_update();choice=None
        for face in bm.faces:
            if face.calc_area()>=1e-12:continue
            for edge in sorted(face.edges,key=lambda e:e.calc_length(),reverse=True):
                if len(edge.link_faces)!=2:continue
                other=next(f for f in edge.link_faces if f!=face)
                if other.calc_area()<1e-10:continue
                origin=other.verts[0].co
                if max(abs((v.co-origin).dot(other.normal)) for v in face.verts)<1e-6:
                    choice=edge;break
            if choice:break
        if choice is None:break
        bmesh.ops.dissolve_edges(bm,edges=[choice],use_verts=False,use_face_split=False);dissolved+=1
    return {'removed_open_fins':removed,'collapsed_subprecision_coplanar_faces':dissolved}
