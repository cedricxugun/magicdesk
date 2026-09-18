"""Choose candidate shell paths by actual triangle sweeps, keeping failed trials."""
import bpy,json,hashlib,itertools,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'review/I_refinement/part_b_shell/panels_b2'
spec=json.loads((OUT/'build.json').read_text()); search=json.loads((OUT/'linkage_search.json').read_text())
assert search['source_sha256']==spec['source_sha256']==hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
def raw(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    p=np.array([e.matrix_world@v.co for v in m.vertices]);tri=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return p,tri
def mesh_tree(p,tri,matrix=None):
    if matrix is not None:
        mat=np.array(matrix);p=p@mat[:3,:3].T+mat[:3,3]
    return BVHTree.FromPolygons(p.tolist(),tri,all_triangles=True),p.min(axis=0),p.max(axis=0)
def contacts(a,b):
    if np.any(a[1]>b[2]) or np.any(b[1]>a[2]):return 0
    return len(a[0].overlap(b[0]))
fixed_names=[spec['fixed_collar']]+[o.name for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH']
fixed_points=[];fixed_tri=[]
for name in fixed_names:
    p,t=raw(bpy.data.objects[name]);offset=len(fixed_points);fixed_points.extend(p.tolist());fixed_tri.extend(tuple(i+offset for i in f) for f in t)
fixed=mesh_tree(np.array(fixed_points),fixed_tri)
geometries=[raw(bpy.data.objects[r['mesh']]) for r in search['panels']]
current=[mesh_tree(*g) for g in geometries];rest=list(current);selected=[];failures=[]
nested='--nested-tip' in sys.argv
for i,row in enumerate(search['panels']):
    accepted=None; rejected=[]
    for candidate_index,candidate in enumerate(row['candidates']):
        trees={}; rejection=None
        carried=(i==4 and nested)
        carrier=np.array(selected[4]['matrices'][-1]) if i==5 and nested else np.eye(4)
        # Final/midpoint first reject bad paths cheaply, then fill the full sample set.
        order=[32,16,8,24,4,12,20,28]+[k for k in range(1,32) if k not in [4,8,12,16,20,24,28]]
        for k in order:
            matrix=(carrier@np.array(candidate['matrices'][k])).tolist()
            tree=mesh_tree(*geometries[i],matrix);trees[k]=tree
            if tree[1][2]<.695:rejection={'against':'base_height_envelope','sample':k};break
            count=contacts(tree,fixed)
            if count:rejection={'against':'A_and_fixed_collar','sample':k,'triangles':count};break
            for j,other in enumerate(current):
                if i==j or (carried and j==5):continue
                count=contacts(tree,other)
                if count:rejection={'against':search['panels'][j]['mesh'],'sample':k,'triangles':count};break
            if rejection:break
            if carried:
                tip=mesh_tree(*geometries[5],matrix)
                count=contacts(tip,fixed)
                if count:rejection={'against':'carried_tip_vs_A','sample':k,'triangles':count};break
                for j,other in enumerate(current):
                    if j in [4,5]:continue
                    count=contacts(tip,other)
                    if count:rejection={'against':'carried_tip_vs_'+search['panels'][j]['mesh'],'sample':k,'triangles':count};break
                if rejection:break
        if rejection:rejected.append({'candidate':candidate_index,**rejection})
        else:
            accepted={'index':row['index'],'mesh':row['mesh'],'candidate_index':candidate_index,**candidate}
            if i==5 and nested:
                accepted['local_matrices']=candidate['matrices'];accepted['carrier_matrix']=carrier.tolist();accepted['carrier_panel']=5
                accepted['matrices']=[(carrier@np.array(m)).tolist() for m in candidate['matrices']]
            if carried:
                accepted['carried_panels']=['IB2_Shell_06']
                current[5]=mesh_tree(*geometries[5],candidate['matrices'][32])
            current[i]=trees[32];break
        if (candidate_index+1)%10==0:print('B2_SWEEP_PROGRESS',i+1,candidate_index+1,rejection,flush=True)
    failures.append({'index':row['index'],'rejected':rejected})
    print('B2_SWEEP_SELECTION',i+1,accepted['candidate_index'] if accepted else None,flush=True)
    if accepted is None:break
    selected.append(accepted)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'selection_complete':len(selected)==6,'nested_tip':nested,'panels':selected,'rejected_trials':failures,'samples_per_panel':33,'scope':'Sequential shell motion against actual A REST, fixed collar, already opened lower panels and stationary upper panels, with base-height envelope. Nested-tip trial carries panel 6 on panel 5, then separates the tip. Surface intersection only. Physical optics, A motion, finite links, supports, containment, runtime and art remain unvalidated.'}
(OUT/('linkage_nested_sweep.json' if nested else 'linkage_sweep.json')).write_text(json.dumps(report,indent=2)+'\n')
print('B2_SWEEP_COMPLETE',len(selected)==6,flush=True)
