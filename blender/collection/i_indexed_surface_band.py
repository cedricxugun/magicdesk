"""Clip a source triangle band while preserving edge identity, including nearby sheets."""
from mathutils import Vector

def clip_band(vertices,triangles,distances,width,joint=None):
    points=[Vector(p) for p in vertices];intersections={};faces=[];origins=[]
    def cut(poly,field_id,value):
        if not poly:return []
        result=[];a=poly[-1];da=value(a)
        for b in poly:
            db=value(b)
            if (db<=0)!=(da<=0):
                if abs(da)<1e-12:crossing=a
                elif abs(db)<1e-12:crossing=b
                else:
                    lo,hi=sorted((a,b));key=(field_id,lo,hi)
                    if key not in intersections:
                        first,last=value(lo),value(hi);intersections[key]=len(points);points.append(points[lo].lerp(points[hi],first/(first-last)))
                    crossing=intersections[key]
                if not result or result[-1]!=crossing:result.append(crossing)
            if db<=0 and (not result or result[-1]!=b):result.append(b)
            a,da=b,db
        if len(result)>1 and result[0]==result[-1]:result.pop()
        return result
    for index,triangle in enumerate(triangles):
        if min(distances[i] for i in triangle)>width:continue
        poly=cut(list(triangle),'width',lambda i:distances[i]-width)
        if len(poly)<3:continue
        pieces=[poly]
        if joint:
            joints=joint if isinstance(joint,list) else [joint]
            for j,entry in enumerate(joints):
                low=entry['center']-entry['gap']/2;high=entry['center']+entry['gap']/2;split=[]
                for piece in pieces:
                    split.extend([cut(piece,('below',j),lambda i:points[i].z-low),cut(piece,('above',j),lambda i:high-points[i].z)])
                pieces=[p for p in split if len(p)>=3]
        for piece in pieces:
            if len(piece)>=3:faces.append(tuple(piece));origins.append(index)
    used=sorted({i for face in faces for i in face});mapping={v:i for i,v in enumerate(used)}
    return [points[i] for i in used],[tuple(mapping[i] for i in face) for face in faces],origins
