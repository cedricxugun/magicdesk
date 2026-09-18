"""Read evaluated Blender clamp poses for independent Godot import comparison."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps'
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
convert=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));undo=convert.inverted()
def pose(name):
    o=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());m=convert@o.matrix_world@undo;p,q,s=m.decompose()
    return {'p':list(p),'q':[q.x,q.y,q.z,q.w],'s':list(s)}
samples=[]
for amount in [0.,.25,.5,.75,1.]:
    for row in spec['collar_clamps']:
        o=bpy.data.objects[row['pivot']];o['service_release']=amount;o.update_tag()
    bpy.context.view_layer.update()
    for row in spec['collar_clamps']:
        o=bpy.data.objects[row['pivot']].evaluated_get(bpy.context.evaluated_depsgraph_get())
        assert abs(o.rotation_euler.y-math.radians(65)*amount)<1e-6
        names=[row['pivot'],row['cam'],row['grip'],row['stud'],row['hinge_pin']]
        samples.append({'index':row['index'],'release':amount,'nodes':{name:pose(name) for name in names}})
(OUT/'source_poses.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'samples':samples,'scope':'Actual refreshed source world transforms, including stationary stud/pin and moving cam/grip; converted to glTF axes.'},indent=2)+'\n')
print('I_COLLAR_POSES_RECORDED',len(samples),flush=True)
