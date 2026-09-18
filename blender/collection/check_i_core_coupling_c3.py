"""Check the actual new C3 fastening/bridge solids against their surroundings."""
import bpy,json,hashlib,itertools
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_c_core/continuous_c3';spec=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=np.array([e.matrix_world@p.co for p in m.vertices]);t=[tuple(f.vertices) for f in m.loop_triangles];e.to_mesh_clear()
    return {'tree':BVHTree.FromPolygons(v.tolist(),t,all_triangles=True),'vertices':v,'triangles':np.array(t,dtype=int),'minimum':v.min(axis=0),'maximum':v.max(axis=0)}
def overlap(a,b):
    if np.any(a['minimum']>b['maximum']) or np.any(b['minimum']>a['maximum']):return []
    return a['tree'].overlap(b['tree'])
names=[name for name in spec['core_hardware'] if name.startswith('IC3_') and name not in spec['core_meshes']]
sources={name:geometry(bpy.data.objects[name]) for name in names};contacts=[];fastener_internal=[];plane_mates=[]
mate_contracts={frozenset((r['positive'],r['negative'])):r for r in spec.get('coupling_mating_planes',[])}
internal_pairs={frozenset((name,name+'_Head')):(name,name+'_Head') for name in spec['coupling_fasteners']}
for sign in [-1,1]:internal_pairs[frozenset(('IC3_CouplerLoadPin','IC3_CouplerLoadCap_'+str(sign)))]=('IC3_CouplerLoadPin','IC3_CouplerLoadCap_'+str(sign))
internal_pairs[frozenset(('IC3_RailLoadPin','IC3_RailLoadCap_Front'))]=('IC3_RailLoadPin','IC3_RailLoadCap_Front')
for frame in [1,17,33,49,65,81,97,113,129,145,161,177,193]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    targets={name:geometry(bpy.data.objects[name]) for name in spec['hardware'] if name not in spec['core_meshes']}
    for name in names:
        for other,target in targets.items():
            if name==other or (other in sources and name>other):continue
            if frame!=1 and other.startswith(('IC1_','IC2_','IC3_')):continue
            pairs=overlap(sources[name],target)
            if not pairs:continue
            row={'frame':frame,'a':name,'b':other,'triangles':len(pairs)};key=frozenset((name,other));accepted=False
            if key in internal_pairs:
                shaft,head=internal_pairs[key];inverse=bpy.data.objects[head].matrix_world.inverted();vertices=targets[shaft]['vertices']
                from mathutils import Vector
                tip=max((inverse@Vector(p)).z for p in vertices)
                if -.0015<=tip<=.00002:row['shaft_tip_in_head_local_z']=tip;fastener_internal.append(row);accepted=True
            if not accepted and key in mate_contracts:
                mate=mate_contracts[key];normal=np.array(mate['normal']);point=np.array(mate['point'])
                indices_a=sorted(set(k for i,j in pairs for k in sources[name]['triangles'][i]));indices_b=sorted(set(k for i,j in pairs for k in target['triangles'][j]))
                a_side=(sources[name]['vertices'][indices_a]-point)@normal;b_side=(target['vertices'][indices_b]-point)@normal
                positive,negative=(a_side,b_side) if mate['positive']==name else (b_side,a_side)
                if float(positive.min())>=-.000002 and float(negative.max())<=.000002:
                    row.update({'purpose':mate['purpose'],'positive_min':float(positive.min()),'negative_max':float(negative.max())});plane_mates.append(row);accepted=True
            if not accepted:contacts.append(row)
    print('C3_COUPLING_MECHANISM',frame,len(contacts),flush=True)
mouth=[o for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH'];mouth_contacts=[]
for frame in [1,49,103,145,181,217,265,337,433]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for obj in mouth:
        target=geometry(obj)
        for name,source in sources.items():
            pairs=overlap(source,target)
            if pairs:mouth_contacts.append({'frame':frame,'coupling':name,'mouth':obj.name,'triangles':len(pairs)})
    print('C3_COUPLING_A',frame,len(mouth_contacts),flush=True)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':not contacts and not mouth_contacts,'coupling_parts':names,'hardware_contacts':contacts,'fastener_internal_contacts':fastener_internal,'verified_plane_mates':plane_mates,'mouth_contacts':mouth_contacts,'scope':'Actual C3 coupling/bridge solids vs hardware over sampled B movement and nine A poses. Separate declared head/shank joins only when measured tips remain inside head solids; accept declared planar seats only when actual intersecting triangles stay on opposite sides within 2e-6. No blanket pair exemption. Does not replace core/body, global containment, native interaction or art checks.'}
(OUT/'coupling_fit_check.json').write_text(json.dumps(report,indent=2)+'\n');print('C3_COUPLING_RESULT',report['passed'],flush=True)
