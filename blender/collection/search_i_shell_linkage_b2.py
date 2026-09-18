"""Search actual shell anchors and closed four-bar paths; never alter the source.

Candidate ranking only. The separate mesh sweep decides collision validity.
"""
import bpy, json, hashlib, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'review/I_refinement/part_b_shell/panels_b2'
spec = json.loads((OUT / 'build.json').read_text())
assert hashlib.sha256((ROOT / spec['source']).read_bytes()).hexdigest() == spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT / spec['source']))
bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
controls = np.array(spec['profile_controls'])

def profile(z):
    j = min(len(controls)-2, max(0, int(np.searchsorted(controls[:,0],z)-1)))
    a,b=controls[j:j+2]; h=b[0]-a[0]; t=(z-a[0])/h; lo=max(0,j-1); hi=min(len(controls)-1,j+2)
    ma=(controls[j+1,1:]-controls[lo,1:])/(controls[j+1,0]-controls[lo,0])
    mb=(controls[hi,1:]-controls[j,1:])/(controls[hi,0]-controls[j,0])
    return (2*t**3-3*t*t+1)*a[1:]+(t**3-2*t*t+t)*h*ma+(-2*t**3+3*t*t)*b[1:]+(t**3-t*t)*h*mb

def height(q,angle):
    lo,hi=1.02,3.43
    for _ in range(45):
        z=(lo+hi)/2; u=(z-1.02)/2.41
        if 6*u+.42*math.sin(math.pi*u)*math.sin(angle-math.tau*.6*u)<q:lo=z
        else:hi=z
    return (lo+hi)/2

def tree_for(o):
    m=o.data; m.calc_loop_triangles()
    return BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices], [tuple(t.vertices) for t in m.loop_triangles], all_triangles=True)

with bpy.data.libraries.load(str(ROOT/'blender/collection/I_shell_form_b1.blend'),link=False) as (src,dst):
    dst.objects=['IB1_OuterForm']
envelope=dst.objects[0]; bpy.context.collection.objects.link(envelope)
envelope_tree=tree_for(envelope)

def inside(point,margin=.015):
    nearest,normal,_,distance=envelope_tree.find_nearest(Vector(point))
    return distance>margin and (Vector(point)-nearest).dot(normal)<0

def circles(b,d,second,coupler):
    delta=d-b; distance=np.linalg.norm(delta,axis=-1)
    if np.any(distance<abs(second-coupler)+.003) or np.any(distance>second+coupler-.003): return None
    axis=delta/distance[:,None]
    along=(coupler*coupler-second*second+distance*distance)/(2*distance)
    height2=coupler*coupler-along*along
    if np.min(height2)<.003**2:return None
    offset=np.stack((-axis[:,1],axis[:,0]),axis=1)*np.sqrt(height2)[:,None]
    return b+along[:,None]*axis+offset, b+along[:,None]*axis-offset

rows=[]
for row in spec['panels']:
    part=row['index']; obj=bpy.data.objects[row['mesh']]; tree=tree_for(obj); candidates=[]
    for angle in [.25,.55,.85,1.15]:
        radial=np.array([math.cos(angle),math.sin(angle),0.]); up=np.array([0.,0.,1.]); axis=np.cross(radial,up)
        zb=height(part-1+.32,angle); zc=height(part-1+.68,angle)
        center=np.r_[profile((zb+zc)/2)[:2],0.]
        anchors=[]; surfaces=[]
        for z in [zb,zc]:
            origin=center+up*z+radial*2.
            hit=tree.ray_cast(Vector(origin),Vector(-radial),4.)
            if hit[0] is None:break
            inner=tree.ray_cast(hit[0]-Vector(radial)*.00005,Vector(-radial),.25)
            if inner[0] is None or inner[1].dot(Vector(radial))>=0:break
            surface=np.array(inner[0]); surfaces.append(surface)
            inward=np.array(inner[1]);inward-=axis*(inward@axis);inward/=np.linalg.norm(inward)
            # A radial inset from the outer face can still be buried in a steep
            # wall. Locate the real inner face, then recess the complete pin seat.
            anchors.append(surface+inward*.066)
        if len(anchors)!=2:continue
        b0,c0=anchors; bc=np.array([(c0-b0)@radial,(c0-b0)@up]); coupler=float(np.linalg.norm(bc))
        if coupler<.065 or coupler>.32:continue
        for length in [.12,.17,.22,.27,.32]:
            for ratio in [.88,1.,1.12]:
                second=length*ratio
                for degrees in range(-80,81,20):
                    theta0=math.radians(degrees)
                    a=-length*np.array([math.cos(theta0),math.sin(theta0)])
                    world_a=b0+radial*a[0]+up*a[1]
                    if not all(inside(world_a+axis*d,.019) for d in [-.039,0.,.063]):continue
                    for offset in [-12,0,12]:
                        theta_second=theta0+math.radians(offset)
                        d=bc-second*np.array([math.cos(theta_second),math.sin(theta_second)])
                        world_d=b0+radial*d[0]+up*d[1]
                        if np.linalg.norm(d-a)<.06 or not all(inside(world_d+axis*x,.019) for x in [-.039,0.,.063]):continue
                        rest=circles(np.zeros((1,2)),d,second,coupler)
                        if rest is None:continue
                        branch=min(range(2),key=lambda i:np.linalg.norm(rest[i][0]-bc))
                        for travel in [-70,-50,-30,30,50,70]:
                            thetas=theta0+np.linspace(0,math.radians(travel),33)
                            b=a+length*np.stack((np.cos(thetas),np.sin(thetas)),axis=1)
                            choices=circles(b,d,second,coupler)
                            if choices is None:continue
                            c=choices[branch]; rot=np.unwrap(np.arctan2((c-b)[:,1],(c-b)[:,0]))-math.atan2(bc[1],bc[0])
                            if np.max(np.abs(rot))>math.radians(65):continue
                            displacement=radial*b[-1,0]+up*b[-1,1]
                            if np.linalg.norm(displacement)<.065:continue
                            # Desired spread is lower bowl down, upper curl up. This
                            # ranks candidates, without weakening any later collision check.
                            desired_z=(-1 if part<=2 else 1)
                            score=displacement[2]*desired_z+float(b[-1,0])*.45-abs(abs(float(rot[-1]))-.20)*.05
                            matrices=[]
                            for bb,rr in zip(b,rot):
                                r=Matrix.Rotation(float(rr),4,Vector(axis)); world_b=Vector(b0+radial*bb[0]+up*bb[1]); r.translation=world_b-r.to_3x3()@Vector(b0)
                                matrices.append([list(v) for v in r])
                            candidates.append({'score':score,'azimuth':angle,'b0':b0.tolist(),'c0':c0.tolist(),'surface_b':surfaces[0].tolist(),'surface_c':surfaces[1].tolist(),'a':world_a.tolist(),'d':world_d.tolist(),'axis':axis.tolist(),'length_ab':length,'length_dc':second,'length_bc':coupler,'theta0':theta0,'travel':math.radians(travel),'branch':branch,'rotation_final':float(rot[-1]),'matrices':matrices})
    candidates.sort(key=lambda r:r['score'],reverse=True)
    # Keep varied final trajectories, rather than sixty near-duplicate lengths.
    selected=[]; bins=set(); quadrants={}
    for c in candidates:
        end=np.array(c['matrices'][-1]); signature=tuple(np.round(end[:3,3]/.035).astype(int))+(round(c['rotation_final']/.08),)
        if signature in bins:continue
        b0=np.array(c['b0']); displacement=end[:3,:3]@b0+end[:3,3]-b0
        outward=displacement@np.array([math.cos(c['azimuth']),math.sin(c['azimuth']),0.])
        quadrant=(displacement[2]>0,outward>0,c['rotation_final']>0)
        if quadrants.get(quadrant,0)>=90:continue
        quadrants[quadrant]=quadrants.get(quadrant,0)+1
        bins.add(signature); selected.append(c)
    rows.append({'index':part,'mesh':obj.name,'valid_paths_found':len(candidates),'candidates':selected})
    print('B2_SEARCH',part,len(candidates),'distinct',len(selected),flush=True)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'panels':rows,'scope':'Real rear surface anchors offset inside, pivots inside B1 envelope and continuous 33-sample circle solutions. Candidate ranking only, no mesh sweep or acceptance.'}
(OUT/'linkage_search.json').write_text(json.dumps(report,indent=2)+'\n')
