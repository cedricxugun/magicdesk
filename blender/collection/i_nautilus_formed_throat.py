"""Continue each real cowl skin from a common section into the side mouth.

The original skin boundary is retained as the loft's final row. Both wall
surfaces and both sector ends continue to the outlet; no overlay collar hides
an open join. This is a shape correction, not a validated moving mechanism.
"""
import bmesh,math
from mathutils import Vector

def extend_skin(obj,center,back,right,up,body_center,radii,clearance,depth=.30,start=.18):
    bm=bmesh.new();bm.from_mesh(obj.data);bm.normal_update();bm.verts.ensure_lookup_table()
    # The patch builder writes the complete outer layer followed by the inner
    # layer. Carry this identity through edge interpolation at the section;
    # boundary vertex normals mix end/side faces and cannot identify wall side.
    wall=bm.verts.layers.float.new('formed_wall_fraction')
    loft_t=bm.verts.layers.float.new('formed_loft_t')
    endpoint=[bm.verts.layers.float.new('formed_end_'+axis) for axis in ['x','y','z']]
    half=len(bm.verts)//2
    for index,v in enumerate(bm.verts):v[wall]=0. if index<half else 1.;v[loft_t]=-1.
    plane=center+back*depth
    distances=[(v.co-plane).dot(back) for v in bm.verts]
    if max(distances)<=1e-8:
        bm.free();raise AssertionError(('Section removes entire cowl',obj.name))
    has_section=min(distances)<-1e-8
    if has_section:bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=plane,plane_no=back,clear_inner=True)
    def outside_aperture(p,fraction,band=.020):
        axial=(p-center).dot(back);cross=p-center-back*axial
        required=clearance(axial)
        if required<0.:return p
        minimum=required+.004+.024*(1.-fraction)
        rho=cross.length
        # Compact C1 smooth maximum; unchanged outside the blending band.
        radius=max(rho,minimum)+(max(band-abs(rho-minimum),0.)**2/(4.*band) if band>1e-8 else 0.)
        return center+back*axial+cross.normalized()*radius if rho>1e-9 else p
    for v in bm.verts:v.co=outside_aperture(v.co,v[wall])
    bm.normal_update()
    if not has_section:
        bm.to_mesh(obj.data);bm.free();return None
    edges=[e for e in bm.edges if len(e.link_faces)==1 and all(abs((v.co-plane).dot(back))<2e-6 for v in e.verts)]
    assert edges,('Missing section boundary',obj.name)
    boundary=list({v for e in edges for v in e.verts})
    # Ellipsoid section center is offset from the mouth axis; this upward and
    # inward offset is what creates a swept neck instead of a straight sleeve.
    qn=Vector(tuple(radii[i]**2*back[i] for i in range(3)))
    section_center=body_center+qn*((plane-body_center).dot(back)/back.dot(qn))
    paths={};steps=28;starts=[]
    for v in boundary:
        end=v.co.copy();delta=end-section_center
        angle=math.atan2(delta.dot(up),delta.dot(right))
        radial=right*math.cos(angle)+up*math.sin(angle)
        outward=Vector(tuple((end[i]-body_center[i])/(radii[i]**2) for i in range(3))).normalized()
        radius=max(.643,clearance(start)+.028)-.024*v[wall]
        begin=center+back*start+radial*radius
        length=(end-begin).length
        tangent0=back*length*.95
        tangent1=back-outward*back.dot(outward)
        tangent1=tangent1.normalized()*length*.95 if tangent1.length>1e-6 else back*length*.3
        path=[]
        for j in range(steps):
            t=j/steps;t2=t*t;t3=t2*t
            p=(2*t3-3*t2+1)*begin+(t3-2*t2+t)*tangent0+(-2*t3+3*t2)*end+(t3-t2)*tangent1
            # The full A mechanism occupies depth as well as the front disc.
            # Form the shell outside that envelope instead of cutting holes
            # through an inward-pinched connector after it has been modeled.
            p=outside_aperture(p,v[wall],.020*(1.-t))
            new=bm.verts.new(p);new[wall]=v[wall];new[loft_t]=t
            for axis,layer in enumerate(endpoint):new[layer]=end[axis]
            path.append(new)
        path.append(v);paths[v]=path;starts.append(path[0])
    for edge in edges:
        a,b=edge.verts
        for j in range(steps):
            bm.faces.new((paths[a][j],paths[b][j],paths[b][j+1],paths[a][j+1]))
    front=[e for e in bm.edges if len(e.link_faces)==1 and all(abs((v.co-center).dot(back)-start)<2e-6 for v in e.verts)]
    bmesh.ops.holes_fill(bm,edges=front,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
    return {'mesh':obj.name,'section_depth':depth,'lip_depth':start,'boundary_vertices':len(boundary),'loft_steps':steps,'section_center':list(section_center),'join':'shared source boundary vertices, tangent continuation','scope':'Static primary cowl shape only; outlet fit and motion clearance pending'}
