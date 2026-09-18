"""Sample actual evaluated shell surfaces against stationary core and neighboring shells."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/restore_r9';scene=bpy.context.scene
scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
fixed=bpy.data.objects['IH1_FixedChamber'];upper=bpy.data.objects['IH1_UPPER']
def snapshot(objects,parent):
    vv=[];ff=[];owners=[];inverse=parent.matrix_world.inverted()
    for o in objects:
        if o.type not in ['MESH','CURVE']:continue
        evaluated=o.evaluated_get(deps);m=evaluated.to_mesh();m.calc_loop_triangles();offset=len(vv);mat=inverse@o.matrix_world
        vv.extend(mat@v.co for v in m.vertices)
        ff.extend(tuple(offset+i for i in t.vertices) for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));evaluated.to_mesh_clear()
    return vv,ff,owners
def tree(s,transform):return BVHTree.FromPolygons([transform@p for p in s[0]],s[1],all_triangles=True,epsilon=0.)
# Fixed acoustic surface only; hardware contacts and lower base are explicitly outside this check.
core_objects=[o for o in upper.children_recursive if any(k in o.name for k in ['ContinuousAcousticSkin','AcousticChamberRib','CoreRolledSeam'])]
core=snapshot(core_objects,upper);ct=tree(core,upper.matrix_world)
rows=[]
for i in range(6):
    group=bpy.data.objects['IR9_Shell'+str(i)]
    objs=[o for o in group.children_recursive if any(k in o.name for k in ['Porcelain','PanelLip'])]
    rows.append((group,snapshot(objs,group)))
contacts=[]
for frame in range(1,302,6):
    scene.frame_set(frame);bpy.context.view_layer.update();trees=[tree(s,g.matrix_world) for g,s in rows]
    for i,(g,s) in enumerate(rows):
        hits=trees[i].overlap(ct)
        pairs=sorted(set((s[2][a],core[2][b]) for a,b in hits))
        if pairs:contacts.append({'frame':frame,'shell':i,'against':'core','pairs':pairs})
        for j in range(i+1,6):
            hits=trees[i].overlap(trees[j]);pairs=sorted(set((s[2][a],rows[j][1][2][b]) for a,b in hits))
            if pairs:contacts.append({'frame':frame,'shell':i,'against':j,'pairs':pairs})
result={'passed':not contacts,'samples':51,'contacts':contacts,'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scope':'Sampled porcelain/rolled lips vs fixed acoustic skin/ribs and other porcelain/lips, forward and reverse. Excludes linkage/fastener/spine/base intersections and contained volumes; not continuous or full assembly acceptance.'}
(OUT/'shell_clearance.json').write_text(json.dumps(result,indent=2)+'\n');print('I_R9_SHELL_CLEARANCE',len(contacts),flush=True)
