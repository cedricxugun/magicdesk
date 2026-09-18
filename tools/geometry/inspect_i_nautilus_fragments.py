import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'review/I_refinement/nautilus_r1';spec=json.loads((folder/'build.json').read_text());check=json.loads((folder/'topology_check.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);rows=[]
for row in check['failures']:
    o=bpy.data.objects[row['name']];bm=bmesh.new();bm.from_mesh(o.data);unseen=set(bm.verts);components=[]
    while unseen:
        queue=[unseen.pop()];vertices=[]
        while queue:
            v=queue.pop();vertices.append(v)
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in unseen:unseen.remove(other);queue.append(other)
        coords=[o.matrix_world@v.co for v in vertices]
        components.append({'count':len(coords),'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]})
    tiny=[{'area':f.calc_area(),'edge_min':min(e.calc_length() for e in f.edges),'edge_max':max(e.calc_length() for e in f.edges)} for f in bm.faces if f.calc_area()<1e-12]
    rows.append({'name':o.name,'components':sorted(components,key=lambda c:-c['count']),'tiny':tiny});bm.free()
(folder/'fragments.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
