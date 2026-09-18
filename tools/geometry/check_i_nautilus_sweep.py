"""Sample full source moving-cover assemblies against their real surroundings."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/build.json');OUT=report.parent;spec=json.loads(report.read_text());source=ROOT/spec['source']
assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(181);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def geometry(objects):
    vertices=[];faces=[]
    for o in objects:
        e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(vertices)
        vertices += [e.matrix_world@v.co for v in m.vertices]
        faces += [tuple(offset+i for i in t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    if not vertices:return None
    return (BVHTree.FromPolygons(vertices,faces,all_triangles=True),[min(v[i] for v in vertices) for i in range(3)],[max(v[i] for v in vertices) for i in range(3)],vertices,faces)
def overlap(a,b):
    if a is None or b is None or any(a[2][i]<b[1][i] or b[2][i]<a[1][i] for i in range(3)):return 0
    return len(a[0].overlap(b[0]))
def contact_bounds(a,b):
    points=[]
    for i,j in a[0].overlap(b[0]):
        points.extend(a[3][v] for v in a[4][i]);points.extend(b[3][v] for v in b[4][j])
    return {'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)],'scope':'Bounds of intersecting triangles, not exact penetration/contact points'}
moving={};moving_set=set()
for row in spec['form_panels']:
    node=bpy.data.objects[row['node']];objects=[o for o in node.children_recursive if o.type=='MESH']
    required=bpy.data.objects[row['mesh']]
    assert len(required.data.vertices)>128 and len(required.data.polygons)>64,('Missing cover invalidates sweep',row['mesh'])
    # This is a read-only sampled-pose run: stop source F-curves from restoring
    # their frame-181 quaternion when the dependency graph updates.
    node.animation_data_clear()
    if 'mechanism' in row:
        m=row['mechanism'];carriage=bpy.data.objects[m['carriage']];rotor=bpy.data.objects[m['rotor']]
        carriage.animation_data_clear();rotor.animation_data_clear()
        objects += [o for o in carriage.children_recursive if o.type=='MESH']
    moving[row['node']]=objects;moving_set.update(objects)
static=[o for o in bpy.data.objects['IN1_BodyRoot'].children_recursive if o.type=='MESH' and o not in moving_set]
static_trees={o.name:geometry([o]) for o in static}
mouth=[o for o in bpy.data.objects if o.name.startswith('IAM_') and o.type=='MESH'];mouth_tree=geometry(mouth)
contacts=[];bounds=[]
for step in range(9):
    opening=step/8
    for row in spec['form_panels']:
        fraction=row.get('lift_fraction',0.);clear=min(1.,opening/max(fraction,.000001));turn=max(0.,(opening-fraction)/max(1.-fraction,.000001))
        node=bpy.data.objects[row['node']];node.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle']*turn)
        node.location=Vector(row['pivot_blender'])+Vector(row.get('lift_blender',[0,0,0]))*clear
        if 'mechanism' in row:
            m=row['mechanism'];bpy.data.objects[m['carriage']].location=Vector((0,0,m['stroke']*clear))
            bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle']*turn)
    bpy.context.view_layer.update()
    for row in spec['form_panels']:
        fraction=row.get('lift_fraction',0.);turn=max(0.,(opening-fraction)/max(1.-fraction,.000001));expected=Quaternion(Vector(row['axis_blender']),row['angle']*turn)
        actual=bpy.data.objects[row['node']].evaluated_get(deps).matrix_local.to_quaternion()
        assert actual.rotation_difference(expected).angle<1e-5,(row['node'],opening,tuple(actual),tuple(expected))
    trees={name:geometry(objects) for name,objects in moving.items()}
    for i,(name,tree) in enumerate(trees.items()):
        bounds.append({'cover':name,'opening':opening,'min':tree[1],'max':tree[2]})
        for other,neighbor in static_trees.items():
            count=overlap(tree,neighbor)
            if count:contacts.append({'opening':opening,'cover':name,'other':other,'triangles':count,'contact_bounds_blender':contact_bounds(tree,neighbor)})
        count=overlap(tree,mouth_tree)
        if count:contacts.append({'opening':opening,'cover':name,'other':'A_at_source_frame_181','triangles':count,'contact_bounds_blender':contact_bounds(tree,mouth_tree)})
        for other,neighbor in list(trees.items())[i+1:]:
            count=overlap(tree,neighbor)
            if count:contacts.append({'opening':opening,'cover':name,'other':other,'triangles':count,'contact_bounds_blender':contact_bounds(tree,neighbor)})
    print('NAUTILUS_COVER_SWEEP',opening,len(contacts),flush=True)
summary={}
for row in contacts:
    key=row['cover']+' / '+row['other'];summary.setdefault(key,[]).append(row['opening'])
result={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':not contacts,'contacts':contacts,'pairs':summary,'bounds':bounds,'scope':'Nine manually verified source hinge poses, complete moving porcelain/rim assemblies against each new fixed part, each other and A at source frame 181. No intentional-contact exclusions. Does not cover every A pose, optical mounts, base, all fixed-part pairs, containment, continuous collision or visual acceptance.'}
(OUT/'cover_sweep_check.json').write_text(json.dumps(result,indent=2)+'\n');print('NAUTILUS_COVER_SWEEP_RESULT',json.dumps(summary),flush=True)
