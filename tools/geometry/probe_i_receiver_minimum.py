import bpy,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'review/I_refinement/nautilus_r1/core_bridge_r4';spec=json.loads((folder/'build.json').read_text());check=json.loads((folder/'receiver_wall_check.json').read_text());assert spec['source_sha256']==check['source_sha256']==hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['IN1_PorcelainPanel_02'];o.data.calc_loop_triangles();m=o.data
attrs={name:[p.value for p in m.attributes[name].data] for name in ['formed_wall_fraction','IN3_receiver_region','IN3_receiver_floor_region']};vs=[o.matrix_world@v.co for v in m.vertices];outer=[tuple(t.vertices) for t in m.loop_triangles if max(attrs['formed_wall_fraction'][i] for i in t.vertices)<.001];tree=BVHTree.FromPolygons(vs,outer,all_triangles=True);inv=bpy.data.objects['IAM_MODULE'].matrix_world.inverted()
rows=[]
for item in check['worst'][:5]:
    tri=m.loop_triangles[item['triangle']];row={'triangle':item['triangle'],'polygon':tri.polygon_index,'polygon_vertices':len(m.polygons[tri.polygon_index].vertices),'sample_distance':item['distance'],'vertices':[]}
    for i in tri.vertices:
        p=vs[i];q,n,face,d=tree.find_nearest(p);row['vertices'].append({'id':i,'world':list(p),'mouth_local':list(inv@p),'attributes':{name:a[i] for name,a in attrs.items()},'distance':d,'signed':-(p-q).dot(n)})
    rows.append(row)
(folder/'wall_minimum_probe.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
