"""Three-tongue evaluated sweep, including other tongues and their moving hardware."""
import bpy,bmesh,json,hashlib,itertools,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/tongue_set')
r=json.loads((OUT/'build.json').read_text());source=ROOT/r['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==r['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def data(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();ret=([o.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles]);e.to_mesh_clear();return ret
def tree(d):return BVHTree.FromPolygons(d[0],d[1],all_triangles=True)
names=[name for group in r['tongues'] for name in group['mesh_names']];foils=[bpy.data.objects[name] for name in names];other=[o for o in bpy.data.objects if o.type=='MESH' and o.name not in names];moving=set()
for group in r['tongues']:
 moving.update(bpy.data.objects[group['carriage']].children_recursive)
 if 'guide_roll' in group:moving.update(bpy.data.objects[group['guide_roll']['rotor']].children_recursive)
if 'diaphragm' in r:
 moving.update(bpy.data.objects[r['diaphragm']['moving']].children_recursive)
 moving.update(bpy.data.objects[name] for name in r['diaphragm']['morphs'])
static=[(o.name,tree(data(o))) for o in other if o not in moving];solids=[]
for o in [*foils,*other]:
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();solids.append({'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
contacts=[];self_hits=[];samples=[]
frames=sorted(set(range(1,434,8))|{48,72,128,151,175,253,433})
for frame in frames:
 scene.frame_set(frame);bpy.context.view_layer.update();dynamic=[(o.name,tree(data(o))) for o in other if o in moving];built=[]
 for foil in foils:
  d=data(foil);t=tree(d);built.append((foil.name,t));triangles=[set(f) for f in d[1]];count=0
  for a,b in t.overlap(t):
   if a<b and not triangles[a].intersection(triangles[b]):count+=1
  if count:self_hits.append({'frame':frame,'foil':foil.name,'count':count})
  for name,other_tree in static+dynamic:
   overlap=t.overlap(other_tree)
   if overlap:contacts.append({'frame':frame,'foil':foil.name,'against':name,'count':len(overlap)})
 for (a,ta),(b,tb) in itertools.combinations(built,2):
  overlap=ta.overlap(tb)
  if overlap:contacts.append({'frame':frame,'foil':a,'against':b,'count':len(overlap)})
 time=(frame-1)/60;g=max(0,min(1,(time-.4)/2.6)) if time<4.2 else 1-max(0,min(1,(time-4.2)/2.6));feeds=[]
 for group in r['tongues']:
  start,end=group['window'];t=max(0,min(1,(g-start)/(end-start)));expected=t*t*(3-2*t);actual=float(bpy.data.objects[group['drive']]['feed']);feeds.append({'actual':actual,'expected':expected,'error':abs(actual-expected)})
 samples.append({'frame':frame,'feeds':feeds});print('SET_SWEEP',frame,len(contacts),len(self_hits),flush=True)
passed=not contacts and not self_hits and all(x['nonmanifold_edges']==0 and x['volume']>0 for x in solids) and max(x['error'] for row in samples for x in row['feeds'])<1e-5
(OUT/'geometry_check.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'scoped_passed':passed,'mesh_solids':solids,'contacts':contacts,'self_surface_contacts':self_hits,'samples':samples,'scope':'Listed source forward/hold/reverse frames, six foils against all other scene surfaces and one another, self nonadjacent surfaces and base topology. Fixed hardware pairs, continuous collision and AAA/native input acceptance not covered.'},indent=2)+'\n');print('I_TONGUE_SET_CHECK',passed,flush=True)
