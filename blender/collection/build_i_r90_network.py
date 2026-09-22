"""Build the fitted continuous metal backbone, authored opal paths and
real blind sockets from R90's approved-direction routing study."""
import bpy,bmesh,json,math,hashlib,sys,array
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_formed_coil_surface import FormedCoilSurface
import i_machined_geometry as P
version='r5' if '--socket-fit' in sys.argv else 'r4' if '--manifolds' in sys.argv else 'r3' if '--refined' in sys.argv else 'r2' if '--visible' in sys.argv else 'r1'
manifolds=version in ['r4','r5']
BASE=R/'review/I_refinement/nautilus_reset_r82';OUT=BASE/f'network_r90/built_{version}';OUT.mkdir(parents=True,exist_ok=True)
old=json.loads((BASE/'chambers_r89/built_r3/build.json').read_text());paths=json.loads((BASE/f'network_r90/paths_{"r3" if manifolds else version}.json').read_text());plate=json.loads((BASE/f'network_r90/plate_parameters_{"r4" if version=="r5" else version}.json').read_text())
assert paths['source_sha256']==old['source_sha256'] and not plate['nonmanifold_edges']
assert hashlib.sha256((R/old['source']).read_bytes()).hexdigest()==old['source_sha256']
SRC=R/f'blender/collection/I_r90_acoustic_network_{version}.blend';COMP=R/f'app/assets/collection/components/I_r90_acoustic_network_{version}.glb';assert not SRC.exists() and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];col=bpy.data.collections['R82_NEW_FORM'];P.configure(col)
surface=FormedCoilSurface(json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'],bpy.data.objects['IAM_Mouth'].matrix_world.inverted(),old['formed_liner_return'])
frames={x['frame']for x in old['new_cells']};liner=bpy.data.objects['R82_Acoustic_Chamber_Liner']
def fingerprint(o):
 h=hashlib.sha256();v=array.array('f',[0.])*(3*len(o.data.vertices));o.data.vertices.foreach_get('co',v);h.update(v.tobytes());idx=array.array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',idx);h.update(idx.tobytes());h.update(str([tuple(row)for row in o.matrix_world]).encode());return h.hexdigest()
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH' and o.name not in frames and o!=liner}
group=P.empty('I90_ACOUSTIC_BACKPLANE',root)
for ob in [liner]+[o for o in root.children_recursive if o.name.startswith('I84_Cell_')]:ob.parent=group
def material(name,color,metal,rough,emission=0.):
 ma=bpy.data.materials.new('Collection_'+name);ma.use_nodes=True;bs=ma.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;bs.inputs['Emission Color'].default_value=(1.,.55,.16,1);bs.inputs['Emission Strength'].default_value=emission;return ma
nickel=material('I90_Nickel',(.55,.50,.41),.95,.28);groove_mat=material('I90_Recess',(.095,.059,.028),.82,.33);opal=material('I90_Opal',(.70,.57,.36),0.,.24,1.6)
if version in ['r3','r4','r5']:nickel.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.64,.61,.52,1)
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.parent=group;me.materials.append(mat);return ob
def boolean(ob,tool,operation='DIFFERENCE',solver='EXACT'):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob;m=ob.modifiers.new('Manufactured socket','BOOLEAN');m.operation=operation;m.solver=solver;m.object=tool;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(tool,do_unlink=True)
parameters=[tuple(v)for v in plate['vertices']];triangles=[tuple(t)for t in plate['triangles']];tags=plate['tags'];positions=[]
def position(p):return surface.point(p[0],p[1])+surface.normal(p[0],p[1])*p[2]
positions=[position(p)for p in parameters]
# Shared-edge refinement preserves all closed profile boundaries.
for iteration in range(9):
 edges={tuple(sorted((a,b)))for f in triangles for a,b in zip(f,f[1:]+f[:1])};marked={}
 for a,b in edges:
  pa,pb=parameters[a],parameters[b]
  if max(abs(pa[0]-pb[0]),abs(pa[1]-pb[1]))>.035 or (positions[a]-positions[b]).length>.022:
   p=tuple((pa[k]+pb[k])/2 for k in range(3));marked[(a,b)]=len(parameters);parameters.append(p);positions.append(position(p))
 if not marked:break
 new=[];new_tags=[]
 for (a,b,c),tag in zip(triangles,tags):
  x=marked.get(tuple(sorted((a,b))));y=marked.get(tuple(sorted((b,c))));z=marked.get(tuple(sorted((c,a))));n=sum(v is not None for v in [x,y,z])
  if n==0:pieces=[(a,b,c)]
  elif n==3:pieces=[(a,x,z),(x,b,y),(z,y,c),(x,y,z)]
  elif n==1:
   if y is not None:a,b,c,x=b,c,a,y
   elif z is not None:a,b,c,x=c,a,b,z
   pieces=[(a,x,c),(x,b,c)]
  else:
   if x is None:a,b,c,x,y=b,c,a,y,z
   elif y is None:a,b,c,x,y=c,a,b,z,x
   pieces=[(b,y,x),(a,x,c),(x,y,c)]
  new.extend(pieces);new_tags.extend([tag]*len(pieces))
 triangles,tags=new,new_tags;print('R90_REFINE',iteration,len(parameters),len(triangles),flush=True)
else:raise AssertionError('Surface refinement did not converge')
base_points=np.array([tuple(surface.point(p[0],p[1]))for p in parameters]);factors=np.ones(len(parameters))
for seg in paths['segments']:
 if seg['kind']!='feed':continue
 for a,b in zip(seg['samples'],seg['samples'][1:]):
  pa=np.array(a['p']);pb=np.array(b['p']);v=pb-pa;den=float(v@v)
  if den<1e-16:continue
  f=np.clip((base_points-pa)@v/den,0,1);closest=pa+f[:,None]*v;distance=np.linalg.norm(base_points-closest,axis=1);width=a['width']*(1-f)+b['width']*f;hs=a.get('height_scale',1.)*(1-f)+b.get('height_scale',1.)*f;q=np.clip((distance-width*1.2)/(width*.8),0,1);influence=1-q*q*(3-2*q);factors=np.minimum(factors,1-(1-hs)*influence)
positions=[Vector(base_points[i])+surface.normal(p[0],p[1])*(p[2]*(factors[i]if p[2]>0 else 1.))for i,p in enumerate(parameters)]
backbone=mesh('I90_CastBackbone',positions,triangles,nickel);backbone.data.materials.append(groove_mat)
bm=bmesh.new();bm.from_mesh(backbone.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();param_layer=bm.verts.layers.float_vector.new('surface_param');region=bm.faces.layers.int.new('surface_region');tag_ids={'bottom':0,'top':1,'floor':2,'outer_bevel':3,'groove_bevel':4,'side':5}
for v,p in zip(bm.verts,parameters):v[param_layer]=Vector(p)
for f,tag in zip(bm.faces,tags):f[region]=tag_ids[tag];f.material_index=1 if tag=='floor'else 0
before_vertices=len(bm.verts);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
bm.to_mesh(backbone.data);bm.free()
for p in backbone.data.polygons:p.use_smooth=True
uv=backbone.data.uv_layers.new(name='CoilSurfaceUV')
for face in backbone.data.polygons:
 for li in face.loop_indices:
  p=backbone.data.attributes['surface_param'].data[backbone.data.loops[li].vertex_index].vector;uv.data[li].uv=(p.x/surface.T,p.y/math.pi)
# Distance-authored solid opal branches; each remains an independent light path.
segments=[];light_paths=[];ports_by_cell={p['cell']:p for p in paths['ports']}
def interpolate_sample(a,b,f):
 p={}
 for key in a:
  if isinstance(a[key],list):p[key]=[x*(1-f)+y*f for x,y in zip(a[key],b[key])]
  elif isinstance(a[key],(int,float)):p[key]=a[key]*(1-f)+b[key]*f
  else:p[key]=a[key]
 return p
for seg in paths['segments']:
 if not manifolds:light_paths.append(seg);continue
 pieces=[];current=[]
 for a,b in zip(seg['samples'],seg['samples'][1:]):
  intervals=[(0.,1.)];pa=Vector(a['p']);pb=Vector(b['p']);v=pb-pa
  for cap in plate['caps']:
   centre=Vector(cap['p']);n=Vector(cap['n']);w=pa-centre;vv=v-n*v.dot(n);ww=w-n*w.dot(n);aa=vv.length_squared;bb=2*ww.dot(vv);cc=ww.length_squared-cap['ring_radius']**2;disc=bb*bb-4*aa*cc
   if aa<1e-15:
    if cc>=0:continue
    left,right=0.,1.
   elif disc<=0:continue
   else:left,right=max(0.,(-bb-math.sqrt(disc))/(2*aa)),min(1.,(-bb+math.sqrt(disc))/(2*aa))
   if right<=left or abs((pa+v*((left+right)/2)-centre).dot(n))>.020:continue
   remaining=[]
   for x,y in intervals:
    if right<=x or left>=y:remaining.append((x,y))
    else:
     if left>x:remaining.append((x,left))
     if right<y:remaining.append((right,y))
   intervals=remaining
  for left,right in intervals:
   aa=interpolate_sample(a,b,left);bb=interpolate_sample(a,b,right)
   if current and abs(current[-1]['distance']-aa['distance'])<1e-8:current.append(bb)
   else:
    if len(current)>1:pieces.append(current)
    current=[aa,bb]
  if not intervals and current:
   if len(current)>1:pieces.append(current)
   current=[]
 if len(current)>1:pieces.append(current)
 for i,piece in enumerate(pieces):light_paths.append({**seg,'id':str(seg['id'])+('_'+str(i)if len(pieces)>1 else ''),'samples':piece})
for seg in light_paths:
 samples=seg['samples'];verts=[];faces=[];uvs=[];N=16
 centres=[Vector(p['p'])+Vector(p['n'])*((.0052 if seg['kind']=='spine'else .0030+.0044*(p.get('height_scale',1.)-.5))if manifolds else .0059*p.get('height_scale',1.))for p in samples]
 if version=='r5' and seg['kind']=='feed':
  port=ports_by_cell[seg['cell']]
  if abs(samples[-1]['uv_distance']-port['distance']/paths['maximum_distance'])<1e-8:
   out=Vector(port['outward']);target=Vector(port['anchor'])+out*.0035;step=min(.002,seg['length']/max(1,len(centres)-1))
   for i in range(max(0,len(centres)-3),len(centres)):centres[i]=target+out*(step*(len(centres)-1-i))
 for i,p in enumerate(samples):
  tangent=(centres[min(i+1,len(centres)-1)]-centres[max(0,i-1)]).normalized();normal=Vector(p['n']);side=tangent.cross(normal).normalized();normal=side.cross(tangent).normalized()
  for k in range(N):
   a=math.tau*k/N;verts.append(centres[i]+side*(p['glass_radius']*math.cos(a))+normal*(p['glass_radius']*math.sin(a)));uvs.append((p['uv_distance'],k/N))
 for i in range(len(samples)-1):
  for k in range(N):faces.append((i*N+k,i*N+(k+1)%N,(i+1)*N+(k+1)%N,(i+1)*N+k))
 faces +=[tuple(range(N-1,-1,-1)),tuple((len(samples)-1)*N+k for k in range(N))]
 label=str(seg['id']).zfill(2);ob=mesh(f'I90_OpalPath_{label}',verts,faces,opal);uv=ob.data.uv_layers.new(name='RootDistanceUV')
 for face in ob.data.polygons:
  face.use_smooth=len(face.vertices)==4
  for li in face.loop_indices:uv.data[li].uv=uvs[ob.data.loops[li].vertex_index]
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 segments.append({'mesh':ob.name,'material':opal.name,'bands':seg['bands'],'cells':seg['cells'],'uv_start':samples[0]['uv_distance'],'uv_end':samples[-1]['uv_distance'],'length':seg['length'],'phase_offset':0.})
if manifolds:
 for cap in plate['caps']:
  jt=Vector(cap['jt']);ju=Vector(cap['ju']);n=Vector(cap['n']);ex=jt.normalized();ey=n.cross(ex).normalized();aa=jt.dot(jt);bb=jt.dot(ju);cc=ju.dot(ju);den=aa*cc-bb*bb;centres=[];normals=[];verts=[];faces=[];uvs=[];N=64;NC=12;uv_distance=cap['distance']/paths['maximum_distance']
  for i in range(N):
   a=math.tau*i/N;delta=(ex*math.cos(a)+ey*math.sin(a))*cap['ring_radius'];dt=(jt.dot(delta)*cc-ju.dot(delta)*bb)/den;du=(ju.dot(delta)*aa-jt.dot(delta)*bb)/den;t=cap['t']+dt;u=cap['u']+du;nn=surface.normal(t,u);centres.append(surface.point(t,u)+nn*.0045);normals.append(nn)
  for i in range(N):
   tangent=(centres[(i+1)%N]-centres[(i-1)%N]).normalized();side=tangent.cross(normals[i]).normalized()
   for k in range(NC):
    a=math.tau*k/NC;verts.append(centres[i]+(side*math.cos(a)+normals[i]*math.sin(a))*cap['ring_glass_radius']);uvs.append((uv_distance,k/NC))
  for i in range(N):
   for k in range(NC):faces.append((i*NC+k,((i+1)%N)*NC+k,((i+1)%N)*NC+(k+1)%NC,i*NC+(k+1)%NC))
  ob=mesh(f'I90_HubOpal_{cap["node"]}',verts,faces,opal);uv=ob.data.uv_layers.new(name='RootDistanceUV')
  for face in ob.data.polygons:
   face.use_smooth=True
   for li in face.loop_indices:uv.data[li].uv=uvs[ob.data.loops[li].vertex_index]
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();inc=[s for s in paths['segments']if s['start']==cap['node']or s['end']==cap['node']]
  segments.append({'mesh':ob.name,'material':opal.name,'bands':sorted({b for s in inc for b in s['bands']}),'cells':sorted({c for s in inc for c in s['cells']}),'uv_start':uv_distance,'uv_end':uv_distance,'length':math.tau*cap['ring_radius'],'phase_offset':0.,'manifold':True})
ports=[]
for port in paths['ports']:
 p=Vector(port['anchor']);axis=Vector(port['outward']);frame=bpy.data.objects[port['frame']]
 tool=P.cylinder('I90_SocketDrill',.0014,.006,group,p-axis*.0015,'I90_Nickel',axis,0);boolean(frame,tool)
 pin=P.cylinder(f'I90_FeedPin_{port["cell"]:02d}',.0011,.005,group,p-axis*.0003,'I90_Nickel',axis,.0001)
 housing=P.sleeve(f'I90_FeedCollar_{port["cell"]:02d}',.0027,.0013,.0026,group,p+axis*.0024,'I90_Nickel',axis)
 ports.append({**port,'pin':pin.name,'housing':housing.name})
caps=[];cap_bores_v=[];cap_bores_f=[];cap_occupied=[]
for j in (plate['caps']if manifolds else sorted(paths['junctions'],key=lambda x:(not x['root'],-x['clearance']))):
 if not j['root'] and j['clearance']<.015:continue
 p=Vector(j['p']);n=Vector(j['n']);radius=.008 if j['root']else .0045;shaft=.0026 if j['root']else .0016
 if any((p-other).length<radius+size+.008 for other,size in cap_occupied):continue
 cap_occupied.append((p,radius))
 head=P.screw(f'I90_JunctionCap_{j["node"]}',group,p+n*.010,radius,n)
 stem=P.cylinder('I90_CapStemTool',shaft,.013,group,p+n*.0025,'I90_Nickel',n,.0001);boolean(head,stem,'UNION')
 washer=P.sleeve(f'I90_JunctionSeal_{j["node"]}',radius*1.07,shaft+.00015,.0016,group,p+n*.0073,'A_Rubber',n)
 tool=P.cylinder('I90_JunctionBore',shaft+.0003,.016,group,p+n*.002,'I90_Nickel',n,0);bpy.context.view_layer.update();offset=len(cap_bores_v);cap_bores_v.extend(tool.matrix_world@v.co for v in tool.data.vertices);cap_bores_f.extend(tuple(offset+i for i in f.vertices)for f in tool.data.polygons);bpy.data.objects.remove(tool,do_unlink=True)
 caps.append({'node':j['node'],'cap':head.name,'seal':washer.name,'point':list(p),'normal':list(n),'root':j['root']})
for target in [backbone,liner]:boolean(target,mesh('I90_CombinedMountingBores',cap_bores_v,cap_bores_f,nickel),solver='MANIFOLD' if target==liner else 'EXACT')
clearance_finishing=[]
if version=='r5':
 from mathutils.bvhtree import BVHTree
 def bvh(ob):
  bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@p.co for p in me.vertices];f=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();return BVHTree.FromPolygons(v,f,all_triangles=True)
 def clearance_tool(ob,margin):
  ob.data.update();vertices=[ob.matrix_world@(v.co+v.normal*margin)for v in ob.data.vertices];faces=[tuple(f.vertices)for f in ob.data.polygons];return mesh('I90_OpticalClearanceTool',vertices,faces,nickel)
 for target in [backbone]+[bpy.data.objects[c['seal']]for c in caps]:
  for entry in segments:
   glass=bpy.data.objects[entry['mesh']];pairs=bvh(target).overlap(bvh(glass))
   if pairs:
    clearance_finishing.append({'target':target.name,'optical':glass.name,'original_triangle_pairs':len(pairs),'clearance':.00025})
    boolean(target,clearance_tool(glass,.00025),solver='MANIFOLD')
validation=[]
for ob in [backbone,liner]+[bpy.data.objects[n]for n in frames]+[o for o in group.children_recursive if o.type=='MESH'and o.name.startswith('I90_')and o!=backbone]:
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.index_update();groups={}
 for face in bm.faces:groups.setdefault(tuple(sorted(v.index for v in face.verts)),[]).append(face)
 duplicates=0
 for same in groups.values():
  if len(same)<2:continue
  edges={e for face in same for e in face.edges};external=any(any(f not in same for f in e.link_faces)for e in edges)
  remove=same[1:] if external else same;duplicates+=len(remove);bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY')
 for edge in list(bm.edges):
  if not edge.link_faces:bm.edges.remove(edge)
 for vertex in list(bm.verts):
  if not vertex.link_edges:bm.verts.remove(vertex)
 bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bm.to_mesh(ob.data);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True)
 if bad:print('R90_BAD_EDGES',ob.name,[{'length':e.calc_length(),'faces':[f.calc_area()for f in e.link_faces],'positions':[list(v.co)for v in e.verts]}for e in bm.edges if not e.is_manifold][:12],flush=True)
 bm.free();changed=ob.data.validate(verbose=True,clean_customdata=False);validation.append({'name':ob.name,'repairs':changed,'duplicate_faces_removed':duplicates,'nonmanifold':bad,'volume':vol})
assert all(not x['repairs']and x['nonmanifold']==0 and x['volume']>0 for x in validation),validation
if hasattr(backbone.data,'set_sharp_from_angle'):backbone.data.set_sharp_from_angle(angle=math.radians(35))
scene.frame_set(1);bpy.context.view_layer.update();changes=[name for name,value in protected.items()if fingerprint(bpy.data.objects[name])!=value];assert not changes,changes
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
for ob in root.children_recursive:
 if ob.type=='MESH' and ob.modifiers and not ob.data.shape_keys:
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());ob.modifiers.clear();ob.data=me
curves=[o for o in root.children_recursive if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_tangents=True,export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ART=R/'app/assets/collection/art/I/r90_network'
if version!='r1':ART=ART/version
ART.mkdir(parents=True,exist_ok=True)
layout=json.loads((R/'app'/old['chamber_response_layout'].removeprefix('res://')).read_text());layout['source_sha256']=sha(SRC);layout['component_sha256']=sha(COMP)
for port in ports:layout['cells'][port['cell']]['phase_offset']=port['distance']/paths['maximum_distance']-port['angle']/math.tau
layout['network']={'root':paths['root'],'maximum_distance':paths['maximum_distance'],'segments':segments,'clock_mode':'work','emission_gain':3.8,'light_color':[1.,.38,.065]}
(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':old['source'],'new_cells':layout['cells'],'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'network':{'group':group.name,'backbone':backbone.name,'segments':segments,'ports':ports,'caps':caps,'maximum_distance':paths['maximum_distance']},'network_topology':validation,'optical_clearance_finishing':clearance_finishing,'preserved_mesh_count':len(protected),'preserved_mesh_changes':changes,'scope':'Actual fitted milled backbone, distance-UV opal paths and frame sockets. Intentional bonded liner/backbone assembly. Final contacts, source-to-runtime motion/light checks and art review pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(205)
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100;cam=scene.camera;cam.location=(-4,-7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1;scene.render.filepath=str(OUT/'open.png');bpy.ops.render.render(write_still=True)
print('R90_NETWORK_BUILT',report['source_sha256'],len(segments),flush=True)
