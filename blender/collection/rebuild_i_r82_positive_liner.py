"""Replace a collapsed inner-coil liner with a strictly positive smooth wall.
Preserve exterior ceramic and mechanism. Reapply real guide and cartridge ports.
"""
import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];BASE=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
old=json.loads((BASE/'installed_r3/build.json').read_text());body=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())
OUT=BASE/'installed_r5';OUT.mkdir(exist_ok=True)
SRC=R/'blender/collection/I_r82_music_receiver_r4.blend';COMP=R/'app/assets/collection/components/I_r82_music_body_r5.glb';assert not SRC.exists()and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['R82_COIL_ROOT'];liner=bpy.data.objects['R82_Acoustic_Chamber_Liner']
for mod in list(liner.modifiers):liner.modifiers.remove(mod)
pars=body['shape_parameters'];T=pars['T'];END=pars['END'];GROW=pars['GROW'];RMAX=pars['RMAX'];RAD=pars['RAD'];DEPTH=pars['DEPTH'];SHIFT=Vector(pars['SHIFT'])
def sm_min(a,b,k):return min(a,b)-max(k-abs(a-b),0.)**2/(4*k)
def frame(t):
 r=RMAX*math.exp(GROW*(t-T));a=END+t-T;n=Vector((math.cos(a),0,math.sin(a)));u=max(0.,(t-(T-1.25))/1.25)
 tangent=Vector((r*(GROW*math.cos(a)-math.sin(a)),-.44*3*u*u/1.25,r*(GROW*math.sin(a)+math.cos(a)))).normalized()
 radial=(n-tangent*n.dot(tangent)).normalized()
 return r,radial,tangent,SHIFT+n*r+Vector((0,-.44*u**3,0))
def dimensions(t):
 r,_,_,_=frame(t);small=min(RAD,DEPTH)*r
 inset=sm_min(.042,small-.004,.003)
 thick=sm_min(.012,(small-inset)*.42,.001)
 assert small-inset-thick>0 and thick>0
 return inset,thick,small-inset-thick
NT=600;NU=96;vs=[];fs=[];mins=[]
for lay in [0,1]:
 for i in range(NT+1):
  t=.01+(T-.01)*i/NT;r,n,a,c=frame(t);inset,thick,residual=dimensions(t);mins.append((thick,residual))
  dep=inset+lay*thick;cross=n.cross(a).normalized()
  for j in range(NU+1):
   u=.06+(math.pi-.12)*j/NU;vs.append(c+n*((RAD*r-dep)*math.cos(u))+cross*((DEPTH*r-dep)*math.sin(u)))
S=NU+1;COUNT=(NT+1)*S
for layer in [0,1]:
 for i in range(NT):
  for j in range(NU):
   k=layer*COUNT+i*S+j;q=(k,k+S,k+S+1,k+1);fs.append(q if layer==0 else q[::-1])
edge=list(range(S))+[i*S+NU for i in range(1,NT+1)]+[NT*S+j for j in range(NU-1,-1,-1)]+[i*S for i in range(NT-1,0,-1)]
for i,a in enumerate(edge):
 b=edge[(i+1)%len(edge)];fs.append((a,b,b+COUNT,a+COUNT))
me=bpy.data.meshes.new('R83_Positive_InnerLiner');me.from_pydata(vs,[],fs);me.update()
for ma in liner.data.materials:me.materials.append(ma)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for p in me.polygons:p.use_smooth=True
assert not me.validate(verbose=True)
liner.data=me
def cylinder(radius,depth,pos,axis):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=radius,depth=depth);o=bpy.context.object;o.location=pos;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');return o
def cut(tool):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=liner
 mod=liner.modifiers.new('Actual receiving opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
me.calc_loop_triangles();tree=BVHTree.FromPolygons([liner.matrix_world@v.co for v in me.vertices],[tuple(t.vertices)for t in me.loop_triangles],all_triangles=True)
ports=[]
for p in body['joints']:
 P=Vector(p['pivot']);A=Vector(p['axis']);D=Vector(p['slide_direction']);length=p['guide_length']
 for side in [-1,1]:
  tip=P+A*p['crosshead_span']*side;start=tip-D*(length+.05);span=length+p['stroke']+.1
  if tree.ray_cast(start,D,span)[0]is None:continue
  cut(cylinder(p['rod_radius']*2.25+.002,span,start+D*span/2,D));ports.append((p['id'],side))
# Existing receiving envelope in the real cartridge coordinate system.
rows=[(-.16,.851),(-.09,.851),(.20,.873),(.24,.880),(.43,.858),(.48,.62),(.62,.50)]
verts=[];faces=[];N=192
for z,r in rows:
 for j in range(N):a=math.tau*j/N;verts.append((r*math.cos(a),r*math.sin(a),z))
for i in range(len(rows)-1):
 for j in range(N):faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
faces +=[tuple(range(N-1,-1,-1)),tuple((len(rows)-1)*N+j for j in range(N))]
toolme=bpy.data.meshes.new('ReceiverClearance');toolme.from_pydata(verts,[],faces);toolme.update()
tool=bpy.data.objects.new('ReceiverClearance',toolme);scene.collection.objects.link(tool);tool.matrix_world=bpy.data.objects['IAM_Mouth'].matrix_world.copy();cut(tool)
# Inspect validity explicitly before export, rather than allowing hidden exporter repairs.
repaired=liner.data.validate(verbose=True,clean_customdata=False)
assert not repaired,'Receiver cutting generated invalid topology; do not export it as a valid candidate.'
bm=bmesh.new();bm.from_mesh(liner.data)
topology={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'volume':bm.calc_volume(signed=True)}
bm.free();assert topology['nonmanifold_edges']==0 and topology['zero_area_faces']==0 and topology['volume']>0,topology
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
receipts=[]
for o in root.children_recursive:
 if o.type not in ['MESH','CURVE']:continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();n=len(mesh.vertices);ids=sorted(set([0,n-1]+[int((n-1)*k/7)for k in range(8)]))
 if o.type=='MESH' and n>len(o.data.vertices):ids=sorted(set(ids+[len(o.data.vertices),n-2]))
 receipts.append({'name':o.name,'kind':o.type,'raw_vertices':len(o.data.vertices)if o.type=='MESH'else None,'evaluated_vertices':n,'evaluated_triangles':len(mesh.loop_triangles),'modifiers':[m.type for m in o.modifiers if m.show_render],'local_samples_blender':[list(mesh.vertices[i].co)for i in ids]});ev.to_mesh_clear()
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=True,export_extras=True,export_tangents=True)
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'component':COMP.relative_to(R).as_posix(),'component_sha256':hashlib.sha256(COMP.read_bytes()).hexdigest(),'parent_source':old['source'],'parent_component':old['component'],'liner_rebuild':{'minimum_wall':min(a for a,b in mins),'minimum_inner_radius':min(b for a,b in mins),'topology':topology,'guide_ports':ports,'global_bevel_removed':True},'export_settings':{'apply_static_modifiers':True,'export_morph':False,'export_animations':False,'export_tangents':True},'scope':'Positive-thickness inner liner replaces collapsed constant-inset sheets; exact guide and receiver holes retained. Static evaluated upper body export. Full assembly and renderer checks remain scoped separately.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'evaluated_geometry.json').write_text(json.dumps({'source':report['source'],'source_sha256':report['source_sha256'],'objects':receipts,'scope':'Independent evaluated body triangle counts and sampled local coordinates including modifier-added vertices.'},indent=2)+'\n')
print('R83_POSITIVE_LINER_READY',topology,report['source_sha256'],flush=True)
