"""Part A actual evaluated surface/shaft/cam checks, scoped and explicit."""
import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth';r=json.loads((OUT/'build.json').read_text());src=ROOT/r['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==r['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def cached(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();data=([v.co.copy() for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles]);e.to_mesh_clear();return data
def tree(o,data):return BVHTree.FromPolygons([o.matrix_world@v for v in data[0]],data[1],all_triangles=True)
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();rows.append({'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)});bm.free()
leaves=[(bpy.data.objects[x['sheet']],cached(bpy.data.objects[x['sheet']])) for x in r['leaves']]
target_names=['CentralResonatorCap','ConcaveMachinedMask','ClearApertureFineLip','IrisOuterCase','OuterGuard','MiddleGuard','InnerGuard','Porcelain','IrisPivotPin']
targets=[(o,cached(o)) for o in bpy.data.objects if o.type=='MESH' and any(n in o.name for n in target_names)];tt=[(o.name,tree(o,d)) for o,d in targets];contacts=[];cam_errors=[];leaf_pair_errors=[];follower_leaf_errors=[]
cam=bpy.data.objects[r['cam']];cam_ring=next(o for o in cam.children if 'SlottedCam' in o.name);cd=cached(cam_ring)
for frame in range(1,242,3):
 scene.frame_set(frame);bpy.context.view_layer.update();ct=tree(cam_ring,cd)
 leaf_trees=[(o,tree(o,d)) for o,d in leaves]
 for j,(o,t) in enumerate(leaf_trees):
  for name,other in tt:
   if t.overlap(other):contacts.append({'frame':frame,'leaf':o.name,'against':name})
  for ob,other in leaf_trees[j+1:]:
   if t.overlap(other):leaf_pair_errors.append({'frame':frame,'leaf':o.name,'against':ob.name})
 for row in r['leaves']:
  o=bpy.data.objects[row['follower']];t=tree(o,cached(o))
  if t.overlap(ct):cam_errors.append({'frame':frame,'follower':o.name})
  for other,ot in leaf_trees:
   if other.name!=row['sheet'] and t.overlap(ot):follower_leaf_errors.append({'frame':frame,'follower':o.name,'against':other.name})
report={'source_sha256':r['source_sha256'],'mesh_solids':rows,'leaf_surrounding_surface_contacts':contacts,'leaf_pair_surface_contacts':leaf_pair_errors,'follower_other_leaf_contacts':follower_leaf_errors,'cam_follower_surface_contacts':cam_errors,'scoped_passed':not contacts and not cam_errors and not leaf_pair_errors and not follower_leaf_errors and all(x['nonmanifold_edges']==0 and x['signed_volume']>0 for x in rows),'scope':'Every mesh topology; 81 sampled leaf vs surrounding parts including ceramic/pivot pins; every leaf pair; followers vs other leaves and cam slots. No full all-pair assembly or containment, native input or art acceptance.'};(OUT/'geometry_check.json').write_text(json.dumps(report,indent=2)+'\n');print('PART_A_CHECK',len([x for x in rows if x['nonmanifold_edges'] or x['signed_volume']<=0]),'bad solids',len(contacts),'leaf contacts',len(leaf_pair_errors),'leaf pairs',len(follower_leaf_errors),'follower/leaf',len(cam_errors),'cam contacts',flush=True)
