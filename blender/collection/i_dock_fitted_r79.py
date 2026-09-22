"""Clip actual source triangles with shared vertex/edge identity, no distance weld."""
import math,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def surface(obj,outline,inside=False,z_limit=1.4):
    mesh=obj.data;mesh.calc_loop_triangles()
    points=[obj.matrix_world@v.co for v in mesh.vertices]
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
    tree=BVHTree.FromPolygons(points,triangles,all_triangles=True)
    cache={};faces=[]
    def clip(poly,plane,a,b):
        result=[]
        def value(index):
            p=points[index];return (b[0]-a[0])*(p.y-a[1])-(b[1]-a[1])*(p.x-a[0])
        previous=poly[-1];fp=value(previous)
        for current in poly:
            fc=value(current)
            if (fp>=0)!=(fc>=0):
                if abs(fp)<1e-13:cross=previous
                elif abs(fc)<1e-13:cross=current
                else:
                    key=(plane,*sorted((previous,current)))
                    if key not in cache:
                        lo,hi=key[1:];fa,fb=value(lo),value(hi)
                        cache[key]=len(points);points.append(points[lo].lerp(points[hi],fa/(fa-fb)))
                    cross=cache[key]
                if not result or cross!=result[-1]:result.append(cross)
            if fc>=0 and (not result or current!=result[-1]):result.append(current)
            previous,fp=current,fc
        if len(result)>1 and result[-1]==result[0]:result.pop()
        return result
    lo=[min(p[k] for p in outline) for k in range(2)];hi=[max(p[k] for p in outline) for k in range(2)]
    for tri in triangles:
        p=[points[i] for i in tri]
        if any(max(v[k] for v in p)<lo[k] or min(v[k] for v in p)>hi[k] for k in range(2)):continue
        normal=(p[1]-p[0]).cross(p[2]-p[0]).normalized()
        if (normal.z<.15 if inside else normal.z>-.15):continue
        if sum(v.z for v in p)/3>z_limit:continue
        poly=list(tri)
        for i,a in enumerate(outline):
            poly=clip(poly,i,a,outline[(i+1)%len(outline)])
            if len(poly)<3:break
        if len(poly)<3:continue
        area=abs(sum(points[a].x*points[poly[(j+1)%len(poly)]].y-points[a].y*points[poly[(j+1)%len(poly)]].x for j,a in enumerate(poly)))/2
        if area<1e-16:continue
        center=sum((points[i] for i in poly),Vector())/len(poly)
        hit=tree.ray_cast(Vector((center.x,center.y,-5)),Vector((0,0,1)),10.)
        if inside and hit[0] is not None:hit=tree.ray_cast(hit[0]+Vector((0,0,.00001)),Vector((0,0,1)),10.)
        if hit[0] is None or abs(hit[0].z-center.z)>.0001:continue
        faces.append(tuple(poly))
    used=sorted({i for f in faces for i in f});mapping={old:i for i,old in enumerate(used)}
    vertices=[points[i] for i in used];faces=[tuple(mapping[i] for i in f) for f in faces]
    counts=collections.Counter(tuple(sorted((a,f[(i+1)%len(f)]))) for f in faces for i,a in enumerate(f))
    edges=[e for e,n in counts.items() if n==1]
    assert not any(n>2 for n in counts.values()),'Nonmanifold source patch'
    degree=collections.Counter(i for edge in edges for i in edge)
    assert all(n==2 for n in degree.values()),('Open patch perimeter',collections.Counter(degree.values()))
    expected=abs(sum(a[0]*outline[(i+1)%len(outline)][1]-a[1]*outline[(i+1)%len(outline)][0] for i,a in enumerate(outline)))/2
    area=sum(abs(sum(vertices[a].x*vertices[f[(i+1)%len(f)]].y-vertices[a].y*vertices[f[(i+1)%len(f)]].x for i,a in enumerate(f)))/2 for f in faces)
    assert abs(area/expected-1)<.0001,(area,expected)
    return vertices,faces,edges
