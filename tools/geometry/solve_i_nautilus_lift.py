"""Find a straight lift preserving the cover angle using real surrounding meshes."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1';spec=json.loads((OUT/'build.json').read_text());args=sys.argv[sys.argv.index('--')+1:];number=int(args[0]);row=spec['form_panels'][number-1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(181)
for r in spec['form_panels']:bpy.data.objects[r['node']].animation_data_clear()
def set_pose(r,p,lift=None,angle=None):
    node=bpy.data.objects[r['node']];f=r.get('lift_fraction',0.);c=min(1.,p/max(f,.000001));t=max(0.,(p-f)/max(1.-f,.000001))
    node.location=Vector(r['pivot_blender'])+Vector(lift if lift is not None else r['lift_blender'])*c
    node.rotation_quaternion=Quaternion(Vector(r['axis_blender']), (r['angle'] if angle is None else angle)*t)
for r in spec['form_panels']:set_pose(r,0.)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def raw(objects):
    vv=[];tt=[]
    for o in objects:
        e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(vv);vv += [tuple(e.matrix_world@v.co) for v in m.vertices];tt += [tuple(offset+i for i in t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    return np.asarray(vv),tt
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t,all_triangles=True),v.min(0),v.max(0)
def collides(a,b):return bool(np.all(a[2]>=b[1]) and np.all(b[2]>=a[1]) and a[0].overlap(b[0]))
groups={};all_cover=set()
for r in spec['form_panels']:
    objects=[o for o in bpy.data.objects[r['node']].children_recursive if o.type=='MESH'];groups[r['node']]=objects;all_cover.update(objects)
fixed=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IN1_') and o not in all_cover]
static=[(o.name,tree(*raw([o]))) for o in fixed]
mouth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')];static.append(('A_source_frame_181',tree(*raw(mouth))))
vertices,triangles=raw(groups[row['node']]);pivot=np.asarray(row['pivot_blender']);local=vertices-pivot
poses=[0.,.04,.08,.12,.16,.20,.25,.35,.50,.65,.80,.90,1.]
neighbors={}
for p in poses:
    for r in spec['form_panels']:
        if r['node']!=row['node']:set_pose(r,p)
    bpy.context.view_layer.update()
    neighbors[p]=[(r['node'],tree(*raw(groups[r['node']]))) for r in spec['form_panels'] if r['node']!=row['node']]
radial=Vector(row['lift_blender']);radial.y=0;radial.normalize();angle=abs(math.degrees(row['angle']));sign=1 if row['angle']>0 else -1
trials=[];solutions=[]
for degrees in ([angle] if number==5 else [angle,20.,18.,16.]):
    for radius in [.055,.080,.100,.130]:
        for forward in [.045,.065,.085,.105]:
            lift=radial*radius+Vector((0,-forward,0));fail=None
            for p in poses:
                f=row['lift_fraction'];c=min(1.,p/f);t=max(0.,(p-f)/(1.-f));rotation=np.array(Quaternion(Vector(row['axis_blender']),math.radians(degrees)*sign*t).to_matrix())
                points=np.einsum('ij,nj->ni',rotation,local)+pivot+np.asarray(lift)*c;candidate=tree(points,triangles)
                for name,other in static+neighbors[p]:
                    if collides(candidate,other):fail={'opening':p,'other':name};break
                if fail:break
            record={'radius':radius,'forward':forward,'angle_degrees':degrees,'lift':list(lift),'failure':fail};trials.append(record)
            if not fail:solutions.append(record)
    if solutions:break
solutions.sort(key=lambda x:(abs(x['radius']-Vector(row['lift_blender']).length)+abs(x['forward']-.085)))
result={'source_sha256':spec['source_sha256'],'panel':number,'solutions':solutions,'trials':trials,'scope':'Straight-lift parameter candidates across 13 body poses against actual fixed body, all other covers and A frame181. Existing other-cover paths held fixed. No all-A/optics/containment/continuous or art acceptance.'};(OUT/f'lift_solutions_{number}.json').write_text(json.dumps(result,indent=2)+'\n');print('NAUTILUS_LIFT_SOLUTIONS',number,json.dumps(solutions),flush=True)
