"""Closed, conservative manufacturing envelopes of the current throat and collar."""
import bpy,bmesh,math
import numpy as np
from mathutils import Vector

def make(name,vertices,faces,col):
    data=bpy.data.meshes.new(name+'Mesh');data.from_pydata(vertices,[],faces);data.update();o=bpy.data.objects.new(name,data);col.objects.link(o)
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    assert not any(not e.is_manifold for e in bm.edges),name
    bm.to_mesh(data);bm.free();return o

def offset_vertices(o,margin):
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();moves=[]
    for v in bm.verts:
        normals=np.array([list(f.normal) for f in v.link_faces],dtype=float)
        delta=np.linalg.lstsq(normals,np.full(len(normals),margin),rcond=1e-4)[0]
        assert np.linalg.norm(delta)<margin*6,('Unstable keepout miter',o.name,list(v.co),list(delta))
        moves.append((v,Vector(delta)))
    for v,delta in moves:v.co+=delta
    bm.to_mesh(o.data);bm.free();o.data.update();o['keepout_maximum_vertex_shift']=max(delta.length for _,delta in moves)

def core_envelope(placement,col,margin=.004):
    center=placement.translation.copy();n=(placement.to_3x3()@Vector((0,0,1))).normalized();right=(placement.to_3x3()@Vector((1,0,0))).normalized();up=(placement.to_3x3()@Vector((0,1,0))).normalized();scale=placement.to_scale().x
    C=Vector((.12,.16,1.96));radii=Vector((.83,.49,.92));front=.6395*scale;back=.6575*scale;section_depth=.70;neck=.490*scale
    N=160;vertices=[];faces=[]
    def ring(points):
        ids=list(range(len(vertices),len(vertices)+N));vertices.extend(tuple(p) for p in points);return ids
    def circle(radius,depth):return ring([center+n*depth+(right*math.cos(k*math.tau/N)+up*math.sin(k*math.tau/N))*radius for k in range(N)])
    def section(depth,angle):
        qn=Vector(tuple(radii[i]**2*n[i] for i in range(3)));h2=n.dot(qn);c0=(C-center).dot(n);radial=right*math.cos(angle)+up*math.sin(angle);w=sum((radial[i]/radii[i])**2 for i in range(3));e=1.-(depth-c0)**2/h2
        p=C+qn*((depth-c0)/h2)+radial*math.sqrt(max(0.,e)/w);derivative=qn/h2-radial*((depth-c0)/(h2*math.sqrt(max(e,1e-10)*w)));return p,derivative
    # The thin, flared flange belongs to the collar envelope; offsetting its
    # acute front lip independently produces a long, unstable miter.
    rings=[circle(neck,back)]
    starts=[center+n*back+(right*math.cos(k*math.tau/N)+up*math.sin(k*math.tau/N))*neck for k in range(N)];ends=[section(section_depth,k*math.tau/N) for k in range(N)];span=section_depth-back
    for j in range(1,41):
        t=j/40;t2=t*t;t3=t2*t;rings.append(ring([(2*t3-3*t2+1)*p+(t3-2*t2+t)*n*span+(-2*t3+3*t2)*end+(t3-t2)*derivative*span for p,(end,derivative) in zip(starts,ends)]))
    qn=Vector(tuple(radii[i]**2*n[i] for i in range(3)));extent=math.sqrt(n.dot(qn));c0=(C-center).dot(n);a0=math.asin((section_depth-c0)/extent)
    for j in range(1,90):
        a=a0+(math.pi/2-a0)*j/90;rings.append(ring([section(c0+extent*math.sin(a),k*math.tau/N)[0] for k in range(N)]))
    for a,b in zip(rings,rings[1:]):
        faces.extend((a[k],a[(k+1)%N],b[(k+1)%N],b[k]) for k in range(N))
    tip=len(vertices);vertices.append(tuple(C+qn/extent));faces.extend((rings[-1][k],rings[-1][(k+1)%N],tip) for k in range(N));faces.append(tuple(reversed(rings[0])))
    o=make('IT16_CoreKeepout',vertices,faces,col);offset_vertices(o,margin);return o

def collar_envelope(objects,col,margin=.004,extra_points=None):
    points=[o.matrix_world@v.co for o in objects for v in o.data.vertices]+list(extra_points or [])
    def hull(cloud):
        bm=bmesh.new()
        for p in cloud:bm.verts.new(p)
        bmesh.ops.convex_hull(bm,input=list(bm.verts));used={v for f in bm.faces for v in f.verts};discard=[v for v in bm.verts if v not in used]
        if discard:bmesh.ops.delete(bm,geom=discard,context='VERTS')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.normal_update();return bm
    bm=hull(points);expanded=[v.co+v.normal*margin for v in bm.verts];bm.free();bm=hull(expanded);bm.verts.ensure_lookup_table();bm.verts.index_update();vertices=[tuple(v.co) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free()
    return make('IT16_CollarKeepout',vertices,faces,col)
