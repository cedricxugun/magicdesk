"""Read evaluated source suspension points for an independent exported GLB audit."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];OUT=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/diaphragm');spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);moving=bpy.data.objects[spec['diaphragm']['moving']]
if moving.animation_data:moving.animation_data.action=None
names=spec['diaphragm']['morphs']+['IAM_CentralResonatorCap_Axial'];deps=bpy.context.evaluated_depsgraph_get();arrays={};samples=[]
for index,stroke in enumerate([0.,-.006,-.0045,-.003,.0015,.003,.0045,.006]):
 moving['stroke']=float(stroke);moving.update_tag();bpy.context.view_layer.update();assert abs(moving.location.z-stroke)<1e-6,('Stale suspension evaluation',stroke,moving.location.z)
 for name in names:
  o=bpy.data.objects[name];e=o.evaluated_get(deps);m=e.to_mesh();p=np.array([tuple(e.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear();arrays['pose%d__%s'%(index,name)]=p[:,[0,2,1]]*np.array([1,1,-1])
 samples.append(stroke)
np.savez_compressed(OUT/'source_suspension_points.npz',**arrays)
(OUT/'source_suspension_points.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'objects':names,'strokes':samples,'scope':'Evaluated Blender world vertices, converted to glTF axes; actual morph/parent drivers, not a rest-to-endpoint formula.'},indent=2)+'\n');print('I_SUSPENSION_POINTS_RECORDED',flush=True)
