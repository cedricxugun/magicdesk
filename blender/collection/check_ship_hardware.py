"""Saved component: moving rigid groups against each other and all fixed parts."""
import bpy,json,hashlib,sys,collections
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'blender/collection/G_ship_r2.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
root=bpy.data.objects['GS2_Ship'];scene=bpy.context.scene
entry=json.loads((ROOT/'app/assets/collection/components/G_ship_r2.json').read_text())['rig']
names=[entry['pitch'],entry['roll']]+entry['sails']+entry['waves']+entry['cams']
dynamic=[bpy.data.objects[n] for n in names]
groups={n:[] for n in names};groups['fixed']=[]
for obj in root.children_recursive:
    if obj.type not in ['MESH','CURVE','FONT']:continue
    ancestor=obj.parent
    while ancestor and ancestor.name not in names:ancestor=ancestor.parent
    groups[ancestor.name if ancestor else 'fixed'].append(obj)
scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get();cache={}
for items in groups.values():
    for obj in items:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        cache[obj.name]=([v.co.copy() for v in mesh.vertices],[tuple(p.vertices) for p in mesh.loop_triangles]);ev.to_mesh_clear()
def tree(items):
    vertices=[];triangles=[];owners=[]
    for obj in items:
        points,faces=cache[obj.name]
        if 'WorkingSheet' in obj.name:
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
            points=[v.co.copy() for v in me.vertices];faces=[tuple(p.vertices) for p in me.loop_triangles];ev.to_mesh_clear()
        offset=len(vertices);vertices.extend(obj.matrix_world@v for v in points)
        triangles.extend(tuple(offset+i for i in p) for p in faces);owners.extend([obj.name]*len(faces))
    return BVHTree.FromPolygons(vertices,triangles,all_triangles=True),owners
stride=60 if '--quick' in sys.argv else 10;frames=list(range(1,452,stride));issues={};fixed=tree(groups['fixed']);names=[n for n in groups if n!='fixed']
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
(ROOT/'review/G_optical_curator/ship_r2/hardware_clearance.json').write_text(json.dumps(report,indent=2)+'\n')
print('SHIP_HARDWARE',json.dumps({'passed':report['passed'],'frames':len(frames),'pair_count':len(issues),'first_pairs':list(issues.values())[:5]}),flush=True)
raise SystemExit(0 if report['passed'] else 2)
