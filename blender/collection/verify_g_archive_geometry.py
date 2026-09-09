"""Sample the real folio/hardware meshes against one another and the active
specimen. Deliberate contact inside each assembled group is excluded."""
import bpy,json,pathlib,itertools
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive_detail.blend'))
scene=bpy.context.scene
data=json.loads((ROOT/'app/assets/collection/models/G_archive_detail.json').read_text(encoding='utf-8'))
take=json.loads((ROOT/'review/G_archive/archive_take.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
for obj in bpy.data.collections['MODULE_G3'].all_objects:obj.animation_data_clear()
groups={}
for leaf in data['g_mechanism']['leaves']:
    root=bpy.data.objects[leaf['face']];groups['page_'+str(leaf['index'])]=[o for o in root.children_recursive if o.type in ['MESH','CURVE']]
for side in [-1,1]:
    root=bpy.data.objects['G3_CoverFace'+str(side)];groups['cover_'+str(side)]=[o for o in root.children_recursive if o.type in ['MESH','CURVE']]
specimens={i:[o for o in bpy.data.objects[item['root']].children_recursive if o.type in ['MESH','CURVE']] for i,item in enumerate(data['g_archive']['contents'])}
def tree(objects,deps):
    verts=[];faces=[]
    for o in objects:
        ev=o.evaluated_get(deps);mesh=ev.to_mesh();offset=len(verts);verts.extend(ev.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(offset+j for j in p.vertices) for p in mesh.polygons);ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts,faces,epsilon=.000015)
failures=[];frames=0
for sample in take['samples'][::10]:
    frames+=1
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if obj:obj.matrix_basis=CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();trees={name:tree(objects,deps) for name,objects in groups.items()}
    for a,c in itertools.combinations(trees,2):
        hits=trees[a].overlap(trees[c])
        if hits:failures.append({'frame':sample['frame'],'a':a,'b':c,'triangles':len(hits)})
    state=sample['state']
    if state['display_amount']>.01 and state['loaded_index']>=0:
        actor=tree(specimens[state['loaded_index']],deps)
        for name,t in trees.items():
            hits=t.overlap(actor)
            if hits:failures.append({'frame':sample['frame'],'a':name,'b':'specimen_'+str(state['loaded_index']),'triangles':len(hits)})
report={'all_passed':not failures,'frames':frames,'scope':'actual folio/cover mesh groups including hardware, plus currently displayed specimen; internal contact within each group excluded','failures':failures}
(ROOT/'review/G_archive/clearance.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('ARCHIVE_MESH_CLEARANCE',frames,len(failures),flush=True)
