"""Read-only R87 rear hardware inventory and actual fixed-interface contacts."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/back_hardware_r88';OUT.mkdir(exist_ok=True)
spec=json.loads((R/'review/I_refinement/nautilus_reset_r82/oblique_hinge_r87/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT']
def geometry(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();vs=[ev.matrix_world@v.co for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles];ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,ts,all_triangles=True),vs,ts,[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]
new=[o for o in root.children_recursive if o.type=='MESH' and o.name.startswith(('I85_Guide_','I85_Wiper_','I85_SupportA_','I85_SupportB_','I85_FixedShoe_'))]
targets=[o for o in root.children_recursive if o.type in ['MESH','CURVE'] and o.name.startswith(('R82_Fixed_Rear_Keel','R82_Acoustic_Chamber_Liner','I86_ReceiverCasting','R82_R4_','R82_R3_')) and not o.name.startswith(('R82_R3_Slider_','R82_R3_Crosshead','R82_R3_Rotating','R82_R3_Pin_Stop'))]
geos={o.name:geometry(o) for o in new+targets}
contacts=[]
for a in new:
 ga=geos[a.name]
 for b in targets:
  gb=geos[b.name]
  if any(ga[4][k]<gb[3][k] or gb[4][k]<ga[3][k] for k in range(3)):continue
  hits=ga[0].overlap(gb[0])
  if hits:
   pts=[ga[1][i] for pair in hits for i in ga[2][pair[0]]]
   contacts.append({'new':a.name,'existing':b.name,'triangle_pairs':len(hits),'new_triangle_bounds':[[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]})
flanges=[{'name':o.name,'parent':o.parent.name if o.parent else None,'location':list(o.matrix_world.translation),'mesh':o.data.name} for o in root.children_recursive if o.name.startswith('R82_R4_Rear_Guide_Flange_')]
(OUT/'inventory.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'rear_guide_flanges':flanges,'new_fixed_parts':len(new),'legacy_targets':len(targets),'contacts':contacts,'scope':'Read-only closed pose of new fixed supports/shoes/guides vs selected existing rear structure. Contacts include intentional joining; require geometric classification. Not a whole-assembly pass.'},indent=2)+'\n')
print('R88_FIXED_INTERFACES',contacts,flush=True)
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=40;scene.render.resolution_x=1000;scene.render.resolution_y=1100
cam=scene.camera;cam.location=(4,7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
scene.render.filepath=str(OUT/'rear_closed.png');bpy.ops.render.render(write_still=True)
scene.frame_set(205);scene.render.filepath=str(OUT/'rear_open.png');bpy.ops.render.render(write_still=True)
print('R88_INSPECT_DONE',flush=True)
