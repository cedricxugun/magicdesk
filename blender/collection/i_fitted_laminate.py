"""One constrained triangulation shared by two actual fitted surface layers."""
import bpy,math
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt,convex_hull_2d

def triangles(points,polygons):
    m=bpy.data.meshes.new('LaminateSurfaceProbe');m.from_pydata(points,[],polygons);m.update();m.calc_loop_triangles();result=[[Vector(points[i]) for i in t.vertices] for t in m.loop_triangles];bpy.data.meshes.remove(m);return result

def between(top,bottom,top_offset=-.0002,bottom_offset=.0002):
    upper=triangles(*top[:2]);lower=triangles(*bottom[:2]);coordinates=[];constraints=[]
    for triangle in upper+lower:
        offset=len(coordinates);coordinates.extend(Vector((p.x,p.y)) for p in triangle);constraints.extend((offset+i,offset+(i+1)%3) for i in range(3))
    for source in [top,bottom]:
        if len(source)<4:continue
        for row in source[3]:
            polygon=row['region'];offset=len(coordinates);coordinates.extend(Vector(p) for p in polygon);constraints.extend((offset+i,offset+(i+1)%len(polygon)) for i in range(len(polygon)))
    # A 2D triangulator may remove collinear perimeter vertices that are
    # essential height breakpoints after lifting into 3D. Tie every boundary
    # breakpoint to an interior vertex so those knots cannot disappear.
    hull=[Vector(p) for p in top[4]] if len(top)>4 else [coordinates[i].copy() for i in convex_hull_2d(coordinates)];center=sum(hull,Vector((0.,0.)))/len(hull);boundary=[]
    for i,p in enumerate(coordinates):
        best=None
        for a,b in zip(hull,hull[1:]+hull[:1]):
            dx=float(b.x)-float(a.x);dy=float(b.y)-float(a.y);t=max(0.,min(1.,((float(p.x)-float(a.x))*dx+(float(p.y)-float(a.y))*dy)/max(dx*dx+dy*dy,1e-30)));q=Vector((float(a.x)+dx*t,float(a.y)+dy*t));distance=math.hypot(float(p.x)-float(q.x),float(p.y)-float(q.y))
            if best is None or distance<best[0]:best=(distance,q)
        if best[0]<1e-6:coordinates[i]=best[1];boundary.append(i)
    center_index=len(coordinates);coordinates.append(center);constraints.extend((i,center_index) for i in boundary if (coordinates[i]-center).length>1e-8)
    points,_,faces,*_=delaunay_2d_cdt(coordinates,constraints,[],0,.00000001,False)
    assert points and faces
    maximum_projection_error=0.
    def height(surface,p,planes=None):
        nonlocal maximum_projection_error
        if planes:
            best=None
            for row in planes:
                polygon=row['region'];signed_area=sum(a[0]*polygon[(i+1)%len(polygon)][1]-a[1]*polygon[(i+1)%len(polygon)][0] for i,a in enumerate(polygon))
                if abs(signed_area)<2e-14:continue
                orientation=1. if signed_area>0 else -1.
                inside=min(q[0] for q in polygon)-1e-9<=p.x<=max(q[0] for q in polygon)+1e-9 and min(q[1] for q in polygon)-1e-9<=p.y<=max(q[1] for q in polygon)+1e-9;distance=float('inf')
                for i,a in enumerate(polygon):
                    b=polygon[(i+1)%len(polygon)];dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
                    if length<1e-15:continue
                    if orientation*(dx*(p.y-a[1])-dy*(p.x-a[0]))/length < -1e-9:inside=False
                    t=max(0.,min(1.,((p.x-a[0])*dx+(p.y-a[1])*dy)/(length*length)));distance=min(distance,(p.x-a[0]-dx*t)**2+(p.y-a[1]-dy*t)**2)
                if inside:distance=0.
                if best is None or distance<best[0]:best=(distance,row['plane'])
                if distance==0.:break
            assert best is not None;error=math.sqrt(best[0]);maximum_projection_error=max(maximum_projection_error,error);assert error<.000002,('Outside original clipped plane domain',error)
            nx,ny,nz,d=best[1];return -(nx*p.x+ny*p.y+d)/nz
        best=None
        for triangle in surface:
            a,b,c=triangle;bx=b.x-a.x;by=b.y-a.y;cx=c.x-a.x;cy=c.y-a.y;den=bx*cy-by*cx
            if abs(den)<1e-18:continue
            px=p.x-a.x;py=p.y-a.y;u=(px*cy-py*cx)/den;v=(bx*py-by*px)/den;w=1.-u-v
            if min(u,v,w)>=-1e-7:distance=0.
            else:
                distance=float('inf')
                for first,second in [(a,b),(b,c),(c,a)]:
                    dx=second.x-first.x;dy=second.y-first.y;t=max(0.,min(1.,((p.x-first.x)*dx+(p.y-first.y)*dy)/max(dx*dx+dy*dy,1e-30)))
                    distance=min(distance,(p.x-first.x-dx*t)**2+(p.y-first.y-dy*t)**2)
            z=w*a.z+u*b.z+v*c.z
            if best is None or distance<best[0]:best=(distance,z)
            if distance==0.:break
        assert best is not None
        distance,z=best;error=math.sqrt(distance);maximum_projection_error=max(maximum_projection_error,error)
        assert error<.000002,('Overlay left actual source footprint',error)
        return z
    upper_points=[(p.x,p.y,height(upper,p,top[3] if len(top)>3 else None)+top_offset) for p in points];lower_points=[(p.x,p.y,height(lower,p,bottom[3] if len(bottom)>3 else None)+bottom_offset) for p in points];count=len(points)
    thicknesses=[a[2]-b[2] for a,b in zip(upper_points,lower_points)];assert min(thicknesses)>.005,('Insufficient real seat span',min(thicknesses))
    edge_faces={};area=0.
    for face in faces:
        for k,a in enumerate(face):
            b=face[(k+1)%len(face)];edge_faces.setdefault(tuple(sorted((a,b))),[]).append((a,b))
        area+=abs(sum(points[a].x*points[face[(i+1)%len(face)]].y-points[a].y*points[face[(i+1)%len(face)]].x for i,a in enumerate(face)))/2.
    assert all(len(rows) in [1,2] for rows in edge_faces.values())
    boundary=[rows[0] for rows in edge_faces.values() if len(rows)==1];degree={}
    for a,b in boundary:degree[a]=degree.get(a,0)+1;degree[b]=degree.get(b,0)+1
    assert all(n==2 for n in degree.values()),'Non-manifold clamp perimeter'
    output_faces=[tuple(f) for f in faces]+[tuple(i+count for i in reversed(f)) for f in faces]+[(a,b,b+count,a+count) for a,b in boundary]
    deviations=[]
    for layer,surface,source,offset in [('upper',upper_points,top,top_offset),('lower',lower_points,bottom,bottom_offset)]:
        maximum=0.;where=None
        for f in faces:
            if len(f)!=3:continue
            for weights in [(1/3,1/3,1/3),(.5,.5,0.),(0.,.5,.5),(.5,0.,.5)]:
                x=sum(points[f[i]].x*weights[i] for i in range(3));y=sum(points[f[i]].y*weights[i] for i in range(3));actual=sum(surface[f[i]][2]*weights[i] for i in range(3));expected=height(upper if layer=='upper' else lower,Vector((x,y)),source[3] if len(source)>3 else None)+offset;error=abs(actual-expected)
                if error>maximum:maximum=error;where=[x,y,actual,expected]
        deviations.append({'layer':layer,'maximum_plane_deviation':maximum,'where':where})
    assert max(r['maximum_plane_deviation'] for r in deviations)<min(-top_offset,bottom_offset)*.4,('Lifted surface exceeds fitting allowance',deviations)
    return upper_points+lower_points,output_faces,{'overlay_cells':len(faces),'surface_vertices':count,'projected_area':area,'maximum_surface_projection_error':maximum_projection_error,'surface_deviations':deviations,'minimum_span':min(thicknesses),'maximum_span':max(thicknesses),'top_gap':-top_offset,'bottom_gap':bottom_offset,'method':'Constrained Delaunay arrangement of both real surface edge sets; shared top/bottom topology'}
