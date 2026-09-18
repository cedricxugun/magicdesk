"""Dense reservoir/open-cage route sampling; not a complete device collision certificate."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/service_r7'
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
reservoir=bpy.data.objects['IS4_ReservoirCartridge'];scene.frame_set(1);home=reservoir.matrix_local.copy()
def mesh(objects,relative=None):
    vertices=[];faces=[];owners=[]
    for obj in objects:
        if obj.type not in ['MESH','CURVE']:continue
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh();data.calc_loop_triangles();base=len(vertices);transform=obj.matrix_world if relative is None else relative@obj.matrix_world
        vertices.extend(transform@v.co for v in data.vertices);faces.extend(tuple(base+k for k in tri.vertices) for tri in data.loop_triangles);owners.extend([obj.name]*len(data.loop_triangles));ev.to_mesh_clear()
    return vertices,faces,owners
vertices,faces,names=mesh(reservoir.children_recursive,reservoir.matrix_world.inverted())
scene.frame_set(340);bpy.context.view_layer.update()
targets=[]
for name in ['IS7_CageLeft','IS7_CageRight']:targets.extend(bpy.data.objects[name].children_recursive)
v,f,obstacles=mesh(targets);fixed=BVHTree.FromPolygons(v,f,all_triangles=True)
route=next(g['route'] for g in spec['groups'] if g['name']==reservoir.name);issues=[]
def offset(amount):
    for a,b in zip(route,route[1:]):
        if amount<=b['at']:
            u=max(0.,min(1.,(amount-a['at'])/(b['at']-a['at'])));u=u*u*(3-2*u)
            return Vector(a['offset']).lerp(Vector(b['offset']),u)
    return Vector(route[-1]['offset'])
for step in range(201):
    amount=.86+.14*step/200
    transform=reservoir.parent.matrix_world@home@Matrix.Translation(offset(amount))
    hits=BVHTree.FromPolygons([transform@v for v in vertices],faces,all_triangles=True).overlap(fixed)
    if hits:issues.append({'amount':amount,'pairs':sorted(set((names[a],obstacles[b]) for a,b in hits))})
result={'passed':not issues,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'samples':201,'collisions':issues,'scope':'Reservoir versus fully-open cage halves including their covers/mounts/conductor segments, service amount0.86..1.0 at201 samples. Cage is already stationary throughout this interval. Not other moving cartridges, earlier release, continuous swept volume or missing hinge/connector hardware.'}
(OUT/'reservoir_exit.json').write_text(json.dumps(result,indent=2)+'\n');print('I_RESERVOIR_EXIT',result['passed'],len(issues),flush=True)
