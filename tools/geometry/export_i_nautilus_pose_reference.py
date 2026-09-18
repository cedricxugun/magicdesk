"""Export evaluated Blender node landmarks for independent imported-pose checks."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/hinge_r1/build.json');OUT=report.parent;spec=json.loads(report.read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(181)
names=[]
for row in spec['form_panels']:
    bpy.data.objects[row['node']].animation_data_clear();names.append(row['node'])
    if 'mechanism' in row:
        m=row['mechanism'];bpy.data.objects[m['carriage']].animation_data_clear();bpy.data.objects[m['rotor']].animation_data_clear()
names += [o.name for o in bpy.data.objects if o.name.startswith('IN2_')]
names += spec.get('runtime_pose_witnesses',[])
local=[Vector((0,0,0)),Vector((.01,0,0)),Vector((0,.01,0)),Vector((0,0,.01))]
def godot(v):return [v.x,v.z,-v.y]
samples=[];engagement=[]
for value in [0.,.10,.20,.35,.65,1.,.55,.12,0.]:
    for row in spec['form_panels']:
        f=row['lift_fraction'];clear=min(1.,value/max(f,.000001));turn=max(0.,(value-f)/max(1-f,.000001));node=bpy.data.objects[row['node']]
        node.location=Vector(row['pivot_blender'])+Vector(row['lift_blender'])*clear;node.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle']*turn)
        if 'mechanism' in row:
            m=row['mechanism'];bpy.data.objects[m['carriage']].location=(0,0,m['stroke']*clear);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle']*turn)
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    points={name:[godot(bpy.data.objects[name].evaluated_get(deps).matrix_world@v) for v in local] for name in names}
    samples.append({'opening':value,'points':points})
    for mechanism in spec.get('real_cassettes',[]):
        inverse=bpy.data.objects[mechanism['frame']].matrix_world.inverted()
        for guide in mechanism['guide_records']:
            rod=bpy.data.objects[guide['rod']];sleeve=bpy.data.objects[guide['sleeve']];a=[(inverse@rod.matrix_world@v.co).z for v in rod.data.vertices];b=[(inverse@sleeve.matrix_world@v.co).z for v in sleeve.data.vertices];overlap=min(max(a),max(b))-max(min(a),min(b));assert overlap>.060
            engagement.append({'opening':value,'rod':rod.name,'sleeve':sleeve.name,'overlap':overlap,'rod_bounds':[min(a),max(a)],'sleeve_bounds':[min(b),max(b)]})
result={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'local_points':[godot(v) for v in local],'samples':samples,'scope':'Evaluated source transform landmarks, with source animation temporarily cleared in memory; not vertex/topology/material equivalence.'}
(OUT/'pose_reference.json').write_text(json.dumps(result,indent=2)+'\n');print('NAUTILUS_POSE_REFERENCE',len(names),len(samples),flush=True)
(OUT/'guide_engagement.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'samples':engagement,'scope':'Actual source rod and sleeve axial overlap at closed/lifted/open/reversed input samples. Not full collision, materials or art acceptance.'},indent=2)+'\n')
