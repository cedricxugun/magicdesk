"""Form a bounded receiver recess on inner vertices; keep outer faces exact."""
import bmesh,hashlib,struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def exterior_signature(obj):
    mesh=obj.data;attr=mesh.attributes['formed_wall_fraction'];values=[a.value for a in attr.data];rows=[]
    for face in mesh.polygons:
        if any(values[i]>.001 for i in face.vertices):continue
        points=[struct.pack('<3f',*mesh.vertices[i].co) for i in face.vertices]
        rotations=[b''.join(points[i:]+points[:i]) for i in range(len(points))]
        rows.append(min(rotations)+mesh.materials[face.material_index].name.encode())
    return hashlib.sha256(b''.join(sorted(rows))).hexdigest()

def form_recess(obj,mouth_matrix):
    before=exterior_signature(obj);obj.data.calc_loop_triangles();values=[a.value for a in obj.data.attributes['formed_wall_fraction'].data]
    outer=BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],[tuple(t.vertices) for t in obj.data.loop_triangles if max(values[k] for k in t.vertices)<.001],all_triangles=True)
    bm=bmesh.new();bm.from_mesh(obj.data);wall=bm.verts.layers.float['formed_wall_fraction'];region=bm.verts.layers.float.new('IN3_receiver_region');floor_region=bm.verts.layers.float.new('IN3_receiver_floor_region');to_mouth=mouth_matrix.inverted()@obj.matrix_world;from_mouth=to_mouth.inverted()
    for v in bm.verts:
        p=to_mouth@v.co;v[region]=float(v[wall]>.999 and .530<p.z<.720);v[floor_region]=float(v[wall]>.999 and .490<p.z<.770)
    edges=[e for e in bm.edges if all(v[wall]>.999 for v in e.verts) and any(v[floor_region]>.5 for v in e.verts)]
    initial=len(bm.verts)
    bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
    profile=[(.560,.560),(.572,.610),(.578,.622),(.608,.622),(.614,.617),(.620,.606),(.6265,.594),(.638,.574),(.643,.558),(.650,.490)]
    def required(z):
        if z<profile[0][0] or z>profile[-1][0]:return -1.
        for (a,r),(b,s) in zip(profile,profile[1:]):
            if z<=b:return r+(s-r)*(z-a)/(b-a)
        return -1.
    moved=0
    for v in bm.verts:
        if v[wall]<.999:continue
        p=to_mouth@v.co;radius=(p.x*p.x+p.y*p.y)**.5;minimum=required(p.z)
        if minimum<0. or radius<1e-8:continue
        target=max(radius,minimum)+max(.001-abs(radius-minimum),0.)**2/.004
        if target<=radius+1e-10:continue
        p.x*=target/radius;p.y*=target/radius;v.co=from_mouth@p;moved+=1
    projected=set();world_inverse=obj.matrix_world.inverted();wall_goal=.0085
    def project_inner():
        for v in bm.verts:
            if v[wall]<.999 or v[floor_region]<.5:continue
            for _ in range(12):
                p=obj.matrix_world@v.co;near,normal,_,distance=outer.find_nearest(p)
                if near is None or (distance>=wall_goal-1e-7 and (p-near).dot(normal)<0.):break
                v.co=world_inverse@(near-normal*wall_goal);projected.add(v)
    project_inner();refinement=[]
    # Vertex projection alone leaves long chords across the concave receiver.
    # Refine the real offending faces and reproject the new points, then let a
    # separate triangle-distance audit check the saved result.
    for step in range(8):
        bad_faces=set();bad_triangles=0
        for loops in bm.calc_loop_triangles():
            verts=[loop.vert for loop in loops]
            if any(v[wall]<.999 for v in verts) or max(v[region] for v in verts)<.5:continue
            pts=[obj.matrix_world@v.co for v in verts]
            probes=[sum(pts,Vector())/3.,(pts[0]+pts[1])/2.,(pts[1]+pts[2])/2.,(pts[2]+pts[0])/2.]
            bad=max((pts[i]-pts[(i+1)%3]).length for i in range(3))>.012
            for p in probes:
                near,normal,_,distance=outer.find_nearest(p)
                if distance<.0075 or (p-near).dot(normal)>=0.:bad=True;break
            if bad:
                bad_faces.add(loops[0].face);bad_triangles+=1
                for v in verts:v[floor_region]=1.
        refinement.append({'pass':step,'bad_triangles':bad_triangles,'vertices':len(bm.verts)})
        if not bad_faces:break
        selected={e for f in bad_faces for e in f.edges if all(v[wall]>.999 for v in e.verts)}
        assert selected,'No refinable inner edges for receiver error'
        previous=set(bm.verts);bmesh.ops.subdivide_edges(bm,edges=list(selected),cuts=1,use_grid_fill=True)
        for v in set(bm.verts)-previous:
            if v[wall]>.999:v[floor_region]=1.
        assert len(bm.verts)<180000,'Receiver refinement exceeded the shape-study limit'
        project_inner()
    thickened=len(projected)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));count=len(bm.verts);bm.to_mesh(obj.data);bm.free();obj.data.update()
    after=exterior_signature(obj);assert before==after,'Receiver recess changed an outer face'
    return {'mesh':obj.name,'outer_surface_sha256':after,'outer_surface_unchanged':before==after,'added_inner_vertices':count-initial,'moved_inner_vertices':moved,'thickened_inner_vertices':thickened,'adaptive_refinement':refinement,'wall_goal_scene_units':wall_goal,'profile_mouth_local':profile,'scope':'Exact outer-face coordinates/winding/materials preserved. Tagged region persists through displacement so wall probes cannot lose coverage. Actual hardware clearance and remaining wall thickness still require independent checks.'}
