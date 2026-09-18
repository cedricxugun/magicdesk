"""Read-only evaluated-geometry measurement for any named model contract."""
import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
contract_path=ROOT/(args[0] if args else 'production/I_refinement/conch_r11/shape_contract.json');contract=json.loads(contract_path.read_text());build=json.loads((ROOT/contract['build_report']).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=ROOT/contract['source'];assert sha(source)==build['source_sha256'],'Unrecorded source revision'
base=json.loads((ROOT/contract['base_measurements']).read_text());assert sha(ROOT/base['source'])==base['source_sha256'],'Shared-base measurement stale: remeasure actual source'
D=base['fixed_base_including_controls']['size'][0]
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def points(node):
 for obj in [node]+list(node.children_recursive):
  if obj.type not in ['MESH','CURVE']:continue
  e=obj.evaluated_get(deps);m=e.to_mesh()
  for v in m.vertices:yield obj.matrix_world@v.co
  e.to_mesh_clear()
def box(node):
 lo=[float('inf')]*3;hi=[-float('inf')]*3;count=0
 for p in points(node):
  for i in range(3):lo[i]=min(lo[i],p[i]);hi[i]=max(hi[i],p[i])
  count+=1
 return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)],'size_D':[(hi[i]-lo[i])/D for i in range(3)],'vertices_measured':count}
groups={key:box(bpy.data.objects[name]) for key,name in contract['groups'].items()};anchors={}
for label,name in contract['anchors'].items():
 obj=bpy.data.objects[name];p=obj.matrix_world.translation;anchors[label]={'object':name,'world_z_up':list(p),'world_D':list(p/D)}
mouth=bpy.data.objects[contract['anchors']['mouth_center']];rim=next(o for o in bpy.data.objects if o.name.startswith(contract['mouth_rim_prefix']));local=[mouth.matrix_world.inverted()@p for p in points(rim)]
aperture_axis=-(mouth.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
local_rim_diameter=2*max(math.hypot(p.x,p.y) for p in local)
unit_x=mouth.matrix_world.to_3x3().col[0].normalized();unit_y=mouth.matrix_world.to_3x3().col[1].normalized();origin=mouth.matrix_world.translation
world_radial=[((p-origin).dot(unit_x),(p-origin).dot(unit_y)) for p in points(rim)]
rim_diameter=2*max(math.hypot(x,y) for x,y in world_radial)
basis_scales=[mouth.matrix_world.to_3x3().col[i].length for i in range(3)]
if max(basis_scales)-min(basis_scales)<1e-6:assert abs(rim_diameter-local_rim_diameter*basis_scales[0])<1e-5

report={'source':contract['source'],'source_sha256':sha(source),'component_sha256':sha(ROOT/contract['component']),'contract_sha256':sha(contract_path),'status':contract['status'],'axes':'Blender world: X width, Y depth, Z up','D':D,'base_sha256':base['source_sha256'],'groups':groups,'anchors':anchors,'intrinsic_unscaled_rim_diameter':local_rim_diameter,'mouth_world_basis_scales':basis_scales,'mouth_outer_rim_diameter':rim_diameter,'mouth_outer_rim_diameter_D':rim_diameter/D,'mouth_outward_axis':list(aperture_axis),'closed_total_height_D':groups['assembly']['max'][2]/D,'design_fidelity':'UNPROVEN: no locked silhouette/landmark target; these are measured candidate values, not accepted design dimensions.'}
out=ROOT/contract['build_report'];out=out.parent/'measured_shape.json';out.write_text(json.dumps(report,indent=2)+'\n');print('SHAPE_MEASURED',report['closed_total_height_D'],rim_diameter/D,flush=True)
