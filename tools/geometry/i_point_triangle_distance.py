"""Double-precision point/triangle distance for thin source triangles."""
def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def segment_squared(p,a,b):
    u=sub(b,a);t=max(0.,min(1.,dot(sub(p,a),u)/max(dot(u,u),1e-300)));d=tuple(p[i]-a[i]-t*u[i] for i in range(3));return dot(d,d)
def distance_squared(p,a,b,c):
    n=cross(sub(b,a),sub(c,a));n2=dot(n,n)
    if n2>1e-36:
        t=dot(sub(p,a),n)/n2;q=tuple(p[i]-t*n[i] for i in range(3))
        if all(dot(cross(sub(v,u),sub(q,u)),n)>=-1e-8*n2 for u,v in [(a,b),(b,c),(c,a)]):
            d=sub(p,q);return dot(d,d)
    return min(segment_squared(p,a,b),segment_squared(p,b,c),segment_squared(p,c,a))
