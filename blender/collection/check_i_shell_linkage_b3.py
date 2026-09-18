"""Finite B3 geometry checks. Does not treat a valid bare-panel path as acceptance."""
import bpy,bmesh,json,hashlib,itertools,sys
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_b_shell/linkage_b3'
argument=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--report=')),None)
if argument:OUT=(ROOT/argument).parent
spec=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=np.array([e.matrix_world@p.co for p in m.vertices]);tri=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    return v,tri
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t,all_triangles=True),v.min(axis=0),v.max(axis=0)
def overlap(a,b):
    if np.any(a[1]>b[2]) or np.any(b[1]>a[2]):return 0
    return len(a[0].overlap(b[0]))
hardware=[bpy.data.objects[n] for n in spec['hardware']];panels=[bpy.data.objects[r['mesh']] for r in spec['rig']]
topology=[]
topology_objects=hardware+([bpy.data.objects[spec['fixed_collar']]] if 'formed_ports' in spec else [])
for o in topology_objects:
    bm=bmesh.new();bm.from_mesh(o.data)
    remaining=set(bm.verts);components=0
    while remaining:
        components+=1;stack=[remaining.pop()]
        while stack:
            v=stack.pop()
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in remaining:remaining.remove(other);stack.append(other)
    topology.append({'name':o.name,'components':components,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'volume':bm.calc_volume(signed=True)});bm.free()
fixed_names=[spec['fixed_collar']]+[o.name for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH']
vp=[];tri=[]
for name in fixed_names:
    v,t=geometry(bpy.data.objects[name]);offset=len(vp);vp.extend(v.tolist());tri.extend(tuple(i+offset for i in f) for f in t)
fixed=tree(np.array(vp),tri)
panel_contacts=[];fixed_contacts=[];fork_contacts=[];closures=[]
frames=list(range(1,194,16))+[225,241,273,305,337,369,401,417]
for frame in frames:
    scene.frame_set(frame);bpy.context.view_layer.update()
    hs={o.name:tree(*geometry(o)) for o in hardware};ps={o.name:tree(*geometry(o)) for o in panels}
    for pn,p in ps.items():
        for hn,h in hs.items():
            count=overlap(p,h)
            if count:panel_contacts.append({'frame':frame,'panel':pn,'hardware':hn,'triangles':count})
    for hn,h in hs.items():
        count=overlap(h,fixed)
        if count:
            detail={'frame':frame,'hardware':hn,'triangles':count}
            if frame==1:
                detail['actual_components']=[]
                for name in fixed_names:
                    n=overlap(h,tree(*geometry(bpy.data.objects[name])))
                    if n:detail['actual_components'].append({'name':name,'triangles':n})
            fixed_contacts.append(detail)
    forks=[o for o in hardware if o.name.startswith('IB3_Fork_')]
    for a,b in itertools.combinations(forks,2):
        count=overlap(hs[a.name],hs[b.name])
        if count:
            av,at=geometry(a);indices=sorted(set(i for i,j in hs[a.name][0].overlap(hs[b.name][0])))
            points=np.array([av[list(at[i])].mean(axis=0) for i in indices])
            fork_contacts.append({'frame':frame,'a':a.name,'b':b.name,'triangles':count,'a_hit_centroid':points.mean(axis=0).tolist(),'a_hit_bounds':[points.min(axis=0).tolist(),points.max(axis=0).tolist()]})
    for row in spec['rig']:
        for arm_name,first,last in zip(row['link_pivots'],['a','d'],['b0','c0']):
            arm=bpy.data.objects[arm_name];panel=bpy.data.objects[row['panel_pivot']];carrier=bpy.data.objects[row['fixed_carrier']]
            offset=Vector(row['axis'])*float(row.get('ab_axis_offset',0.)) if first=='a' else Vector()
            length=(Vector(row[last])-Vector(row[first])).length
            errors=[(arm.matrix_world.translation-carrier.matrix_world@(Vector(row[first])+offset)).length,(arm.matrix_world@Vector((length,0,0))-panel.matrix_world@(Vector(row[last])+offset)).length]
            closures.append({'frame':frame,'arm':arm_name,'endpoint_error':max(errors)})
    print('B3_FINITE_SWEEP',frame,'panel_hits',len(panel_contacts),'fixed_hits',len(fixed_contacts),'fork_hits',len(fork_contacts),flush=True)
passed=not panel_contacts and not fixed_contacts and not fork_contacts and all(t['components']==1 and t['nonmanifold']==0 and t['tiny_faces']==0 and t['volume']>0 for t in topology) and max(c['endpoint_error'] for c in closures)<.00002
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':passed,'frames':frames,'topology':topology,'panel_hardware_contacts':panel_contacts,'fixed_A_hardware_contacts':fixed_contacts,'fork_pair_contacts':fork_contacts,'closures':closures,'max_endpoint_error':max(c['endpoint_error'] for c in closures),'scope':'Finite hardware topology and panel/hardware, A REST/fixed collar/hardware, fork/fork triangle contacts, source endpoint closure over sampled open/reverse poses. No all-hardware pair/containment, optics/moving A, runtime or art acceptance. Provisional C supports require fitting.'}
(OUT/'finite_geometry_check.json').write_text(json.dumps(report,indent=2)+'\n');print('B3_FINITE_RESULT',passed,flush=True)
