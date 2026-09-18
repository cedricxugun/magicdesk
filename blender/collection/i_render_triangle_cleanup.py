"""Freeze actual render triangles and remove only opposed, zero-thickness fins."""
import bpy,bmesh

def repair(o,connected_fins=False):
    old=o.data;old.calc_loop_triangles();triangles=list(old.loop_triangles);edges={};groups={}
    for i,t in enumerate(triangles):
        f=tuple(t.vertices);groups.setdefault(tuple(sorted(f)),[]).append(i)
        for k,a in enumerate(f):edges.setdefault(tuple(sorted((a,f[(k+1)%3]))),[]).append(i)
    removed=set();details=[]
    for vertices,ids in groups.items():
        if len(ids)!=2:continue
        a=tuple(triangles[ids[0]].vertices);b=tuple(reversed(triangles[ids[1]].vertices))
        if b not in [a,a[1:]+a[:1],a[2:]+a[:2]]:continue
        counts=sorted(len(edges[tuple(sorted((a[k],a[(k+1)%3])))]) for k in range(3))
        if counts!=[2,2,4] and not (connected_fins and min(counts)>=2 and max(counts)>=4):continue
        removed.update(ids);details.append({'vertices':list(vertices),'triangle_indices':ids,'polygon_indices':[triangles[i].polygon_index for i in ids],'proof':'Exact same vertex set, opposite winding, attached through one four-face edge; zero enclosed thickness and canceling signed volume.'})
    # Keep the exact tessellation even when there is no fin. Later coplanar
    # cleanup must operate on the same triangles as the actual render.
    kept=[t for i,t in enumerate(triangles) if i not in removed];used=sorted({v for t in kept for v in t.vertices});mapping={v:i for i,v in enumerate(used)}
    mesh=bpy.data.meshes.new(o.name+'_RenderTriangleRepair');mesh.from_pydata([tuple(old.vertices[i].co) for i in used],[],[tuple(mapping[i] for i in t.vertices) for t in kept]);mesh.update()
    for material in old.materials:mesh.materials.append(material)
    for face,t in zip(mesh.polygons,kept):face.material_index=old.polygons[t.polygon_index].material_index;face.use_smooth=old.polygons[t.polygon_index].use_smooth
    for layer in old.uv_layers:
        uv=mesh.uv_layers.new(name=layer.name)
        for i,t in enumerate(kept):
            for j,loop in enumerate(t.loops):uv.data[i*3+j].uv=layer.data[loop].uv
    # Preserve source wall/provenance fields when this helper is used on a
    # formed shell rather than a plain frame. UVs and normals are handled above.
    for attribute in old.attributes:
        if attribute.name.startswith('.') or attribute.name in mesh.attributes or attribute.domain not in ['POINT','FACE']:continue
        property_name='vector' if attribute.data_type=='FLOAT_VECTOR' else 'color' if attribute.data_type in ['FLOAT_COLOR','BYTE_COLOR'] else 'value'
        if not attribute.data or not hasattr(attribute.data[0],property_name):continue
        copied=mesh.attributes.new(attribute.name,attribute.data_type,attribute.domain);indices=used if attribute.domain=='POINT' else [t.polygon_index for t in kept]
        for i,source_index in enumerate(indices):setattr(copied.data[i],property_name,getattr(attribute.data[source_index],property_name))
    mesh.normals_split_custom_set([old.corner_normals[i].vector.copy() for t in kept for i in t.loops])
    bm=bmesh.new();bm.from_mesh(mesh);bad=[{'faces':len(e.link_faces),'length':e.calc_length(),'points':[list(v.co) for v in e.verts]} for e in bm.edges if not e.is_manifold];assert not bad,('Triangulated fin repair left an open mesh',o.name,bad[:12]);bm.free();o.data=mesh
    return {'removed_opposed_triangles':len(removed),'details':details,'geometry_changed':bool(removed),'triangulation_frozen':True,'other_render_triangles_preserved':len(kept)}
