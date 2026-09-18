"""Check the trusted rear outer surface for nonadjacent triangle crossings."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/mouth_relation_r3/build.json');spec=json.loads(path.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['IN1_PorcelainPanel_02'];o.data.calc_loop_triangles();values=[a.value for a in o.data.attributes['formed_wall_fraction'].data];v=[o.matrix_world@p.co for p in o.data.vertices];inv=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();scale=bpy.data.objects['IAM_MODULE'].matrix_world.to_scale().x
faces=[tuple(t.vertices) for t in o.data.loop_triangles if max(values[k] for k in t.vertices)<.001 and min((inv@v[k]).z*scale for k in t.vertices)>.31];tree=BVHTree.FromPolygons(v,faces,all_triangles=True);pairs={tuple(sorted(p)) for p in tree.overlap(tree)};separate=[(i,j) for i,j in pairs if not set(faces[i]).intersection(faces[j])];rows=[]
for i,j in separate[:30]:
    a=[v[k] for k in faces[i]];b=[v[k] for k in faces[j]];na=(a[1]-a[0]).cross(a[2]-a[0]).normalized();nb=(b[1]-b[0]).cross(b[2]-b[0]).normalized();points=a+b
    rows.append({'triangles':[i,j],'normal_dot':na.dot(nb),'bounds':{'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]}})
result={'source_sha256':spec['source_sha256'],'outer_triangles':len(faces),'all_intersection_pairs':len(pairs),'nonadjacent_intersection_pairs':len(separate),'examples':rows,'scope':'02 outer triangles with original trusted wall labels behind axial .31. Nonadjacent means no shared source vertex; excludes the untrusted original loft labels.'}
(path.parent/'receiver_outer_self.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
