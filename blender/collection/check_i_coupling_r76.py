"""Independent screw/pitch and installed assembly checks for the saved R76."""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76'
s=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mount=bpy.data.objects['IC1_MouthMount'];axis_vector=mount.matrix_world.to_3x3().col[2]
axis=axis_vector.normalized();scale=axis_vector.length

def geometry(o):
    m=o.data;m.calc_loop_triangles()
    return [o.matrix_world@p.co for p in m.vertices],[tuple(t.vertices) for t in m.loop_triangles]

results=[]
for row in s['coupling_threads']['threads']:
    bv,bf=geometry(bpy.data.objects[row['bolt']]);cv,cf=geometry(bpy.data.objects[row['collar']])
    ct=BVHTree.FromPolygons(cv,cf,all_triangles=True)
    center=mount.matrix_world@Vector(row['center_parent']);pitch=row['pitch_parent']
    def contacts(distance,angle):
        q=Quaternion(axis,angle)
        points=[center+q@(p-center)+axis_vector*distance for p in bv]
        return len(BVHTree.FromPolygons(points,bf,all_triangles=True).overlap(ct))
    samples=[]
    for i in range(121):
        distance=row['release_world_distance']/scale*i/120
        angle=math.tau*distance/pitch
        samples.append({'local_distance':distance,'angle':angle,'contacts':contacts(distance,angle)})
    # These deliberately wrong motions must collide: appearance alone is not
    # evidence that the modeled threads actually interlock.
    axial=contacts(pitch/4,0.)
    spin=contacts(0.,math.pi/2)
    results.append({'bolt':row['bolt'],'closed_contacts':contacts(0.,0.),'samples':samples,
                    'axial_only_contacts':axial,'spin_only_contacts':spin,
                    'release_tip_parent':.628+row['release_world_distance']/scale,
                    'female_thread_exit_parent':.6345})
    print('R76_THREAD',row['index'],sum(p['contacts'] for p in samples),axial,spin,flush=True)
passed=all(r['closed_contacts']==0 and all(p['contacts']==0 for p in r['samples'])
           and r['axial_only_contacts']>0 and r['spin_only_contacts']>0
           and r['release_tip_parent']>r['female_thread_exit_parent'] for r in results)
report={'source_sha256':s['source_sha256'],'passed':passed,'installed_axis_scale':scale,'results':results,
        'scope':'Six saved male/female mesh pairs, 121 installed helical positions each; closed clearance, geometric interlock and tip-release witnesses. Not torque/strength or continuous collision certification.'}
(OUT/'thread_interlock.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed
