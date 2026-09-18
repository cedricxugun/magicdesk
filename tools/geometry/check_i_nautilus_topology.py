"""Read the actual independent source. No scene mutation or art acceptance."""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/build.json');folder=report.parent;spec=json.loads(report.read_text());source=ROOT/spec['source']
assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);rows=[]
body_root=bpy.data.objects['IN1_BodyRoot']
for o in body_root.children_recursive:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();unseen=set(bm.verts);sizes=[]
    while unseen:
        queue=[unseen.pop()];size=0
        while queue:
            v=queue.pop();size+=1
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in unseen:unseen.remove(other);queue.append(other)
        sizes.append(size)
    row={'name':o.name,'vertices':len(bm.verts),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'components':sorted(sizes,reverse=True),'signed_volume':bm.calc_volume(signed=True)}
    if row['nonmanifold_edges']:row['bad_edge_details']=[{'faces':len(e.link_faces),'length':e.calc_length(),'face_areas':[f.calc_area() for f in e.link_faces]} for e in bm.edges if not e.is_manifold][:15]
    rows.append(row);bm.free()
fail=[r for r in rows if r['nonmanifold_edges'] or r['tiny_faces'] or r['signed_volume']<=0 or len(r['components'])!=1]
(folder/'topology_check.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':not fail,'rows':rows,'failures':fail,'scope':'Actual source connected/manifold and nonzero-face checks for named new body meshes only. No collision, fitted contacts, complete runtime or art acceptance.'},indent=2)+'\n')
print('NAUTILUS_TOPOLOGY',json.dumps(fail),flush=True)
