"""Measure actual first-liner skirt edges and normal wall rays before rounding."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/port_edge_r68';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_envelope_r67/smooth_r3/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
o=bpy.data.objects['IS18_Leg01_PortLiner'];frame=bpy.data.objects['IS18_Leg01_PortFrame'];F=frame.matrix_world;inv=F.inverted();m=o.data;m.calc_loop_triangles();v=[o.matrix_world@p.co for p in m.vertices];t=[tuple(f.vertices)for f in m.loop_triangles];tree=BVHTree.FromPolygons(v,t,all_triangles=True)
measure=[]
for i in range(192):
 top=inv@v[11*192+i];bottom=inv@v[12*192+i];neighbor=inv@v[11*192+(i+1)%192]
 measure.append({'angle':i,'axial_edge_height':top.z-bottom.z,'top_edge_length':(top-neighbor).length,'top':list(top),'bottom':list(bottom)})
wall=[]
for k,f in enumerate(t):
 if not all(5*192<=i<12*192 for i in f):continue
 a,b,c=[v[i]for i in f];center=(a+b+c)/3;normal=(b-a).cross(c-a).normalized();hit=tree.ray_cast(center-normal*1e-6,-normal,.1)
 if hit[0]is not None:wall.append({'face':k,'distance':hit[3]+1e-6,'other_face':hit[2]})
r={'source_sha256':s['source_sha256'],'edge_samples':measure,'minimum_edge_axial_height':min(x['axial_edge_height']for x in measure),'minimum_edge_length':min(x['top_edge_length']for x in measure),'normal_wall_rays':len(wall),'minimum_normal_ray_thickness':min(x['distance']for x in wall),'thinnest_rays':sorted(wall,key=lambda x:x['distance'])[:20],'scope':'Source edge lengths/heights and inward face-centroid normal rays; not a full minimum-thickness proof.'}
(OUT/'edge_measurements.json').write_text(json.dumps(r,indent=2)+'\n');print('PORT_EDGE_MEASURE',json.dumps({k:value for k,value in r.items()if k not in ['edge_samples','thinnest_rays']}))
