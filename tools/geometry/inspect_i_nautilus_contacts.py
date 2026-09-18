"""Resolve sampled assembly contacts to actual meshes and spatial regions."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1';spec=json.loads((OUT/'build.json').read_text());receipt=json.loads((OUT/'cover_sweep_check.json').read_text());assert receipt['source_sha256']==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(181)
for row in spec['form_panels']:bpy.data.objects[row['node']].animation_data_clear()
deps=bpy.context.evaluated_depsgraph_get()
def geom(o):
    e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@p.co for p in m.vertices];t=[tuple(p.vertices) for p in m.loop_triangles];e.to_mesh_clear()
    return BVHTree.FromPolygons(v,t,all_triangles=True),v,t
def members(name):
    o=bpy.data.objects[name]
    return [o] if o.type=='MESH' else [p for p in o.children_recursive if p.type=='MESH']
rows=[]
for pair,poses in receipt['pairs'].items():
    left,right=pair.split(' / ')
    for value in sorted(set([poses[0],poses[-1]])):
        for r in spec['form_panels']:
            t=r.get('lift_fraction',0.);node=bpy.data.objects[r['node']]
            node.location=Vector(r['pivot_blender'])+Vector(r.get('lift_blender',[0,0,0]))*min(1.,value/max(t,.000001))
            node.rotation_quaternion=Quaternion(Vector(r['axis_blender']),r['angle']*max(0.,(value-t)/max(1.-t,.000001)))
        bpy.context.view_layer.update()
        aa=[(o.name,*geom(o)) for o in members(left)];bb=[(o.name,*geom(o)) for o in members(right)]
        for an,at,av,af in aa:
            for bn,bt,bv,bf in bb:
                hits=at.overlap(bt)
                if not hits:continue
                points=[av[i] for a,b in hits for i in af[a]]+[bv[i] for a,b in hits for i in bf[b]]
                rows.append({'opening':value,'left':an,'right':bn,'triangle_pairs':len(hits),'contact_triangle_bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}})
(OUT/'contact_parts.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'rows':rows,'scope':'Contacting triangle bounds, not measured penetration depth; representative first/last poses from known pair report.'},indent=2)+'\n');print(json.dumps(rows),flush=True)
