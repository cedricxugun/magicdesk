"""Read evaluated Blender guide/shaft poses as an independent runtime reference."""
import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import pose
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/front_guides')
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source']
assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;rows=[]
for frame in [25,49,61,85,103,133,157,169,181]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for group in spec['tongues']:
        guide=bpy.data.objects[group['guide_roll']['rotor']]
        row=next(r for r in spec['guide_interfaces'] if r['index']==group['tongue_index'])
        shaft=bpy.data.objects[row['shaft']]
        rows.append({'frame':frame,'opening':(frame-25)/156,'index':group['tongue_index'],'guide':guide.name,'guide_pose':pose(guide.matrix_world),'shaft':shaft.name,'shaft_pose':pose(shaft.matrix_world),'feed':float(bpy.data.objects[group['drive']]['feed'])})
(OUT/'source_poses.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'poses':rows,'scope':'Actual evaluated source transforms at integer authored frames, in glTF coordinates. For independent runtime hierarchy/drive comparison.'},indent=2)+'\n')
print('I_FRONT_GUIDE_POSES_RECORDED',len(rows))
