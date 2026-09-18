"""A fitted optical tip accessory on the current actual red terminal mesh."""
import bpy,bmesh,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/scan_caps_r41';ART=ROOT/'app/assets/collection/art/I/scan_caps_r41'
for p in [OUT,ART]:p.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256();o.data.calc_loop_triangles()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for t in o.data.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
 return [h.hexdigest(),[list(r)for r in o.matrix_world]]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'};tip=bpy.data.objects['IAM_TineRoundedAxial_0'];tip.data.calc_loop_triangles();bvh=BVHTree.FromPolygons([v.co for v in tip.data.vertices],[tuple(t.vertices)for t in tip.data.loop_triangles],all_triangles=True)
for i in [1,2]:assert [tuple(v.co)for v in bpy.data.objects[f'IAM_TineRoundedAxial_{i}'].data.vertices]==[tuple(v.co)for v in tip.data.vertices]
col=bpy.data.collections.new('SCAN_CAP_R41');bpy.context.scene.collection.children.link(col);root=bpy.data.objects.new('I_ScanCapRoot',None);col.objects.link(root)
def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
metal=material('I41_NickelGold',(.36,.27,.14),.94,.23);rubber=material('I41_DarkSeal',(.012,.013,.011),0,.60);glass=material('I41_AmberOptic',(.17,.067,.012),.05,.13)
N=96;gap=.000025;back_samples=[]
def seat(r,a):
 hit=bvh.ray_cast(Vector((r*math.cos(a),r*math.sin(a),-.03)),Vector((0,0,1)),.05);assert hit[0]is not None
 back_samples.append({'r':r,'angle':a,'surface_z':hit[0].z,'seat_z':hit[0].z-gap});return hit[0].z-gap
def mesh_from_rings(name,definitions,mat):
 verts=[];rings=[];faces=[]
 for r,z in definitions:
  if r==0:rings.append([len(verts)]);verts.append((0,0,z if not callable(z)else z(0)))
  else:
   ring=[]
   for k in range(N):a=math.tau*k/N;ring.append(len(verts));verts.append((r*math.cos(a),r*math.sin(a),z(a)if callable(z)else z))
   rings.append(ring)
 for j,a in enumerate(rings):
  b=rings[(j+1)%len(rings)]
  if len(a)==len(b)==1:continue
  for k in range(N):
   if len(a)==1:faces.append((a[0],b[k],b[(k+1)%N]))
   elif len(b)==1:faces.append((a[k],b[0],a[(k+1)%N]))
   else:faces.append((a[k],b[k],b[(k+1)%N],a[(k+1)%N]))
 m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);o.parent=root;m.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges)
 for f in bm.faces:f.smooth=True
 for e in bm.edges:e.smooth=e.calc_face_angle()<.50
 bm.to_mesh(m);bm.free();m.update();return o
# The back annulus samples the actual triangulated red terminal, not an ideal sphere.
profile=[(.0043,-.01022),(.00436,-.01040),(.00451,-.01050),(.00635,-.01050),(.00657,-.01042),(.00670,-.01022)]
for j in range(17):
 r=.00670-(.00670-.0043)*j/16;profile.append((r,lambda a,r=r:seat(r,a)))
housing=mesh_from_rings('I_ScanCapHousing',profile,metal)
seal=mesh_from_rings('I_ScanCapSeal',[(.00360,-.01004),(.00360,-.01040),(.00428,-.01040),(.00428,-.01004)],rubber)
lens_profile=[(0.,-.01090)]+[(.00360*j/16,-.01090+.00050*(j/16)**2)for j in range(1,17)]+[(.00360,-.01004),(0.,-.01004)]
lens=mesh_from_rings('I_ScanCapLens',lens_profile,glass)
assert all(fingerprint(bpy.data.objects[n])==v for n,v in protected.items())
checks=[]
for o in [housing,seal,lens]:
 m=o.data;m.calc_loop_triangles();v=[x.co.copy()for x in m.vertices];tris=[tuple(t.vertices)for t in m.loop_triangles];tree=BVHTree.FromPolygons(v,tris,all_triangles=True);raw=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(tris[a])&set(tris[b])];contacts=tree.overlap(bvh)
 checks.append({'mesh':o.name,'vertices':len(v),'triangles':len(tris),'self_contacts':raw,'terminal_intersections':contacts})
assert all(not c['self_contacts']and not c['terminal_intersections']for c in checks),checks
source=ROOT/'blender/collection/I_scan_cap_r41.blend';component=ART/'cap.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'mouth_source_sha256':s['source_sha256'],'mouth_component_sha256':s['component_sha256'],'root':'I_ScanCapRoot','lens':'I_ScanCapLens','focus_local_blender':[0,0,-.01090],'outer_radius':.00670,'seat_gap':gap,'protected_source_meshes':len(protected),'geometry_checks':checks,'scope':'New small accessory seated over existing actual red spherical terminal. Original A geometry/transforms preserved. Source self/terminal intersections checked; cap-to-cap interfaces and runtime attachment still pending.'};(ART/'cap.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'seat_samples.json').write_text(json.dumps(back_samples,indent=2)+'\n');print('R41_CAP',d['source_sha256'],flush=True)
