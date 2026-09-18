"""Sample rigid source geometry during the R14 opening/reverse layout."""
import bpy,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/receiver_r16';spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();root=bpy.data.objects['IC11_MODULE']
def cache(objects,parent):
 vertices=[];faces=[];owners=[];inverse=parent.matrix_world.inverted()
 for o in objects:
  if o.type not in ['MESH','CURVE']:continue
  e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(vertices);mat=inverse@o.matrix_world
  vertices.extend(mat@v.co for v in m.vertices);faces.extend(tuple(offset+i for i in t.vertices) for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
 return vertices,faces,owners
def tree(data,mat):return BVHTree.FromPolygons([mat@v for v in data[0]],data[1],all_triangles=True,epsilon=0.)
groups=[];moving=set()
for row in spec['rig']:
 o=bpy.data.objects[row['name']];objects=[o]+list(o.children_recursive);moving.update(objects);groups.append((o,cache(objects,o)))
irises=[]
extra_bearings=[{'name':o.name} for o in root.children_recursive if 'BearingEnvelope' in o.name]
for row in spec['leaves']+spec.get('support_envelopes',[])+extra_bearings:
 o=bpy.data.objects[row['name']];objects=[o]+list(o.children_recursive);moving.update(objects);irises.append((o,cache(objects,o)))
fixed=cache([o for o in root.children_recursive if o not in moving],root);fixed_tree=tree(fixed,root.matrix_world);contacts=[];bounds=[]
for frame in range(1,362,10):
 scene.frame_set(frame);bpy.context.view_layer.update();trees=[tree(data,o.matrix_world) for o,data in groups];iris_trees=[tree(data,o.matrix_world) for o,data in irises]
 all_x=[];all_z=[]
 for i,(o,data) in enumerate(groups):
  for v in data[0]:p=o.matrix_world@v;all_x.append(p.x);all_z.append(p.z)
  for other_name,other_data,other_tree in [('fixed',fixed,fixed_tree)]+[(a.name,d,t) for (a,d),t in zip(irises,iris_trees)]+[(groups[j][0].name,groups[j][1],trees[j]) for j in range(i+1,len(groups))]:
   pairs=sorted(set((data[2][a],other_data[2][b]) for a,b in trees[i].overlap(other_tree)))
   if pairs:contacts.append({'frame':frame,'moving':o.name,'against':other_name,'pairs':pairs})
 bounds.append({'frame':frame,'moving_width_D':(max(all_x)-min(all_x))/2.74,'moving_top_D':max(all_z)/2.74})
 print('OPENING_SAMPLE',frame,len(contacts),flush=True)
result={'source_sha256':spec['source_sha256'],'samples':37,'surface_contacts':contacts,'pose_bounds':bounds,'clear_of_all_sampled_contacts':not contacts,'scope':'Moving shells/hood vs each other, static geometry and all moving iris/bearing/support envelopes at 37 times including reverse. Expected layout contacts are retained; no continuous-volume, hardware or art acceptance.'}
(OUT/'clearance.json').write_text(json.dumps(result,indent=2)+'\n');print('I_OPENING_CLEARANCE_CONTACTS',len(contacts),flush=True)
