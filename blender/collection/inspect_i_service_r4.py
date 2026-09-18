"""Read-only source poses and detached service-assembly surface intersections."""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/service_r4'
for arg in sys.argv:
    if arg.startswith('--review-dir='):OUT=ROOT/arg.split('=',1)[1]
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene;root=bpy.data.objects['IH1_MODULE'];take=json.loads((OUT/'take.json').read_text())
groups={r['name']:bpy.data.objects[r['name']] for r in spec['groups']}
members={name:[] for name in groups};members['fixed']=[]
for obj in root.children_recursive:
    if obj.type not in ['MESH','CURVE']:continue
    parent=obj.parent
    while parent and parent.name not in groups:parent=parent.parent
    members[parent.name if parent else 'fixed'].append(obj)
cache={}
for objects in members.values():
    for o in objects:
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
        cache[o.name]=([v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles]);ev.to_mesh_clear()
def tree(objects):
    points=[];faces=[];names=[]
    for o in objects:
        vs,fs=cache[o.name];offset=len(points);points.extend(o.matrix_world@v for v in vs);faces.extend(tuple(offset+k for k in face) for face in fs);names.extend([o.name]*len(fs))
    return BVHTree.FromPolygons(points,faces,all_triangles=True),names
issues=[];initial_contacts=[];checks=0
split_topology=[]
for objects in members.values():
    for obj in objects:
        is_cover=('RearPorcelain' in obj.name and obj.name.endswith(('_A','_B'))) or ('FrontPorcelain' in obj.name and obj.name.endswith(('_L','_R')))
        is_rib='AcousticChamberRib' in obj.name and obj.name.endswith(('_L','_R'))
        if not (is_cover or is_rib):continue
        bm=bmesh.new();bm.from_mesh(obj.data);split_topology.append({'name':obj.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)});bm.free()
# This first inspection samples the initial full extraction; report contact pairs for review.
for frame in [1]+list(range(151,342,19)):
    scene.frame_set(frame);bpy.context.view_layer.update();trees={k:tree(v) for k,v in members.items()}
    for i,a in enumerate(members):
        for b in list(members)[i+1:]:
            hits=trees[a][0].overlap(trees[b][0]);checks+=1
            if hits:
                pairs=sorted(set((trees[a][1][x],trees[b][1][y]) for x,y in hits))
                (initial_contacts if frame==1 else issues).append({'frame':frame,'amount':take['samples'][frame-1]['service']['amount'],'a':a,'b':b,'pairs':pairs})
snapshots=[]
pose_nodes=dict(groups)
pose_nodes.update({o.name:o for o in root.children_recursive if o.name.startswith('IH7_FrontPanel')})
for key in ['piston_stem','hub']:
    if spec.get(key):pose_nodes[spec[key]]=bpy.data.objects[spec[key]]
# Source world matrices converted explicitly to the asset-root Godot coordinates.
C=__import__('mathutils').Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for frame in sorted(set([1,82,151,241,340,400,490,590,625,780,840,970]+([96,99,109] if spec.get('piston_stem') else []))):
    scene.frame_set(frame);bpy.context.view_layer.update()
    snapshots.append({'frame':frame,'poses':{name:[list(row) for row in C@root.matrix_world.inverted()@node.matrix_world@C.inverted()] for name,node in pose_nodes.items()}})
(OUT/'source_poses.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'snapshots':snapshots},indent=2)+'\n')
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'passed':not issues,'pair_checks':checks,'surface_intersections':issues,'scope':'First extraction group/fixed surface inspection, 11 sampled poses. All reported contacts require classification or repair; no automatic baseline exclusions. Cached rest mesh used after pneumatic recovery; not all reverse/continuous-volume/visual checks.'}
result['split_topology']=split_topology;result['passed']=result['passed'] and all(r['nonmanifold_edges']==0 and r['signed_volume']>0 for r in split_topology)
result['initial_surface_intersections']=initial_contacts;result['passed']=result['passed'] and not initial_contacts
(OUT/'clearance.json').write_text(json.dumps(result,indent=2)+'\n');print('I_SERVICE_INSPECTION',len(issues),'contact groups',flush=True)
