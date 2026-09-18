"""Double-precision separating-axis witnesses for two triangle surfaces."""
import math
def sub(a,b):return tuple(float(a[i])-float(b[i]) for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def prepare(points):
    points=[tuple(float(x) for x in p) for p in points];edges=[sub(points[(i+1)%3],points[i]) for i in range(3)];normal=cross(edges[0],edges[1])
    return {'points':points,'edges':edges,'normal':normal,'edge_normals':[cross(normal,e) for e in edges],'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def separated_prepared(pa,pb,tolerance=1e-7):
    for i in range(3):
        gap=max(pa['min'][i]-pb['max'][i],pb['min'][i]-pa['max'][i])
        if gap>tolerance:return {'gap':gap,'axis':tuple(float(i==j) for j in range(3))}
    a=pa['points'];b=pb['points'];ea=pa['edges'];eb=pb['edges'];na=pa['normal'];nb=pb['normal']
    axes=[na,nb]+[cross(x,y) for x in ea for y in eb]+pa['edge_normals']+pb['edge_normals']
    for axis in axes:
        length=math.sqrt(dot(axis,axis))
        if length<1e-24:continue
        axis=tuple(x/length for x in axis);pa=[dot(p,axis) for p in a];pb=[dot(p,axis) for p in b];gap=max(min(pb)-max(pa),min(pa)-max(pb))
        if gap>tolerance:return {'gap':gap,'axis':axis}
    return None
def separation(a,b,tolerance=1e-7):return separated_prepared(prepare(a),prepare(b),tolerance)

def self_check():
    a=[(0,0,0),(1,0,0),(0,1,0)]
    assert separation(a,[(0,0,.0002),(1,0,.0002),(0,1,.0002)])['gap']>.00019
    assert separation(a,[(.6,.6,0),(1.6,.6,0),(.6,1.6,0)])
    assert separation(a,[(.2,.2,0),(.8,.2,0),(.2,.8,0)]) is None
    assert separation(a,[(.2,.2,-1),(.2,.2,1),(.8,.2,0)]) is None
