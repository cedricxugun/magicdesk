"""Current fitted caps versus actual evaluated A tongue/suspension combinations."""
import bpy,json,hashlib,math,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/scan_caps_runtime_r43';cap=json.loads((ROOT/'app/assets/collection/art/I/scan_caps_r41/cap.json').read_text());spec=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text());assert hashlib.sha256((ROOT/cap['source']).read_bytes()).hexdigest()==cap['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/cap['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
original=bpy.data.objects[cap['root']];nodes=[]
for i in range(3):
 root=bpy.data.objects.new('R43_Cap_'+str(i),None);bpy.context.scene.collection.objects.link(root);root.parent=bpy.data.objects['IAM_TineRoundedAxial_'+str(i)];root.matrix_basis=Matrix.Identity(4)
 for src in original.children:
  o=src.copy();o.data=src.data;o.name='R43_'+str(i)+'_'+src.name;bpy.context.scene.collection.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);nodes.append(o)
# The glass outer wall and seal inner wall intentionally share one prism.
# Check actual convex halfspaces rather than declaring all cross-mesh hits harmless.
lens=bpy.data.objects['I_ScanCapLens'];seal=bpy.data.objects['I_ScanCapSeal'];housing=bpy.data.objects['I_ScanCapHousing'];interface_errors=[]
inner=[v.co for v in seal.data.vertices if abs(math.hypot(v.co.x,v.co.y)-.0036)<1e-7]
for k in range(96):
 a=math.tau*(k+.5)/96;n=Vector((math.cos(a),math.sin(a),0));plane=min(n.dot(v)for v in inner if abs(math.atan2(math.sin(math.atan2(v.y,v.x)-a),math.cos(math.atan2(v.y,v.x)-a)))<math.tau/96)
 interface_errors.append(max(n.dot(v.co)-plane for v in lens.data.vertices))
assert max(interface_errors)<1e-9
minimum_housing_apothem=.0043*math.cos(math.pi/96);maximum_seal_radius=max(math.hypot(v.co.x,v.co.y)for v in seal.data.vertices);assert minimum_housing_apothem>maximum_seal_radius
volumes=[]
for o in [lens,seal,housing]:
 bm=bmesh.new();bm.from_mesh(o.data);volume=bm.calc_volume(signed=True);assert volume>0;volumes.append({'mesh':o.name,'signed_volume':volume});bm.free()
moving=bpy.data.objects[spec['diaphragm']['moving']];moving.animation_data.action=None
for g in spec['tongues']:bpy.data.objects[g['drive']].animation_data_clear()
deps=bpy.context.evaluated_depsgraph_get()
def tree(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();b=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices)for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return b
poses=[]
for stroke in [-.006,-.003,0.,.003,.006]:
 moving['stroke']=stroke;moving.update_tag();bpy.context.view_layer.update();assert abs(moving.location.z-stroke)<1e-6;poses.append((stroke,[(o.name,tree(o))for o in nodes]))
contacts=[];samples=[]
for k in range(17):
 opening=k/16
 for g in spec['tongues']:
  lo,hi=g['window'];t=max(0,min(1,(opening-lo)/(hi-lo)));drive=bpy.data.objects[g['drive']];drive['feed']=float(t*t*(3-2*t));drive.update_tag()
 bpy.context.view_layer.update();foils=[]
 for g in spec['tongues']:
  o=bpy.data.objects[g['mesh_names'][0]];actual=sum(i*key.value/256 for i,key in enumerate(o.data.shape_keys.key_blocks)if i>0);assert abs(actual-bpy.data.objects[g['drive']]['feed'])<1e-5
  foils.extend((name,tree(bpy.data.objects[name]))for name in g['mesh_names'])
 for stroke,caps in poses:
  for name,ct in caps:
   for foil,ft in foils:
    hits=ct.overlap(ft)
    if hits:contacts.append({'opening':opening,'stroke':stroke,'cap':name,'foil':foil,'triangles':len(hits)})
  samples.append({'opening':opening,'stroke':stroke})
 print('R43_CAP_CLEARANCE',opening,len(contacts),flush=True)
r={'passed':not contacts,'cap_source_sha256':cap['source_sha256'],'mouth_source_sha256':spec['source_sha256'],'samples':samples,'contacts':contacts,'positive_volumes':volumes,'glass_seal_maximum_halfspace_excess':max(interface_errors),'housing_seal_prism_radial_gap':minimum_housing_apothem-maximum_seal_radius,'scope':'Three installed caps: actual evaluated six tongue meshes across 17 openings x 5 independent diaphragm strokes; positive closed component volumes and explicitly shared glass/seal wall with no halfspace penetration. Not continuous sweep or full surrounding assembly/art acceptance.'};(OUT/'cap_clearance.json').write_text(json.dumps(r,indent=2)+'\n');print('R43_CAP_CHECK',r['passed'],flush=True)
