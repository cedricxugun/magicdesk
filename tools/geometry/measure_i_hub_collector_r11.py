import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r9/build.json';s=json.loads(p.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
core=bpy.data.objects['IN3_ContinuousThroat'];core.data.calc_loop_triangles();tree=BVHTree.FromPolygons([core.matrix_world@v.co for v in core.data.vertices],[tuple(t.vertices) for t in core.data.loop_triangles],all_triangles=True)
for name in ['IN1_SpiralHubFront','IN1_HubCeramicFront','IN1_HubRingFront','IN1_HubRecessFront','IN1_HubInsetFront']:
    o=bpy.data.objects[name];points=[o.matrix_world@v.co for v in o.data.vertices];rows.append({'name':name,'matrix':[list(r) for r in o.matrix_world],'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}})
hub=rows[0];center=Vector((.12,hub['bounds']['max'][1],1.96));gaps=[]
import math
for radius in [0.,.08,.13,.155,.16]:
    for i in range(24):
        a=i*math.tau/24;start=center+Vector((radius*math.cos(a),.00001,radius*math.sin(a)));hit=tree.ray_cast(start,Vector((0,1,0)),.2)
        if hit[0] is not None:gaps.append({'radius':radius,'angle':a,'hub_point':list(start-Vector((0,.00001,0))),'core_point':list(hit[0]),'gap':hit[0].y-center.y})
OUT=ROOT/'review/I_refinement/nautilus_r1/throat_chambers_r11';OUT.mkdir(parents=True,exist_ok=True);(OUT/'hub_interface_inventory.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'hub_parts':rows,'back_face_core_samples':gaps,'scope':'Actual existing hub and core geometry; no collector built and no support connection accepted.'},indent=2)+'\n');print(json.dumps({'parts':rows,'samples':len(gaps),'gap_min':min(r['gap'] for r in gaps),'gap_max':max(r['gap'] for r in gaps)}),flush=True)
