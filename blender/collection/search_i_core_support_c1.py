"""Fit substantial support-leg envelopes to the new metal trunnions and B sweep."""
import bpy,json,hashlib,math,itertools,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_c_core/mount_c1'
spec=json.loads((OUT/'build.json').read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene
points=[];triangles=[];owners=[]
def append_object(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=np.array([e.matrix_world@p.co for p in m.vertices])
    if v[:,2].min()>1.65:e.to_mesh_clear();return
    t=np.array([tuple(f.vertices) for f in m.loop_triangles]);t=t[v[t,2].min(axis=1)<=1.65];offset=len(points)
    points.extend(v.tolist());triangles.extend(tuple(i+offset for i in f) for f in t);owners.extend([o.name+'@'+str(scene.frame_current)]*len(t));e.to_mesh_clear()
scene.frame_set(1);bpy.context.view_layer.update()
for o in bpy.data.collections['MODULE_IAM'].all_objects:
    if o.type=='MESH':append_object(o)
ports='--allow-coaming-ports' in sys.argv
if not ports:append_object(bpy.data.objects[spec['fixed_collar']])
names=[row['mesh'] for row in spec['rig']]+[name for name in spec['hardware'] if not name.startswith(('IB3_Provisional','IC1_')) and name!='IB3_RailRootStudy']
for frame in range(1,194,16):
    scene.frame_set(frame);bpy.context.view_layer.update()
    for name in names:append_object(bpy.data.objects[name])
# Feet must land on the real deck, not on a guessed plane through its raised
# metal traces. Import for read-only fitting; never export a duplicate base.
assert hashlib.sha256((ROOT/'app/assets/helios_model.glb').read_bytes()).hexdigest()==spec['base_sha256']
bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'));bpy.context.view_layer.update();base=bpy.data.objects['BASE_FIXED']
base_points=[];base_tri=[]
for o in [base]+list(base.children_recursive):
    if o.type!='MESH':continue
    m=o.data;m.calc_loop_triangles();offset=len(base_points);base_points.extend(o.matrix_world@v.co for v in m.vertices);base_tri.extend(tuple(i+offset for i in t.vertices) for t in m.loop_triangles);append_object(o)
base_tree=BVHTree.FromPolygons(base_points,base_tri,all_triangles=True)
def flat_foot(foot):
    radial=np.array([foot[0],foot[1],0.]);radial/=np.linalg.norm(radial);tangent=np.array([-radial[1],radial[0],0.])
    for fraction in [0.,.5,1.]:
        for i in range(1 if fraction==0 else 32):
            angle=i*math.tau/32;p=foot+fraction*(radial*.035*math.cos(angle)+tangent*.077*math.sin(angle));origin=Vector((p[0],p[1],1.))
            hit=base_tree.ray_cast(origin,Vector((0,0,-1)),2.)
            if hit[0] is None or abs(hit[0].z-.5625)>.0001:return False
    return True
print('C1_SUPPORT_OBSTACLES',len(points),len(triangles),flush=True)
obstacles=BVHTree.FromPolygons(points,triangles,all_triangles=True)

def envelope(a,k,b):
    vertices=[];faces=[]
    def sphere(center,radius,basis=None):
        base=len(vertices);n=20;lat=12
        scale=np.array([radius]*3) if np.isscalar(radius) else np.array(radius)
        basis=np.eye(3) if basis is None else basis
        vertices.append(tuple(center+basis@(scale*np.array([0,0,-1.]))))
        for j in range(1,lat):
            t=-math.pi/2+math.pi*j/lat
            vertices.extend(tuple(center+basis@(scale*np.array([math.cos(t)*math.cos(i*math.tau/n),math.cos(t)*math.sin(i*math.tau/n),math.sin(t)]))) for i in range(n))
        top=len(vertices);vertices.append(tuple(center+basis@(scale*np.array([0,0,1.]))))
        for i in range(n):faces.append((base,base+1+(i+1)%n,base+1+i));faces.append((top,top-n+i,top-n+(i+1)%n))
        for j in range(lat-2):
            x=base+1+j*n
            for i in range(n):faces.append((x+i,x+(i+1)%n,x+n+(i+1)%n,x+n+i))
    def cylinder(a,b,r):
        d=b-a;d/=np.linalg.norm(d);helper=np.array([0.,0.,1.]) if abs(d[2])<.9 else np.array([1.,0.,0.]);u=np.cross(d,helper);u/=np.linalg.norm(u);v=np.cross(d,u)
        base=len(vertices);n=24
        radii=r if isinstance(r,tuple) else (r,r)
        for c,radius in zip([a,b],radii):vertices.extend(tuple(c+radius*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))) for i in range(n))
        faces.extend([tuple(base+i for i in range(n-1,-1,-1)),tuple(base+n+i for i in range(n))])
        for i in range(n):faces.append((base+i,base+(i+1)%n,base+n+(i+1)%n,base+n+i))
    neck=a+(k-a)/np.linalg.norm(k-a)*.11
    radial=np.array([b[0],b[1],0.]);radial/=np.linalg.norm(radial);tangent=np.array([-radial[1],radial[0],0.]);foot_basis=np.stack((radial,tangent,np.array([0.,0.,1.])),axis=1)
    heel=b+(k-b)/np.linalg.norm(k-b)*.04
    sphere(a,.018);sphere(k,.048);sphere(b,[.032,.051,.054],foot_basis);cylinder(a,neck,(.012,.030));cylinder(neck,k,.030);cylinder(k,heel,.035);cylinder(heel,b,.024)
    return BVHTree.FromPolygons(vertices,faces),vertices

front=np.array(spec['mouth_blender_forward']);front[2]=0.;front/=np.linalg.norm(front)
selected=[];failures=[];previous=[]
for index,anchor in enumerate(spec['mount_anchors']):
    top=np.array(anchor['world']);axis=np.array(anchor['axis_world']);sign=-1 if index==0 else 1;candidates=[]
    feet_cache={}
    for knee_z,knee_depth,foot_depth,spread in itertools.product([.78,.88,.98,1.08,1.18],[-.1,0.,.1,.2,.3,.4,.5,.6,.7],[.35,.40,.45,.50,.55,.60,.65,.70,.75],[-.12,-.06,0.,.06,.12,.18]):
        knee=top+front*knee_depth;knee[2]=knee_z
        foot=top+front*foot_depth+axis*spread*sign;foot[2]=.655
        if np.linalg.norm(foot[:2])>1.15:continue
        key=(foot_depth,spread)
        if key not in feet_cache:feet_cache[key]=flat_foot(foot)
        if not feet_cache[key]:continue
        cost=abs(knee_z-.98)+abs(knee_depth-.45)+abs(foot_depth-.55)+abs(spread)*.8
        candidates.append((cost,knee,foot))
    candidates.sort(key=lambda x:x[0]);tried=0;best_failure=None
    for cost,knee,foot in candidates:
        tried+=1;tree,vertices=envelope(top,knee,foot)
        hits=tree.overlap(obstacles);count=len(hits)
        if count:
            if best_failure is None or count<best_failure['triangles']:
                from collections import Counter
                best_failure={'triangles':count,'knee':knee.tolist(),'foot':foot.tolist(),'against':Counter(owners[j] for i,j in hits).most_common(15)}
            continue
        if any(tree.overlap(t) for t in previous):continue
        selected.append({'anchor':anchor['name'],'top':top.tolist(),'knee':knee.tolist(),'foot':foot.tolist(),'axis':axis.tolist(),'top_eye_radius':.018,'neck_length':.11,'neck_radius_start':.012,'body_radius_upper':.030,'body_radius_lower':.035,'joint_radius':.048,'foot_seat_radial_radius':.034,'foot_seat_tangential_radius':.075,'score':cost,'trials':tried});previous.append(tree);break
    failures.append({'anchor':anchor['name'],'trials':tried,'found':len(selected)>index,'closest_rejected':best_failure});print('C1_SUPPORT_SELECTION',index,len(selected)>index,tried,best_failure,flush=True)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'base_sha256':spec['base_sha256'],'complete':len(selected)==2,'requires_coaming_ports':ports,'supports':selected,'trials':failures,'scope':'Finite leg cylinder/joint sphere envelopes against actual A REST, real BASE_FIXED and thirteen sampled B shell/hardware poses below z1.65, with sampled flat foot patches. Existing provisional legs excluded. Port trial explicitly excludes the unmodified fixed coaming, requiring actual formed ports before any collision claim. Own-joint fitting, final seat triangles, detailed solids, full sweep and art require checks.'}
(OUT/('support_layout_ports.json' if ports else 'support_layout.json')).write_text(json.dumps(report,indent=2)+'\n')
