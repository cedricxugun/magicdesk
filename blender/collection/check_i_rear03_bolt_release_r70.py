"""Independent axial witness for releasing rear inserts before cassette removal."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/rear03_release_r70/partial_bolts_r3';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
row=next(r for r in s['form_panels']if r['mesh']=='IN1_PorcelainPanel_03');normal=Vector(row['mechanism']['rear_shoe']['normal']).normalized()
def extent(name):
 o=bpy.data.objects[name];v=[normal.dot(o.matrix_world@x.co)for x in o.data.vertices];return [min(v),max(v)]
rows=[]
for sign in [-1,1]:
 prefix='IN2_Cassette03BodyBolt'+str(sign);bolt=extent(prefix+'Bolt');insert=extent(prefix+'ThreadedInsert');liner=extent(prefix+'BoreLiner');shift=.010
 row={'bolt':prefix+'Bolt','insert':prefix+'ThreadedInsert','bolt_axis_range':bolt,'insert_axis_range':insert,'liner_axis_range':liner,'normal':list(normal),'withdrawal':shift,'released_bolt_tip_to_insert_gap':bolt[0]+shift-insert[1],'remaining_liner_axial_overlap':max(0.,min(bolt[1]+shift,liner[1])-max(bolt[0]+shift,liner[0]))};rows.append(row)
passed=all(r['released_bolt_tip_to_insert_gap']>.0002 and r['remaining_liner_axial_overlap']>.001 for r in rows)
result={'source_sha256':s['source_sha256'],'passed':passed,'rows':rows,'scope':'Actual mesh axis extrema show the loosened bolt no longer reaches the existing insert and still passes through the liner. Existing threads are simplified; this is not thread-flank simulation, a new captive retainer, torque or gravity proof.'};(OUT/'bolt_disengagement.json').write_text(json.dumps(result,indent=2)+'\n');print('REAR_BOLT_DISENGAGEMENT',json.dumps(result));assert passed
