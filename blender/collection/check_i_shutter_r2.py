"""REST-only surface/topology checks. No assertion about unimplemented motion."""
import bpy,bmesh,json,hashlib,itertools
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2'
r=json.loads((OUT/'build.json').read_text());p=ROOT/r['source'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.view_layer.update();rows=[];trees={}
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();rows.append({'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
 m=o.data;m.calc_loop_triangles();trees[o.name]=BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
pairs=[];contacts=[]
for a,b in itertools.combinations(r['shutter_meshes'],2):
 if trees[a].overlap(trees[b]):pairs.append([a,b])
for a in r['shutter_meshes']:
 for name,t in trees.items():
  if any(s in name for s in ['Porcelain','CentralResonatorCap','HeadBronzeCollar','TineRoot','OuterGuard','MiddleGuard','InnerGuard','IrisOuterCase','ConcaveMachinedMask']):
   if trees[a].overlap(t):contacts.append([a,name])
liner_contacts=[]
for a,at in trees.items():
 if 'IrisOuterCase' not in a:continue
 for b,bt in trees.items():
  if 'Porcelain' in b and at.overlap(bt):liner_contacts.append([a,b])
passed=not pairs and not contacts and not liner_contacts and all(x['nonmanifold_edges']==0 and x['volume']>0 for x in rows)
(OUT/'rest_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'mesh_solids':rows,'rest_leaf_pairs':pairs,'rest_surrounding_contacts':contacts,'liner_porcelain_contacts':liner_contacts,'scoped_passed':passed,'scope':'REST topology and leaf/leaf + listed fixed surfaces, plus metal liner against ivory. Pin-seat engagement, motion, general containment and all-part collisions not accepted.'},indent=2)+'\n')
print('I_SHUTTER_REST_CHECK',passed,'bad solids',sum(x['nonmanifold_edges']>0 or x['volume']<=0 for x in rows),'leaf pairs',len(pairs),'surrounding',len(contacts),'liner/ivory',len(liner_contacts))
