"""Actual continuous-core self contact, mates, mechanism sweep and A fit."""
import bpy,bmesh,json,hashlib,itertools
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_c_core/continuous_c3';spec=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=np.array([e.matrix_world@p.co for p in m.vertices]);t=np.array([tuple(f.vertices) for f in m.loop_triangles]);e.to_mesh_clear()
    return {'vertices':v,'triangles':t,'tree':BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True),'minimum':v.min(axis=0),'maximum':v.max(axis=0)}
def hits(a,b):
    if np.any(a['minimum']>b['maximum']) or np.any(b['minimum']>a['maximum']):return []
    return a['tree'].overlap(b['tree'])
cores={name:geometry(bpy.data.objects[name]) for name in spec['core_meshes']};topology=[];self_contacts=[]
for name,g in cores.items():
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);left=set(bm.verts);components=0
    while left:
        components+=1;stack=[left.pop()]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in left:left.remove(w);stack.append(w)
    topology.append({'name':name,'components':components,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'volume':bm.calc_volume(signed=True)});bm.free()
    count=sum(i<j and not set(g['triangles'][i]).intersection(g['triangles'][j]) for i,j in g['tree'].overlap(g['tree']))
    if count:self_contacts.append({'name':name,'nonadjacent_triangle_contacts':count})
pair_contacts=[]
for a,b in itertools.combinations(cores,2):
    overlap=hits(cores[a],cores[b])
    if overlap:pair_contacts.append({'a':a,'b':b,'triangles':len(overlap)})

mount=bpy.data.objects['IC3_CouplingMount'].matrix_world;plane=mount@Vector((0,0,.6575));normal=(mount.to_3x3()@Vector((0,0,1))).normalized()
mechanism=[];mating=[];other_names=[name for name in spec['hardware'] if name not in cores]+[r['mesh'] for r in spec['rig']]+[spec['fixed_collar']]
for frame in [1,17,33,49,65,81,97,113,129,145,161,177,193,225,241,273,305,337,369,401,417]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for name in other_names:
        other=geometry(bpy.data.objects[name])
        for core,g in cores.items():
            overlap=hits(g,other)
            if not overlap:continue
            allowed=False
            if core=='IC3_ContinuousLiner' and name=='IC3_CouplingFlange':
                indices=sorted(set(i for a,b in overlap for i in g['triangles'][a]));signed=(g['vertices'][indices]-np.array(plane))@np.array(normal)
                # Only the existing rear plane contact is a mating surface. A
                # body triangle that crosses forward into the flange still fails.
                allowed=float(signed.min())>-.00001
            row={'frame':frame,'core':core,'against':name,'triangles':len(overlap)}
            (mating if allowed else mechanism).append(row)
    print('C3_MECHANISM_FIT',frame,len(mechanism),flush=True)

mouth_spec=json.loads((ROOT/spec['mouth_report']).read_text());layout=json.loads((ROOT/'app'/mouth_spec['music_optics_layout'].removeprefix('res://')).read_text())
with bpy.data.libraries.load(str(ROOT/layout['source']),link=False) as (src,dst):dst.objects=[name for name in src.objects if name.startswith('I_')]
loaded=[o for o in dst.objects if o is not None]
for o in loaded:bpy.context.collection.objects.link(o)
next(o for o in loaded if o.name=='I_MusicOptics').parent=bpy.data.objects['IAM_Mouth']
mouth=[o for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH']+[o for o in loaded if o.type=='MESH' and o.name!=layout['sheet']]
mouth_contacts=[]
for frame in [1,49,103,145,181,217,265,337,433]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for obj in mouth:
        other=geometry(obj)
        for core,g in cores.items():
            overlap=hits(g,other)
            if overlap:mouth_contacts.append({'frame':frame,'core':core,'against':obj.name,'triangles':len(overlap)})
    print('C3_A_FIT',frame,len(mouth_contacts),flush=True)
passed=not self_contacts and not pair_contacts and not mechanism and not mouth_contacts and all(r['components']==1 and r['nonmanifold']==0 and r['tiny_faces']==0 and r['volume']>0 for r in topology)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':passed,'topology':topology,'self_contacts':self_contacts,'core_pair_contacts':pair_contacts,'mechanism_contacts':mechanism,'coupling_mating_contacts':mating,'mouth_optics_contacts':mouth_contacts,'max_radius_times_curvature':spec['core_max_radius_times_curvature'],'scope':'Actual liner/ribbon self and pair tests, source hardware/shell sampled sweep, nine A and physical-optics poses; only the explicit rear flange plane mate is classified separately. New coupling interfaces have a separate check. No global containment, complete musical/echo presentation, native interaction or art acceptance.'}
(OUT/'core_fit_check.json').write_text(json.dumps(report,indent=2)+'\n');print('C3_CORE_FIT_RESULT',passed,flush=True)
