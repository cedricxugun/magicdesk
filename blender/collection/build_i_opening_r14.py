"""R13-derived opening layout study. Original form preserved at rest; not finished hardware."""
import bpy,bmesh,math,json,hashlib,sys,ast
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder,C,pose,smooth,reparent_preserving_world
SOURCE=ROOT/'blender/collection/I_conch_r13.blend';TARGET=ROOT/'blender/collection/I_opening_r14.blend';OUT=ROOT/'review/I_refinement/opening_r14';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=json.loads((ROOT/'review/I_refinement/conch_r13/build.json').read_text());assert sha(SOURCE)==prior['source_sha256']
if TARGET.exists():
 old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded opening source edits'
 backup=TARGET.parent/'checkpoints'/('I-opening-'+sha(TARGET)[:12]+'.blend');backup.write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['IC11_MODULE'];upper=bpy.data.objects['IC11_UPPER'];body=bpy.data.objects['IC11_ConchBody'];mouth=bpy.data.objects['IH1_Mouth']
recipe=ast.parse((ROOT/'blender/collection/build_i_conch_r13.py').read_text());names={'radius','center','band_limits','band_theta','band_surface'};namespace={'math':math,'Vector':Vector}
exec(compile(ast.Module(body=[n for n in recipe.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<shape-functions>','exec'),namespace)
center=namespace['center'];radius=namespace['radius'];surface=namespace['band_surface'];theta_at=namespace['band_theta']
b=Builder.__new__(Builder);b.id='IO14';b.serial=0;b.root=root;b.upper=body;b.col=bpy.data.collections.new('I_OPENING_LAYOUT_R14');scene.collection.children.link(b.col);b.mats={}
for key in ['ConchPorcelain','ConchNickel','ConchDarkMetal','ConchBrass','ConchRed']:b.mats[key]=bpy.data.materials['Collection_'+key]
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats};exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
original_world={o.name:o.matrix_world.copy() for o in root.children_recursive}
def reparent(o,parent):
 return reparent_preserving_world(o,parent)
def apply(o):
 if o.type!='MESH':return
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
# Repair over-thick inherited rolled edges: two 0.008-radius beads overlapped a ~0.008 seam.
# Keep original surface centerlines and names, trim with the same actual throat cutter.
trim_changes=[]
bpy.ops.mesh.primitive_cone_add(vertices=192,radius1=.797,radius2=.567,depth=1.50)
trim_tool=bpy.context.object;trim_tool.parent=mouth;trim_tool.location=(0,0,.10);trim_tool.rotation_euler=(0,0,0);bpy.context.view_layer.update()
for index,row in enumerate(prior['shells']):
 plate=bpy.data.objects[row['node']]
 edges=sorted([o for o in plate.children if o.name.startswith('IC11_HelicalNickelEdge')],key=lambda o:o.name)
 assert len(edges)==2
 for u,old_edge in zip([0.,1.],edges):
  edge=b.tube('RebuiltRolledEdge',[surface(index,u,theta_at(index,k/192)) for k in range(193)],.003,'ConchNickel',plate)
  bpy.ops.object.select_all(action='DESELECT');edge.select_set(True);bpy.context.view_layer.objects.active=edge;edge.data.use_fill_caps=True;bpy.ops.object.convert(target='MESH');bpy.context.view_layer.update()
  mod=edge.modifiers.new('Preserved throat opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=trim_tool;mod.solver='EXACT';bpy.ops.object.modifier_apply(modifier=mod.name);apply(edge)
  old_edge.data=edge.data;trim_changes.append(old_edge.name);bpy.data.objects.remove(edge,do_unlink=True)
bpy.data.objects.remove(trim_tool,do_unlink=True)
# Each helical plate retains its own rear-edge chord, rather than opening a complete half-cage.
rig=[];joints=[]
for i,row in enumerate(prior['shells']):
 plate=bpy.data.objects[row['node']];p0=surface(i,.50,theta_at(i,.025),True);p1=surface(i,.50,theta_at(i,.975),True)
 axis=(p1-p0).normalized();pivot=b.empty('IO14_RearHinge'+str(i),body,(p0+p1)*.5);pivot.rotation_mode='QUATERNION';pivot.rotation_quaternion=axis.to_track_quat('Z','Y');bpy.context.view_layer.update();reparent(plate,pivot)
 # Moderate first pose: enough to judge peeling and contact; not an accepted final angle.
 angle=[.12,.19,.23,.25,.22,.16][i]
 rig.append({'name':pivot.name,'kind':'shell','home_matrix':[list(r) for r in pivot.matrix_local],'angle':angle,'order':i,'plate':plate.name,'axis_body':list(axis),'p0':list(p0),'p1':list(p1)})
 for endpoint,p in enumerate([p0,p1]):
  # These are bearing-envelope volumes for layout; detailed forks/pins are intentionally not claimed.
  sphere=b.sphere('BearingEnvelope',.027,'ConchBrass',body,p);sphere['layout_only']=True;joints.append(sphere.name)
  q=(p.z-1.16)/2.26;q=max(.03,min(.97,q));anchor=center(q)+Vector((0,radius(q)*.46,0))
  b.beam('RearHingeSupport',anchor,p,.016,'ConchNickel',body)
# Move the apex with its own outer plate; its rest coordinates stay unchanged.
reparent(bpy.data.objects['IC11_Apex'],bpy.data.objects[prior['shells'][-1]['node']])
# Divide the existing porcelain lip into an upper hood and retained lower collar.
old_lip=next(o for o in body.children_recursive if o.name.startswith('IC11_RolledThroatPorcelain'))
profile=next(ast.literal_eval(n.args[1]) for n in ast.walk(recipe) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='lathe' and isinstance(n.args[0],ast.Constant) and n.args[0].value=='RolledThroatPorcelain')
hood=b.empty('IO14_UpperHoodHinge',mouth,(0,.70,.55));bpy.context.view_layer.update();lip_parts=[]
for label,start,end,parent in [('Upper',9,87,hood),('Lower',87,201,mouth)]:
 count=end-start;n=count+1;verts=[];faces=[];uv=[]
 for r,z in profile:
  for k in range(n):
   a=(start+k)*math.tau/192+( .001 if k==0 else -.001 if k==count else 0.)
   verts.append((r*math.cos(a),r*math.sin(a),z));uv.append(((start+k)/192,z))
 for j in range(len(profile)):
  for k in range(count):faces.append((j*n+k,j*n+k+1,((j+1)%len(profile))*n+k+1,((j+1)%len(profile))*n+k))
 faces.extend([tuple(j*n for j in range(len(profile))),tuple(j*n+count for j in range(len(profile)-1,-1,-1))])
 part=b.fast['fast_instance']('IC11_RolledThroatPorcelain_'+label,verts,faces,'ConchPorcelain',mouth,(0,0,0),smooth_faces=True,uv=uv);apply(part)
 if label=='Upper':reparent(part,hood)
 bpy.context.view_layer.update()
 assert max(abs(part.matrix_world[r][c]-mouth.matrix_world[r][c]) for r in range(4) for c in range(4))<1e-6,'New lip segment lost its rest frame'
 lip_parts.append(part.name)
bpy.data.objects.remove(old_lip,do_unlink=True)
rig.append({'name':hood.name,'kind':'hood','home_matrix':[list(r) for r in hood.matrix_local],'angle':.38,'order':-1,'axis_local':[1,0,0]})
# Continuous inner volume and annular resonator rings are anatomy envelopes, not final detailed art.
core=b.empty('IO14_AcousticCore',body)
for rail_x in [-.07,.07]:
 pts=[center(.045+.91*j/128)+Vector((rail_x,radius(.045+.91*j/128)*.46,0)) for j in range(129)]
 b.tube('ContinuousRearSpine',pts,.025,'ConchNickel',core)
 b.beam('SpineFoot',(.03,.22,1.10),pts[0],.035,'ConchNickel',core)
for band in range(18):
 q=.10+.84*band/17;rr=radius(q)*.58;zhalf=.018;outer=[];faces=[];n=96
 for r,z in [(rr,-zhalf),(rr,zhalf),(max(.018,rr-.026),zhalf),(max(.018,rr-.026),-zhalf)]:
  for k in range(n):a=k*math.tau/n;outer.append(center(q)+Vector((r*math.cos(a),r*.8*math.sin(a),z)))
 for j in range(4):
  for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,((j+1)%4)*n+(k+1)%n,((j+1)%4)*n+k))
 o=b.fast['fast_instance'](b.name('AnnularResonatorEnvelope'),outer,faces,'ConchDarkMetal' if band%2 else 'ConchNickel',core,(0,0,0),smooth_faces=True);o['layout_only']=True;apply(o)
# A continuous hollow acoustic wall supplies the mass between resonator rings.
verts=[];faces=[];nq=96;na=96
for inner in [False,True]:
 for j in range(nq+1):
  q=.09+.87*j/nq;rr=radius(q)*.53-(min(.014,radius(q)*.12) if inner else 0.)
  for k in range(na):
   a=k*math.tau/na;verts.append(center(q)+Vector((rr*math.cos(a),rr*.8*math.sin(a),0)))
size=(nq+1)*na
for layer in [0,1]:
 for j in range(nq):
  for k in range(na):
   a=layer*size+j*na+k;c=layer*size+j*na+(k+1)%na;f=(a,c,c+na,a+na);faces.append(f if layer==0 else f[::-1])
for j in [0,nq]:
 for k in range(na):a=j*na+k;c=j*na+(k+1)%na;faces.append((a,c,c+size,a+size))
wall=b.fast['fast_instance'](b.name('ContinuousAcousticWallEnvelope'),verts,faces,'ConchDarkMetal',core,(0,0,0),smooth_faces=True);wall['layout_only']=True;apply(wall)
profile2=[(.61,.18),(.58,.32),(.46,.58),(.40,.75),(.38,.75),(.43,.58),(.55,.32),(.59,.18)];verts=[];faces=[];n=96
for r,z in profile2:
 for k in range(n):a=k*math.tau/n;verts.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(profile2)):
 for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,((j+1)%len(profile2))*n+(k+1)%n,((j+1)%len(profile2))*n+k))
neck=b.fast['fast_instance'](b.name('AcousticThroatConnectorEnvelope'),verts,faces,'ConchDarkMetal',mouth,(0,0,0),smooth_faces=True);neck['layout_only']=True;apply(neck)
# Fixed throat support closes the load path to the existing cradle; detailed seats remain.
for x in [-.24,.24]:
 end=(body.matrix_world.inverted()@mouth.matrix_world)@Vector((x,-.45,.18));b.beam('ThroatSupport',(.03+x,.22,1.10),end,.027,'ConchNickel',core)
# Preserve every surviving original object's rest transform before authoring the new motion.
bpy.context.view_layer.update();drift={}
for name,world in original_world.items():
 o=bpy.data.objects.get(name)
 if o:
  error=max(abs(o.matrix_world[r][c]-world[r][c]) for r in range(4) for c in range(4))
  if error>1e-6:drift[name]=error
assert not drift,drift
for o in root.children_recursive:o.animation_data_clear()
scene.render.fps=30;scene.frame_start=1;scene.frame_end=361;poses={}
for frame in range(1,362):
 seconds=(frame-1)/30
 opening=smooth((seconds-.5)/3.) if seconds<6 else 1.-smooth((seconds-7.)/3.)
 for row in rig:
  o=bpy.data.objects[row['name']];home=Matrix(row['home_matrix']);amount=smooth((opening-max(0,row['order'])*.065)/.675) if row['kind']=='shell' else smooth(opening/.40)
  axis=Vector((0,0,1)) if row['kind']=='shell' else Vector((1,0,0))
  o.matrix_basis=home@Quaternion(axis,row['angle']*amount).to_matrix().to_4x4();o.rotation_mode='QUATERNION';o.keyframe_insert('rotation_quaternion',frame=frame);o.keyframe_insert('location',frame=frame)
 iris=smooth(seconds/.5) if seconds<7 else 1.-smooth((seconds-10.)/.5)
 for row in prior['leaves']:
  o=bpy.data.objects[row['name']];o.rotation_euler.z=row['home']-row['travel']*iris;o.keyframe_insert('rotation_euler',frame=frame)
 if frame in [1,31,61,91,121,181,241,301,361]:
  bpy.context.view_layer.update();poses[str(frame)]={row['name']:pose(bpy.data.objects[row['name']].matrix_world) for row in rig}
for o in b.col.objects:apply(o)
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));bpy.ops.object.select_all(action='DESELECT')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_opening_r14.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_extras=True)
runtime=[]
for row in rig:
 m=C@Matrix(row['home_matrix'])@C.inverted();item={k:v for k,v in row.items() if k!='home_matrix'};item['home']=pose(Matrix(row['home_matrix']));runtime.append(item)
(ROOT/'app/assets/collection/i_opening_rig_r14.json').write_text(json.dumps({'rig':runtime,'leaves':prior['leaves']},indent=2)+'\n')
(OUT/'source_poses.json').write_text(json.dumps(poses,indent=2)+'\n')
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'input_source_sha256':sha(SOURCE),'shells':prior['shells'],'leaves':prior['leaves'],'rig':rig,'lip_parts':lip_parts,'layout_bearings':joints,'rest_original_transform_drift':drift,'rest_geometry_changes':{'split_lip':lip_parts,'rolled_edge_radius':.003,'rebuilt_edges':trim_changes},'scope':'Original-form-derived rotational opening LAYOUT. Core/hinges are anatomy envelopes; no complete mechanical hardware, collision, art/native/music acceptance.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_OPENING_R14_BUILT',flush=True)
