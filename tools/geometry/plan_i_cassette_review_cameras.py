"""Choose fixed inspection cameras that see the installed mechanism across its poses."""
import bpy,json,hashlib,itertools,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/upper_cassettes_r19/build.json');OUT=report.parent;s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
for row in s['form_panels']:
    bpy.data.objects[row['node']].animation_data_clear()
    if 'mechanism' in row:
        for key in ['carriage','rotor']:bpy.data.objects[row['mechanism'][key]].animation_data_clear()
skins=[o for o in bpy.data.objects['IN1_BodyRoot'].children_recursive if o.type=='MESH' and not o.name.startswith('IN2_')]
base=bpy.data.objects['BASE_FIXED'];skins += [o for o in [base,*base.children_recursive] if o.type=='MESH'];skins += [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')];skins=list(dict.fromkeys(skins))
def pose(value):
    for row in s['form_panels']:
        clear=min(1.,value/max(row['lift_fraction'],1e-6));turn=max(0.,(value-row['lift_fraction'])/max(1-row['lift_fraction'],1e-6));node=bpy.data.objects[row['node']];node.location=Vector(row['pivot_blender'])+Vector(row['lift_blender'])*clear;node.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle']*turn)
        if 'mechanism' in row:
            m=row['mechanism'];bpy.data.objects[m['carriage']].location=(0,0,m['stroke']*clear);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle']*turn)
    bpy.context.view_layer.update()
def shell_tree():
    v=[];f=[]
    for o in skins:
        o.data.calc_loop_triangles();offset=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices);f.extend(tuple(offset+i for i in t.vertices) for t in o.data.loop_triangles)
    return BVHTree.FromPolygons(v,f,all_triangles=True)
def center(name):
    o=bpy.data.objects[name];return sum((o.matrix_world@Vector(p) for p in o.bound_box),Vector())/8
def godot(p):return [p.x,p.z,-p.y]
rows=[]
for m in s['real_cassettes']:
    panel=m['panel_number'];frame=bpy.data.objects[m['frame']];matrix=frame.matrix_world.copy();target=matrix@Vector((0,.025,-.035));up=-(matrix.to_3x3()@Vector((0,1,0))).normalized();prefix='IN2_Cassette%02d'%panel;names=[prefix+'BackBlock',prefix+'Crosshead',prefix+'RotatingTongue','IN2_Guide%02dJacket-1'%panel,'IN2_Guide%02dJacket1'%panel]
    candidates=[]
    if 'power' in m and 'linear' in m['power']:names.append(m['power']['linear']['housing'])
    for x,y,z in itertools.product([-.90,.90],[.18,.40,.65],[.25,.50]):
        eye=target+matrix.to_3x3()@Vector((x,-z,y))
        if eye.z>.78:candidates.append({'eye':eye,'visible':0,'by_pose':[]})
    radial=(target-Vector((.12,.16,1.96))).normalized();hinge=matrix.to_3x3().col[0].normalized()
    for sign,distance in itertools.product([-1,1],[.55,.85]):
        eye=target+radial*distance+hinge*(sign*.65)+Vector((0,-.20,.25))
        if eye.z>.78:candidates.append({'eye':eye,'visible':0,'by_pose':[]})
    for value in [0.,.2,1.]:
        pose(value);tree=shell_tree();points=[center(n) for n in names]
        for candidate in candidates:
            count=0
            for p in points:
                ray=p-candidate['eye'];hit=tree.ray_cast(candidate['eye'],ray.normalized(),ray.length)
                if hit[0] is None:count+=1
            candidate['visible']+=count;candidate['by_pose'].append(count)
    best=max(candidates,key=lambda r:r['visible']*100-(r['eye']-target).length)
    rows.append({'panel_number':panel,'eye':godot(best['eye']),'target':godot(target),'up':godot(up),'fov':34.,'visible_landmarks':best['visible'],'landmarks_per_pose':best['by_pose'],'scope':'Fixed camera above the base and ranked against actual body/base/A occlusion across closed/lifted/open poses, not art or mechanism acceptance.'})
(OUT/'cassette_review_cameras.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'cameras':rows},indent=2)+'\n');print(json.dumps(rows),flush=True)
