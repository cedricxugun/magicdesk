"""Evaluated morph motion contacts, not merely analytic centerline bounds."""
import bpy,bmesh,json,hashlib,os
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/tongue_probe';r=json.loads((OUT/'build.json').read_text());src=ROOT/r['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==r['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();solids=[]
def data(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();vs=[o.matrix_world@v.co for v in m.vertices];fs=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return vs,fs
def tree(d):return BVHTree.FromPolygons(d[0],d[1],all_triangles=True)
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();solids.append({'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
foils=[bpy.data.objects[n] for n in r['mesh_names']];others=[o for o in bpy.data.objects if o.type=='MESH' and o.name not in r['mesh_names']]
# Static tree caches are valid only for nodes outside the animated carriage.
carriage=bpy.data.objects[r['carriage']];moving=set(carriage.children_recursive);static=[(o.name,tree(data(o))) for o in others if o not in moving]
contacts=[];self_hits=[];samples=[]
interpolation=os.environ.get('MAGICDESK_TONGUE_INTERPOLATION')=='1'
if interpolation:
 for name in [r['drive'],r['carriage'],r['spool']]:bpy.data.objects[name].animation_data_clear()
frames=list(range(r['pose_steps'])) if interpolation else sorted(set(range(1,338,8))|{139,199,319,337})
for frame in frames:
 if interpolation:
  amount=(frame+.5)/r['pose_steps'];bpy.data.objects[r['drive']]['feed']=float(amount);a=r['states'][frame];b=r['states'][frame+1]
  bpy.data.objects[r['carriage']].location=[(x+y)*.5 for x,y in zip(a['axis'],b['axis'])];bpy.data.objects[r['spool']].rotation_euler.z=r['spin_sign']*(a['angle']+b['angle'])*.5
  bpy.data.objects[r['drive']].update_tag();label={'between_poses':[frame,frame+1]}
 else:scene.frame_set(frame);label={'frame':frame}
 bpy.context.view_layer.update();dyn=[(o.name,tree(data(o))) for o in others if o in moving];built=[]
 for foil in foils:
  d=data(foil);t=tree(d);built.append((foil.name,t));triangles=[set(f) for f in d[1]];hits=[]
  for a,b in t.overlap(t):
   if a<b and not triangles[a].intersection(triangles[b]):hits.append([a,b])
  if hits:self_hits.append({**label,'foil':foil.name,'count':len(hits),'examples':hits[:8]})
  for name,other in static+dyn:
   pairs=t.overlap(other)
   if pairs:contacts.append({**label,'foil':foil.name,'against':name,'count':len(pairs)})
 if built[0][1].overlap(built[1][1]):contacts.append({**label,'foil':built[0][0],'against':built[1][0],'count':len(built[0][1].overlap(built[1][1]))})
 time=(frame-1)/60;v=max(0,min(1,(time-.3)/2)) if time<3.3 else 1-max(0,min(1,(time-3.3)/2));expected=v*v*(3-2*v)
 if interpolation:expected=amount
 samples.append({**label,'feed':float(bpy.data.objects[r['drive']]['feed']),'expected_feed':expected,'feed_error':abs(float(bpy.data.objects[r['drive']]['feed'])-expected)})
 print('TONGUE_FRAME_CHECK',frame,len(contacts),len(self_hits),flush=True)
passed=not contacts and not self_hits and max(x['feed_error'] for x in samples)<1e-5 and all(x['nonmanifold_edges']==0 and x['volume']>0 for x in solids)
report={'source_sha256':r['source_sha256'],'sampling_mode':'all_pose_interval_midpoints' if interpolation else 'source_forward_hold_reverse_frames','mesh_solids':solids,'samples':samples,'contacts':contacts,'self_surface_contacts':self_hits,'scoped_passed':passed,'scope':'Actual evaluated morph geometry at listed samples. Foils vs all scene meshes and each other, nonadjacent self triangle surfaces, base mesh topology. Midpoint mode uses runtime table interpolation for carriage/spool. Not a continuous collision proof, material stress/strain validation, complete hardware or original-art acceptance.'}
(OUT/('interpolation_check.json' if interpolation else 'geometry_check.json')).write_text(json.dumps(report,indent=2)+'\n');print('I_TONGUE_CHECK',passed,len(contacts),len(self_hits),flush=True)
