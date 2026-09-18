"""Fit a planar four-bar candidate to real inner-shell attachment points."""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_b_shell/panels_b2';spec=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
controls=np.array(spec['profile_controls'])
def profile(z):
    j=min(len(controls)-2,max(0,int(np.searchsorted(controls[:,0],z)-1)));a=controls[j];b=controls[j+1];h=b[0]-a[0];t=(z-a[0])/h;lo=max(0,j-1);hi=min(len(controls)-1,j+2)
    ma=(controls[j+1,1:]-controls[lo,1:])/(controls[j+1,0]-controls[lo,0]);mb=(controls[hi,1:]-controls[j,1:])/(controls[hi,0]-controls[j,0])
    return (2*t**3-3*t*t+1)*a[1:]+(t**3-2*t*t+t)*h*ma+(-2*t**3+3*t*t)*b[1:]+(t**3-t*t)*h*mb
def height(q,angle):
    lo=1.02;hi=3.43
    for i in range(50):
        z=(lo+hi)/2;u=(z-1.02)/2.41;value=6*u+.42*math.sin(math.pi*u)*math.sin(angle-math.tau*.6*u)
        if value<q:lo=z
        else:hi=z
    return (lo+hi)/2
def intersections(b,d,r,c):
    delta=d-b;distance=np.linalg.norm(delta)
    if not abs(r-c)<distance<r+c:return []
    axis=delta/distance;a=(c*c-r*r+distance*distance)/(2*distance);h=math.sqrt(max(0,c*c-a*a));side=np.array([-axis[1],axis[0]])
    return [b+a*axis+h*side,b+a*axis-h*side]
rows=[];angle=.95;radial=Vector((math.cos(angle),math.sin(angle),0));up=Vector((0,0,1));normal=radial.cross(up)
for row in spec['panels']:
    part=row['index'];o=bpy.data.objects[row['mesh']];m=o.data;m.calc_loop_triangles();vertices=[o.matrix_world@v.co for v in m.vertices];tree=BVHTree.FromPolygons(vertices,[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
    zb=height(part-1+.30,angle);zc=height(part-1+.70,angle);cx,cy,_,_=profile(zb)
    hit=tree.ray_cast(Vector((cx,cy,zb)),radial,2.);assert hit[0] is not None,('No lower shell anchor',part)
    b0=hit[0];hit=tree.ray_cast(b0-radial*.6+up*(zc-zb),radial,1.3);assert hit[0] is not None,('No upper shell anchor',part)
    c0=hit[0];bc=np.array([(c0-b0).dot(radial),(c0-b0).dot(up)]);coupler=float(np.linalg.norm(bc))
    length=min(.24,max(.11,(zc-zb)*1.5));second=length*.92
    theta0=math.radians(-70);theta_second=math.radians(-65)
    a=-length*np.array([math.cos(theta0),math.sin(theta0)]);d=bc-second*np.array([math.cos(theta_second),math.sin(theta_second)])
    choices=intersections(np.zeros(2),d,second,coupler);assert choices
    branch=min(range(2),key=lambda i:np.linalg.norm(choices[i]-bc));samples=[];valid=True
    for k in range(65):
        t=k/64;theta=theta0+math.radians(60)*t;b=a+length*np.array([math.cos(theta),math.sin(theta)])
        choices=intersections(b,d,second,coupler)
        if not choices:valid=False;break
        c=choices[branch];rotation=math.atan2((c-b)[1],(c-b)[0])-math.atan2(bc[1],bc[0])
        world_b=b0+radial*float(b[0])+up*float(b[1]);world_c=b0+radial*float(c[0])+up*float(c[1])
        r=Matrix.Rotation(rotation,4,normal);r.translation=world_b-r.to_3x3()@b0
        samples.append({'release':t,'b':list(world_b),'c':list(world_c),'rotation':rotation,'matrix':[list(v) for v in r]})
    rows.append({'index':part,'mesh':o.name,'b0':list(b0),'c0':list(c0),'a':list(b0+radial*float(a[0])+up*float(a[1])),'d':list(b0+radial*float(d[0])+up*float(d[1])),'axis':list(normal),'length_ab':length,'length_dc':second,'length_bc':coupler,'valid_circle_solutions':valid,'samples':samples})
    print('LINKAGE_CANDIDATE',part,valid,'samples',len(samples),'angle',samples[-1]['rotation'] if samples else None,flush=True)
(OUT/'linkage_candidate.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'panels':rows,'scope':'Actual inner-shell anchor points and four-bar circle solutions only; no collision, support attachment, native or art acceptance. Candidate path must be checked before building hardware.'},indent=2)+'\n')
