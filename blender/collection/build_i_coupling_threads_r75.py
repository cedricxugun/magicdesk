"""Thread the six actual coupling bores for a defined short release travel."""
import bpy,bmesh,json,hashlib,math,array
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/coupling_threads_r75';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/seam_release_r73/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];assert json.loads((ROOT/'review/I_refinement/nautilus_r1/seam_release_r73/thread_interlock.json').read_text())['passed'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();mount=bpy.data.objects['IC1_MouthMount'];F=mount.matrix_world.copy();inv=F.inverted()
allowed={'IC1_CollarUpper','IC1_CollarLower'}|{'IN3_CouplingBolt_%02d'%i for i in range(6)}
def fingerprint(o):
 m=o.data;m.calc_loop_triangles();h=hashlib.sha256()
 for c,p,w,k in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
  a=array.array(k,[0])*(len(c)*w);c.foreach_get(p,a);h.update(a.tobytes())
 for uv in m.uv_layers:
  a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);h.update(a.tobytes())
 if m.shape_keys:
  for key in m.shape_keys.key_blocks:
   a=array.array('f',[0])*(len(key.data)*3);key.data.foreach_get('co',a);h.update(key.name.encode());h.update(a.tobytes())
 return h.hexdigest(),[list(r)for r in o.matrix_world],[x.name if x else None for x in m.materials],[p.material_index for p in m.polygons]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in allowed}
def geo(o):
 m=o.data;m.calc_loop_triangles();v=[o.matrix_world@x.co for x in m.vertices];f=[tuple(t.vertices)for t in m.loop_triangles];return BVHTree.FromPolygons(v,f,all_triangles=True),v,f
def solid(o):
 bm=bmesh.new();bm.from_mesh(o.data);nonmanifold=sum(not e.is_manifold for e in bm.edges)+sum(not v.is_manifold for v in bm.verts);volume=bm.calc_volume(signed=True);bm.free();tree,v,f=geo(o);hits=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(f[a])&set(f[b])];return {'name':o.name,'nonmanifold':nonmanifold,'volume':volume,'self_contacts':len(hits),'pairs':hits[:20]}
def smooth(x):x=max(0.,min(1.,x));return x*x*(3-2*x)
pitch=.0006;clearance=.00003;cut=.6352;tip=.628
stations=[cut+(tip-cut)*i/144 for i in range(1,145)]
def male_radius(z,a):
 r=.00305+.00015*(.5+.5*math.cos(math.tau*((z-.6285)/pitch-a/math.tau)))
 r=.0032+(r-.0032)*smooth((.6348-z)/.0004)
 if z<.6285:r=r+(.0027-r)*smooth((.6285-z)/.0005)
 return r
centers=[Vector((.502*math.cos(math.pi/6+i*math.tau/6),.502*math.sin(math.pi/6+i*math.tau/6),0))for i in range(6)]
old_collars={n:geo(bpy.data.objects[n])for n in ['IC1_CollarUpper','IC1_CollarLower']};rows=[];checks=[]
for i,center in enumerate(centers):
 bolt=bpy.data.objects['IN3_CouplingBolt_%02d'%i];M=bolt.matrix_world.copy();to_parent=inv@M;from_parent=M.inverted()@F
 bm=bmesh.new();bm.from_mesh(bolt.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=from_parent@Vector((center.x,center.y,cut)),plane_no=M.to_3x3().transposed()@F.to_3x3().col[2].normalized(),dist=1e-9,clear_inner=True)
 edges=[e for e in bm.edges if e.is_boundary];vertices={v for e in edges for v in e.verts};assert len(vertices)==len(edges)and len(vertices)>=32
 order=sorted(vertices,key=lambda v:math.atan2((to_parent@v.co).y-center.y,(to_parent@v.co).x-center.x));angles=[math.atan2((to_parent@v.co).y-center.y,(to_parent@v.co).x-center.x)for v in order];assert max(abs(math.hypot((to_parent@v.co).x-center.x,(to_parent@v.co).y-center.y)-.0032)for v in order)<1e-6
 for z in stations:
  ring=[bm.verts.new(from_parent@Vector((center.x+male_radius(z,a)*math.cos(a),center.y+male_radius(z,a)*math.sin(a),z)))for a in angles]
  for k in range(len(order)):bm.faces.new((order[k],order[(k+1)%len(order)],ring[(k+1)%len(order)],ring[k]))
  order=ring
 bm.faces.new(tuple(reversed(order)));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(bolt.data);bm.free();bolt.data.update()
 for f in bolt.data.polygons:f.use_smooth=len(f.vertices)==4
 # Add same-metal stock inside the old clearance bore. Its outside overlaps
 # existing collar stock; endpoints end within stock, not at coincident bore faces.
 N=64;aa=[k*math.tau/N for k in range(N)];vv=[];ff=[];rings=[]
 def ring(z,radius):
  ids=[]
  for a in aa:
   r=radius(a)if callable(radius)else radius;ids.append(len(vv));vv.append((center.x+r*math.cos(a),center.y+r*math.sin(a),z))
  rings.append(ids)
 ring(.628,.0037);ring(.6345,.0037)
 def inner(z,a):
  r=male_radius(z,a)+clearance
  if z<.6286:r=r+(.0036-r)*smooth((.6286-z)/.0006)
  if z>.6338:r=r+(.0036-r)*smooth((z-.6338)/.0007)
  return r
 female_z=sorted({.628,.6345}|{z for z in stations if .628<z<.6345},reverse=True)
 for z in female_z:ring(z,lambda a,z=z:inner(z,a))
 for j in range(len(rings)):
  a=rings[j];b=rings[(j+1)%len(rings)]
  for k in range(N):ff.append((a[k],a[(k+1)%N],b[(k+1)%N],b[k]))
 mesh=bpy.data.meshes.new('R75ThreadStock');mesh.from_pydata(vv,[],ff);mesh.update();tool=bpy.data.objects.new('R75ThreadStock',mesh);bolt.users_collection[0].objects.link(tool);tool.parent=mount
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 collar=bpy.data.objects['IC1_CollarUpper'if i<3 else 'IC1_CollarLower'];tool.data.materials.append(collar.data.materials[0]);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=collar;mod=collar.modifiers.new('Local machined coupling thread','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
 row={'index':i,'bolt':bolt.name,'collar':collar.name,'center_parent':list(center),'axis_parent':[0,0,1],'pitch_parent':pitch,'radial_clearance_parent':clearance,'nominal_female_engagement_parent':[.6286,.6338],'release_world_distance':.006,'release_parent_distance':.006/F.to_3x3().col[2].length};rows.append(row);checks.append(solid(bolt));print('R75_THREAD',i,checks[-1],flush=True)
for name in old_collars:checks.append(solid(bpy.data.objects[name]))
fit=[]
for row in rows:
 bt,_,_=geo(bpy.data.objects[row['bolt']]);ct,_,_=geo(bpy.data.objects[row['collar']]);fit.append({'bolt':row['bolt'],'collar':row['collar'],'contacts':len(bt.overlap(ct))})
exterior=[]
for name,(old_tree,old_vertices,_)in old_collars.items():
 tree,_,_=geo(bpy.data.objects[name]);distances=[]
 for p in old_vertices:
  q=inv@p
  if any(math.hypot(q.x-c.x,q.y-c.y)<.0042 and .6275<q.z<.635 for c in centers):continue
  distances.append(tree.find_nearest(p)[3])
 exterior.append({'collar':name,'samples':len(distances),'max_distance':max(distances)})
proof={'parent_source_sha256':s['source_sha256'],'changed_meshes':sorted(allowed),'protected_meshes':len(protected),'threads':rows,'solids':checks,'closed_fit':fit,'outside_thread_regions':exterior,'scope':'Six actual male tips and local same-metal tapped bores in existing clamp halves. Short release engagement specified; source self/closed fit and protected exterior checked. Dynamic helix, assembly clearance, visuals and load behavior pending.'};(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n');print('R75_CHECK',[(c['name'],c['nonmanifold'],c['self_contacts'])for c in checks],fit,exterior,flush=True)
assert all(c['nonmanifold']==0 and c['volume']>0 and c['self_contacts']==0 for c in checks);assert all(r['contacts']==0 for r in fit);assert max(r['max_distance']for r in exterior)<2e-6;assert all(fingerprint(bpy.data.objects[n])==p for n,p in protected.items())
source=ROOT/'blender/collection/I_nautilus_coupling_threads_r75.blend';component=ROOT/'app/assets/collection/components/I_nautilus_coupling_threads_r75.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/coupling_threads_r75';ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n');d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'coupling_threads':proof,'chamber_response_layout':'res://assets/collection/art/I/coupling_threads_r75/chamber_layout.json','status':'coupling_thread_candidate_dynamic_checks_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('R75_SAVED',d['source_sha256'])
