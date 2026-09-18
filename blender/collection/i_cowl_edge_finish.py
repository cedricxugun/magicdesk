"""A bonded nickel return built into the existing solid cover edge."""
import bpy,bmesh,math
import numpy as np
from mathutils import Vector
def finish(o,chain,mouth_matrix,clean_precision_edges=False,clamp_overlap=True,graded_cheek_edge=False,adaptive_radius=False,planar_cheek_retopology=False):
    assert chain['closed'];bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();bm.edges.ensure_lookup_table();bm.edges.index_update()
    edges=[bm.edges[i]for i in chain['source_edges']]
    for edge,expected in zip(edges,chain['segments_blender']):
        points=[o.matrix_world@v.co for v in edge.verts]
        assert min(max((points[j]-Vector(expected[j])).length for j in [0,1]),max((points[j]-Vector(expected[1-j])).length for j in [0,1]))<1e-6
    cleanup=[]
    planar_record=None
    if clean_precision_edges or planar_cheek_retopology:
        boundary=bm.edges.layers.int.new('RimSourceBoundary')
        bm.edges.ensure_lookup_table();edges=[bm.edges[i]for i in chain['source_edges']]
        for edge in edges:edge[boundary]=1
        candidates=[e for e in edges if e.calc_length()<1e-6]if clean_precision_edges else []
        for edge in candidates:
            if not edge.is_valid:continue
            a,b=edge.verts;pa=o.matrix_world@a.co;pb=o.matrix_world@b.co
            limit=float(np.spacing(np.float32(max(abs(x)for x in tuple(pa)+tuple(pb)))))
            distance=(pa-pb).length
            delta=[abs(float(pa[k])-float(pb[k]))for k in range(3)]
            # Explicit local geometry edit, not an equality/ULP assertion.
            # This bound is 0.00004% of base D and 1/4000 of the cheek seam.
            assert distance<=1e-6,('Short-edge reconstruction exceeds bound',o.name,distance)
            before=a.co.copy();bmesh.ops.weld_verts(bm,targetmap={b:a});a.co=before
            cleanup.append({'from_world':list(pb),'to_world':list(pa),'distance':distance,'component_displacements':delta,'maximum_float32_ulp_per_component':limit,'world_edit_bound':1e-6,'policy':'Local short-boundary-edge reconstruction; not an exact-coordinate claim'})
        bm.normal_update();edges=[e for e in bm.edges if e[boundary]==1]
        assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts)
        degree={v:sum(e in edges for e in v.link_edges)for e in edges for v in e.verts};assert all(d==2 for d in degree.values())
        if planar_cheek_retopology:
            faces={f for f in bm.faces if all(abs((o.matrix_world@v.co).z-1.702)<5e-7 for v in f.verts)}
            internal=[e for e in bm.edges if e.is_manifold and all(f in faces for f in e.link_faces)]
            assert internal
            bounds_before={tuple(v.co)for e in bm.edges if sum(f in faces for f in e.link_faces)==1 for v in e.verts}
            count=len(internal);bmesh.ops.dissolve_edges(bm,edges=internal,use_verts=False,use_face_split=False);bm.normal_update()
            assert bounds_before<={tuple(v.co)for v in bm.verts};edges=[e for e in bm.edges if e[boundary]==1]
            assert all(e.is_manifold for e in bm.edges)
            planar_record={'removed_internal_edges':count,'plane_world_z':1.702,'plane_vertex_tolerance':5e-7,'boundary_point_coordinates_preserved':True}
    material=bpy.data.materials['Collection_A_Nickel'];slot=len(o.data.materials);o.data.materials.append(material)
    inverse=mouth_matrix.inverted();normal_matrix=o.matrix_world.to_3x3().inverted().transposed();center=Vector((.12,.16,1.96));radii=(1.01,.67,1.10)
    def cap(face):
        point=o.matrix_world@face.calc_center_median();local=inverse@point
        body=Vector(((point[k]-center[k])/(radii[k]*radii[k])for k in range(3))).normalized();radial=(mouth_matrix.to_3x3()@Vector((local.x,local.y,0))).normalized()
        blend=max(0.,min(1.,(.70-local.z)/.30))*max(0.,min(1.,(1.4-math.hypot(local.x,local.y))/.4));normal=body.lerp(radial,blend).normalized()
        return abs((normal_matrix@face.normal).normalized().dot(normal))<.35
    caps={f for e in edges for f in e.link_faces if cap(f)};pending=list(caps)
    while pending:
        for e in pending.pop().edges:
            for f in e.link_faces:
                if f not in caps and cap(f):caps.add(f);pending.append(f)
    for f in caps:f.material_index=slot
    original={tuple(v.co)for v in bm.verts};segments=np.asarray([[tuple(v.co)for v in e.verts]for e in edges]);a=segments[:,0];d=segments[:,1]-a;dd=np.sum(d*d,axis=1)
    if graded_cheek_edge or adaptive_radius:
        chosen={tuple(sorted((tuple(e.verts[0].co),tuple(e.verts[1].co))))for e in edges}
        radius_by_edge={}
        if adaptive_radius:
            loop_vertices={v for e in edges for v in e.verts}
            radii_local={v:min(.0025,.20*min(e.calc_length()for e in v.link_edges))for v in loop_vertices}
            # Bound the radius by nearby face tessellation and carry a gradual
            # change around the loop instead of globally clamping all edges.
            for _ in range(len(loop_vertices)):
                changed=False
                for e in edges:
                    va,vb=e.verts;length=e.calc_length()
                    for v,w in [(va,vb),(vb,va)]:
                        bound=radii_local[w]+.15*length
                        if radii_local[v]>bound:radii_local[v]=bound;changed=True
                if not changed:break
            for e in edges:
                radius_by_edge[tuple(sorted((tuple(e.verts[0].co),tuple(e.verts[1].co))))]=min(radii_local[v]for v in e.verts)
        bm.to_mesh(o.data);bm.free();o.data.update()
        weight=o.data.attributes.get('bevel_weight_edge')or o.data.attributes.new('bevel_weight_edge','FLOAT','EDGE')
        width_records=[]
        for i,e in enumerate(o.data.edges):
            key=tuple(sorted(tuple(o.data.vertices[v].co)for v in e.vertices))
            if key not in chosen:weight.data[i].value=0.;continue
            midpoint=o.matrix_world@((o.data.vertices[e.vertices[0]].co+o.data.vertices[e.vertices[1]].co)*.5)
            t=max(0.,min(1.,(midpoint.z-1.702-.003)/.045));factor=radius_by_edge[key]/.0025 if adaptive_radius else .10+.90*t*t*(3-2*t)
            weight.data[i].value=factor;width_records.append({'midpoint_world':list(midpoint),'requested_width':.0025*factor})
        modifier=o.modifiers.new('Graded cheek-to-hood metal radius','BEVEL');modifier.width=.0025;modifier.segments=4;modifier.limit_method='WEIGHT';modifier.use_clamp_overlap=False;modifier.material=slot;modifier.profile=.5
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=modifier.name)
        bm=bmesh.new();bm.from_mesh(o.data);result={'faces':list(bm.faces)}
    else:
        width_records=[]
        result=bmesh.ops.bevel(bm,geom=edges,offset=.0025,segments=4,profile=.5,affect='EDGES',clamp_overlap=clamp_overlap,material=slot)
    added=[tuple(v.co)for v in bm.verts if tuple(v.co)not in original];distances=[]
    for start in range(0,len(added),256):
        points=np.asarray(added[start:start+256]);delta=points[:,None,:]-a[None,:,:];t=np.clip(np.sum(delta*d[None,:,:],axis=2)/dd[None,:],0,1);q=a[None,:,:]+t[:,:,None]*d[None,:,:];distances.extend(np.sqrt(np.min(np.sum((points[:,None,:]-q)**2,axis=2),axis=1)).tolist())
    assert distances and np.median(distances)>.0007,('Bevel collapsed to negligible width',o.name,float(np.median(distances)))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0,('Bevel opened the source cover',o.name,bad)
    for f in bm.faces:f.smooth=True
    for e in bm.edges:e.smooth=e.is_manifold and e.calc_face_angle()<.65
    row={'mesh':o.name,'precision_edge_cleanup':cleanup,'planar_retopology':planar_record,'graded_widths':width_records,'complete_outer_loop_edges':len(edges),'complete_outer_loop_length':chain['length'],'cap_faces_in_metal':len(caps),'bevel_faces':len(result['faces']),'new_vertices':len(added),'median_actual_bevel_offset':float(np.median(distances)),'minimum_actual_bevel_offset':min(distances),'maximum_actual_bevel_offset':max(distances),'requested_offset':.0025,'construction':'Bonded nickel return and rounded outer edge within the original closed cover solid; travels with that cover, not a floating decoration.'}
    bm.to_mesh(o.data);bm.free();o.data.update();o.data.normals_split_custom_set([(0.,0.,0.)]*len(o.data.loops));return row
