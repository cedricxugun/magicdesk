"""Measure complete local fixed-skin crossings around each proposed leg passage."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'review/I_refinement/nautilus_r1/trunnion_support_r18/route_r2';plan=json.loads((out/'route_plan.json').read_text());s=json.loads((ROOT/'review/I_refinement/nautilus_r1/chamber04_r15/build.json').read_text());assert plan['complete_route_candidate'] and plan['source_sha256']==s['source_sha256']==hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
for row in plan['selected']:
    top=Vector(row['top']);direction=(Vector(row['foot'])-top).normalized();u=Vector(row['pin_axis']);v=direction.cross(u).normalized();names=[r['mesh'] for r in row['required_fixed_shell_ports']];vertices=[];faces=[];owners=[]
    for name in names:
        o=bpy.data.objects[name];o.data.calc_loop_triangles();offset=len(vertices);vertices.extend(o.matrix_world@p.co for p in o.data.vertices);faces.extend(tuple(offset+i for i in t.vertices) for t in o.data.loop_triangles);owners.extend(name for t in o.data.loop_triangles)
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True);samples=[]
    for radius in [0.,.031,.036,.043]:
        for k in range(64 if radius else 1):
            angle=k*math.tau/64;origin=top+(u*math.cos(angle)+v*math.sin(angle))*radius;start=origin-direction*.10;hits=[]
            for _ in range(16):
                hit=tree.ray_cast(start,direction,row['length']+.20)
                if hit[0] is None:break
                depth=(hit[0]-origin).dot(direction)
                if depth>row['length']+.05:break
                hits.append({'depth':depth,'normal_dot':hit[1].dot(direction),'mesh':owners[hit[2]]});start=hit[0]+direction*.00001
            samples.append({'radius':radius,'angle':angle,'hits':hits})
    depths=[h['depth'] for r in samples for h in r['hits']];matrix=Matrix((u,v,direction)).transposed().to_4x4();matrix.translation=top
    rows.append({'anchor':row['anchor'],'source_skins':names,'matrix_blender':[list(r) for r in matrix],'samples':samples,'minimum_axial_depth':min(depths),'maximum_axial_depth':max(depths),'missing_rays':sum(not r['hits'] for r in samples),'odd_crossing_rays':sum(len(r['hits'])%2 for r in samples)})
(out/'port_sections.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'rows':rows,'scope':'Actual fixed-skin ray intersections for proposed port footprints; no skin cut, liner or support hardware built.'},indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['anchor','source_skins','minimum_axial_depth','maximum_axial_depth','missing_rays','odd_crossing_rays']} for r in rows]),flush=True)
