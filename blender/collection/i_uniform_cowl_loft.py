"""Uniform parametric cowl sampling with a zipper to the retained body section."""
import bisect,math
from mathutils import Vector
def add(bm,world,inverse,center,back,right,up,cap_loops,angles,fraction,required_radius,front_depth,end_depth,around=128,depth_steps=48,wall_steps=4):
    definitions=[];records=[]
    def interpolate(knots,points,value):
        if value<=knots[0]:return points[0].copy()
        if value>=knots[-1]:return points[-1].copy()
        i=bisect.bisect_right(knots,value)-1;f=(value-knots[i])/(knots[i+1]-knots[i]);return points[i].lerp(points[i+1],f)
    for outer,inner,caps in cap_loops:
        first=angles[outer[0]];span=angles[outer[-1]]-first
        rails=[]
        for arc in [outer,inner]:rails.append(([(angles[v]-first)/span for v in arc],[world@v.co for v in arc]))
        ends=[([fraction[v]for v in chain],[world@v.co for v in chain])for chain in caps]
        d={'outer':outer,'inner':inner,'caps':caps,'first':first,'span':span,'rails':rails,'ends':ends};definitions.append(d)
        for v in outer+inner+caps[0][1:-1]+caps[1][1:-1]:
            w=fraction[v];theta=angles[v];start=center+back*front_depth+(right*math.cos(theta)+up*math.sin(theta))*(.70*(.962158*(1-w)+.927872*w));records.append({'end':list(world@v.co),'start':list(start),'wall_fraction':w})
    def point(d,u,w,t):
        if w<=0.:end=interpolate(*d['rails'][0],u)
        elif w>=1.:end=interpolate(*d['rails'][1],u)
        elif u<=0.:end=interpolate(*d['ends'][0],w)
        elif u>=1.:end=interpolate(*d['ends'][1],w)
        else:end=interpolate(*d['rails'][0],u).lerp(interpolate(*d['rails'][1],u),w)
        theta=d['first']+d['span']*u;start=center+back*front_depth+(right*math.cos(theta)+up*math.sin(theta))*(.70*(.962158*(1-w)+.927872*w));c1=start+back*(end_depth-front_depth)*.30;c2=end-back*(end_depth-front_depth)*.30
        return start*(1-t)**3+c1*(3*(1-t)**2*t)+c2*(3*(1-t)*t*t)+end*t**3
    bulge=0.
    for d in definitions:
        samples=sorted(set(d['rails'][1][0]+[i/around for i in range(around+1)]))
        for j in range(1,depth_steps):
            t=j/depth_steps
            for u in samples:
                p=point(d,u,1.,t);axial=(p-center).dot(back);radius=(p-center-back*axial).length;needed=max(0.,required_radius(axial/.70)-radius);bulge=max(bulge,needed/math.sin(math.pi*t)**2)
    def formed(d,u,w,t):
        p=point(d,u,w,t);radial=p-center-back*(p-center).dot(back)
        return p+radial.normalized()*bulge*math.sin(math.pi*t)**2
    statistics=[]
    for d in definitions:
        samples=[(i/around,0.)for i in range(around+1)]+[(1.,j/wall_steps)for j in range(1,wall_steps+1)]+[(i/around,1.)for i in range(around-1,-1,-1)]+[(0.,j/wall_steps)for j in range(wall_steps-1,0,-1)]
        def phase(u,w):
            if w==0.:return u
            if u==1.:return 1.+w
            if w==1.:return 3.-u
            return 4.-w
        phases=[phase(u,w)for u,w in samples];rings=[]
        for j in range(depth_steps):rings.append([bm.verts.new(inverse@formed(d,u,w,j/depth_steps))for u,w in samples])
        count=len(samples)
        for j in range(depth_steps-1):
            for k in range(count):bm.faces.new((rings[j][k],rings[j][(k+1)%count],rings[j+1][(k+1)%count],rings[j+1][k]))
        outer,inner,caps=d['outer'],d['inner'],d['caps'];body=outer+caps[1][1:-1]+list(reversed(inner))+list(reversed(caps[0][1:-1]));body_phases=[]
        outer_set=set(outer);inner_set=set(inner);end_set=set(caps[1][1:-1])
        for v in body:
            u=(angles[v]-d['first'])/d['span']
            body_phases.append(u if v in outer_set else 3.-u if v in inner_set else 1.+fraction[v]if v in end_set else 4.-fraction[v])
        assert all(b>=a-1e-10 for a,b in zip(body_phases,body_phases[1:]))
        i=j=0;last=rings[-1]
        while i<len(last)or j<len(body):
            a=phases[i+1]if i+1<len(last)else 4.;b=body_phases[j+1]if j+1<len(body)else 4.;va=last[i%len(last)];vb=body[j%len(body)]
            if abs(a-b)<1e-12:
                bm.faces.new((va,last[(i+1)%len(last)],body[(j+1)%len(body)],vb));i+=1;j+=1
            elif a<b:bm.faces.new((va,last[(i+1)%len(last)],vb));i+=1
            else:bm.faces.new((va,body[(j+1)%len(body)],vb));j+=1
        # A proper annular-sector cap; never a single concave face across the mouth.
        grid={(round(u*around),round(w*wall_steps)):v for (u,w),v in zip(samples,rings[0])}
        for i in range(around+1):
            for j in range(wall_steps+1):
                if (i,j)not in grid:grid[i,j]=bm.verts.new(inverse@formed(d,i/around,j/wall_steps,0.))
        for i in range(around):
            for j in range(wall_steps):bm.faces.new((grid[i,j],grid[i+1,j],grid[i+1,j+1],grid[i,j+1]))
        statistics.append({'uniform_ring_vertices':count,'depth_rows':depth_steps,'around_steps':around,'wall_steps':wall_steps,'original_body_section_vertices':len(body)})
    return {'bulge':bulge,'paths':records,'sections':statistics}
