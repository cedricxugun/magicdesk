"""Saved component: moving rigid groups against each other and all fixed parts."""
import bpy,json,hashlib,sys,collections
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'blender/collection/G_butterfly_r2.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
root=bpy.data.objects['GB2_Butterfly'];scene=bpy.context.scene
dynamic=[o for o in root.children if o.name.startswith(('GB2_Wing','GB2_DriveCrank','GB2_ConnectingRod')) and o.type=='EMPTY']
assert len(dynamic)==12
moving=set(o for node in dynamic for o in node.children_recursive)
groups={node.name:[o for o in node.children_recursive if o.type in ['MESH','CURVE','FONT']] for node in dynamic}
groups['fixed']=[o for o in root.children_recursive if o not in moving and o.type in ['MESH','CURVE','FONT']]
scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get();cache={}
for items in groups.values():
    for obj in items:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        cache[obj.name]=([v.co.copy() for v in mesh.vertices],[tuple(p.vertices) for p in mesh.loop_triangles]);ev.to_mesh_clear()
def tree(items):
    vertices=[];triangles=[];owners=[]
    for obj in items:
        points,faces=cache[obj.name];offset=len(vertices);vertices.extend(obj.matrix_world@v for v in points)
        triangles.extend(tuple(offset+i for i in p) for p in faces);owners.extend([obj.name]*len(faces))
    return BVHTree.FromPolygons(vertices,triangles,all_triangles=True),owners
stride=30 if '--quick' in sys.argv else 10;frames=list(range(1,542,stride));issues={};fixed=tree(groups['fixed']);names=[n for n in groups if n!='fixed']
for frame in frames:
    scene.frame_set(frame);bpy.context.view_layer.update();trees={n:tree(groups[n]) for n in names};trees['fixed']=fixed
    for i,name in enumerate(names):
        for other in ['fixed']+names[i+1:]:
            ta,oa=trees[name];tb,ob=trees[other];hits=ta.overlap(tb)
            if not hits:continue
            pairs=collections.Counter((oa[a],ob[b]) for a,b in hits)
            for pair,count in pairs.items():
                key=' | '.join(pair)
                if key not in issues:issues[key]={'objects':pair,'groups':[name,other],'frames':[],'max_triangle_pairs':0}
                issues[key]['frames'].append(frame);issues[key]['max_triangle_pairs']=max(count,issues[key]['max_triangle_pairs'])
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frames':frames,'moving_groups':len(dynamic),'pairs':list(issues.values()),'passed':not issues,'scope':'All moving mesh/curve surfaces vs other moving groups and fixed component surfaces; same-rigid-group contacts not checked. Surface overlap does not certify solid containment, minimum manufacturing gaps or external player clearance.'}
(ROOT/'review/G_optical_curator/butterfly_r2/hardware_clearance.json').write_text(json.dumps(report,indent=2)+'\n')
print('BUTTERFLY_HARDWARE',json.dumps({'passed':report['passed'],'frames':len(frames),'pair_count':len(issues),'first_pairs':list(issues.values())[:5]}),flush=True)
raise SystemExit(0 if report['passed'] else 2)
