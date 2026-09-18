"""Independently locate each through-bolt ring on actual connected frame/film pieces."""
import bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/front_sockets_r12/build.json');OUT=report.parent;s=json.loads(report.read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
parent=json.loads((ROOT/s.get('socket_parent_topology','review/I_refinement/nautilus_r1/throat_chambers_r11/topology_check.json')).read_text());assert parent['source_sha256']==s['parent_source_sha256'];expected={r['name']:len(r['components']) for r in parent['rows']}
for cleanup in s.get('construction_cleanup',[]):
    assert cleanup['removed_components']==1 and cleanup['removed_vertex_count']<=16 and abs(cleanup['volume'])<1e-9 and cleanup['diagonal']<.005
    assert max(abs(v-.34/.7) for v in cleanup['mouth_axial_range'])<.001
    expected[cleanup['mesh']]-=cleanup['removed_components']
names=sorted({seat[key] for seat in s['front_sockets']['seats'] for key in ['source_frame','source_film']})
for name in names:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.verts.index_update();remaining=set(bm.verts);labels={};component=0
    while remaining:
        stack=[remaining.pop()]
        while stack:
            v=stack.pop();labels[v.index]=component
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in remaining:remaining.remove(other);stack.append(other)
        component+=1
    bm.free();o.data.calc_loop_triangles();faces=[tuple(t.vertices) for t in o.data.loop_triangles]
    bvh=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],faces,all_triangles=True);sites=[]
    for seat in s['front_sockets']['seats']:
        if name not in [seat['source_frame'],seat['source_film']]:continue
        matrix=Matrix(seat['matrix_blender']);direction=-(matrix.to_3x3()@Vector((0,0,1))).normalized()
        for bolt in seat['bolts']:
            indices=[];points=[]
            for i in range(8):
                a=i*math.tau/8;x,y=bolt['xy'];start=matrix@Vector((x+.0032*math.cos(a),y+.0032*math.sin(a),bolt['frame_seat_z']+.020));hit=bvh.ray_cast(start,direction,.3)
                if hit[0] is None:indices.append(None)
                else:indices.append(labels[faces[hit[2]][0]]);points.append(list(hit[0]))
            sites.append({'bolt':bolt['mesh'],'seat':seat['frame'],'component':indices[0] if len(set(indices))==1 else None,'all_eight_ring_samples_on_one_component':len(set(indices))==1 and indices[0] is not None,'sample_points':points})
    coverage={str(i):sorted(set(r['seat'] for r in sites if r['component']==i)) for i in range(component)}
    rows.append({'mesh':name,'components':component,'parent_components':expected[name],'sites':sites,'component_seats':coverage,'passed':component==expected[name] and all(r['all_eight_ring_samples_on_one_component'] for r in sites) and all(len(v)>=2 for v in coverage.values())})
result={'source_sha256':s['source_sha256'],'passed':all(r['passed'] for r in rows),'rows':rows,'scope':'Actual supported frame and membrane pieces retain their preexisting component counts from the parent topology report. All bore-edge rings must register on one real component; each piece requires at least two distinct clamp seats. Does not merge pieces, prove loads, continuous border capture or whole model/native acceptance.'}
(OUT/'component_support.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'rows':[{k:r[k] for k in ['mesh','components','component_seats','passed']} for r in rows]}),flush=True)
