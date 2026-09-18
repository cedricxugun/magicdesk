"""Guided release + peeling study, preserving R14 source and its failure evidence."""
import bpy,bmesh,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder,C,pose,smooth,reparent_preserving_world
BASE=ROOT/'review/I_refinement/opening_r14';prior=json.loads((BASE/'build.json').read_text());SOURCE=ROOT/prior['source'];TARGET=ROOT/'blender/collection/I_opening_r15.blend';OUT=ROOT/'review/I_refinement/opening_r15';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SOURCE)==prior['source_sha256']
options=json.loads((BASE/'release_options_fine.json').read_text());assert options['source_sha256']==sha(SOURCE);step=min(r['release_step'] for r in options['options'] if r['contact_samples']==0)
if TARGET.exists():
 old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded R15 edits';(TARGET.parent/'checkpoints'/('I-release-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IC11_MODULE'];body=bpy.data.objects['IC11_ConchBody'];mouth=bpy.data.objects['IH1_Mouth']
for o in root.children_recursive:o.animation_data_clear()
b=Builder.__new__(Builder);b.id='IO15';b.serial=0;b.root=root;b.upper=body;b.col=bpy.data.collections.new('I_GUIDED_RELEASE_R15');scene.collection.children.link(b.col);b.mats={k:bpy.data.materials['Collection_'+k] for k in ['ConchPorcelain','ConchNickel','ConchDarkMetal','ConchBrass','ConchRed']}
b.material('DiaphragmRubber',(.012,.017,.014),0,.55)
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats};exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
rig=[];releases=[];supports=[]
beam_objects=sorted([o for o in root.children_recursive if 'RearHingeSupport' in o.name],key=lambda o:o.name);assert len(beam_objects)==12
for i,row in enumerate(prior['rig'][:6]):
 node=bpy.data.objects[row['name']];carrier=b.empty('IO15_Release'+str(i),body);bpy.context.view_layer.update();reparent_preserving_world(node,carrier)
 release={'name':carrier.name,'kind':'release','home_matrix':[list(x) for x in carrier.matrix_local],'offset':[0,0,i*step],'order':i};releases.append(release)
 for j in range(2):
  ball=bpy.data.objects[prior['layout_bearings'][i*2+j]];reparent_preserving_world(ball,carrier)
  beam=beam_objects[i*2+j];mesh=beam.data;zmin=min(v.co.z for v in mesh.vertices);zmax=max(v.co.z for v in mesh.vertices)
  end=beam.matrix_local@Vector((0,0,zmax));anchor=beam.matrix_local@Vector((0,0,zmin));expected=Vector(row['p0' if j==0 else 'p1']);assert (end-expected).length<1e-5
  beam['layout_only']=True;beam['purpose']='Telescopic actuator space envelope; not a stretching production rod'
  supports.append({'name':beam.name,'kind':'support_envelope','anchor':list(anchor),'end':list(end),'length':zmax-zmin,'home_direction':list((end-anchor).normalized()),'home_rotation':[list(r) for r in beam.matrix_local.to_3x3().normalized()],'lift':i*step,'release_offset':[0,0,i*step],'order':i})
 new=dict(row);new['home_matrix']=[list(x) for x in node.matrix_local];rig.append(new)
# Only the front hood moves. The deep throat transition becomes a fixed receiver.
hood=bpy.data.objects['IO14_UpperHoodHinge'];front=bpy.data.objects['IC11_RolledThroatPorcelain_Upper'];reparent_preserving_world(front,mouth)
rear=bpy.data.objects.new('IO15_FixedUpperNeck',front.data.copy());b.col.objects.link(rear);rear.parent=mouth;rear.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
def clip_depth(obj,z,keep_front):
 if obj.data.users>1:obj.data=obj.data.copy()
 bm=bmesh.new();bm.from_mesh(obj.data)
 result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector((0,0,z)),plane_no=Vector((0,0,1)),dist=1e-7,clear_outer=keep_front,clear_inner=not keep_front)
 edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
clip_depth(front,.0145,True);clip_depth(rear,.0155,False)
hood.location=(0,.25,.015);hood.rotation_mode='QUATERNION';hood.rotation_quaternion=Quaternion();bpy.context.view_layer.update();reparent_preserving_world(front,hood)
hood_carrier=b.empty('IO15_HoodRelease',mouth);bpy.context.view_layer.update();reparent_preserving_world(hood,hood_carrier)
releases.append({'name':hood_carrier.name,'kind':'release','home_matrix':[list(x) for x in hood_carrier.matrix_local],'offset':[0,.12,-.16],'order':-1})
rig.append({'name':hood.name,'kind':'hood','home_matrix':[list(x) for x in hood.matrix_local],'angle':.30,'order':-1,'axis_local':[1,0,0]})
# The upper hood has explicit support envelopes, not an invisible pivot in empty space.
hood_envelopes=[]
for sign in [-1,1]:
 anchor=Vector((sign*.60,.45,.22));end=Vector((sign*.82,.25,.015))
 base_joint=b.sphere('HoodAnchorEnvelope',.022,'ConchBrass',mouth,anchor);base_joint['layout_only']=True;hood_envelopes.append(base_joint.name)
 end_joint=b.sphere('HoodBearingEnvelope',.018,'ConchBrass',mouth,end);end_joint['layout_only']=True;reparent_preserving_world(end_joint,hood_carrier);hood_envelopes.append(end_joint.name)
 beam=b.beam('HoodSupportEnvelope',anchor,end,.014,'ConchNickel',mouth);beam['layout_only']=True;hood_envelopes.append(beam.name);bpy.context.view_layer.update()
 length=max(v.co.z for v in beam.data.vertices)-min(v.co.z for v in beam.data.vertices)
 supports.append({'name':beam.name,'kind':'support_envelope','anchor':list(anchor),'end':list(end),'length':length,'home_direction':list((end-anchor).normalized()),'home_rotation':[list(r) for r in beam.matrix_local.to_3x3().normalized()],'lift':0.,'release_offset':[0,.12,-.16],'order':-1,'parent_frame':'mouth'})
# Accurate receiver space follows the actual outer lip, rather than the former approximate cone.
def lathe(name,profile,key,parent,n=128):
 v=[(r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),z) for r,z in profile for k in range(n)];f=[(j*n+k,j*n+(k+1)%n,((j+1)%len(profile))*n+(k+1)%n,((j+1)%len(profile))*n+k) for j in range(len(profile)) for k in range(n)]
 o=b.fast['fast_instance'](b.name(name),v,f,key,parent,(0,0,0),smooth_faces=True)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();return o
profile=[(0,-.45),(.811,-.45),(.811,-.178),(.861,-.157),(.894,-.105),(.902,-.035),(.874,.045),(.797,.200),(.694,.520),(.604,.850),(.604,.865),(0,.865)]
cut=lathe('ReceiverClearanceTool',profile,'ConchDarkMetal',mouth);bpy.context.view_layer.update();recut=[]
for row in prior['shells']:
 plate=bpy.data.objects[row['node']]
 for obj in list(plate.children):
  if obj.type=='MESH' and ('PorcelainHelix' in obj.name or 'HelicalNickelEdge' in obj.name):
   obj.data=obj.data.copy();bpy.context.view_layer.objects.active=obj;mod=obj.modifiers.new('Measured throat receiving face','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);recut.append(obj.name)
bpy.data.objects.remove(cut,do_unlink=True)
# Give the fixed inner metal lip a receiving groove instead of intersecting the moving porcelain.
small=[(.754,-.129),(.762,-.138),(.774,-.138),(.779,-.127),(.772,-.119),(.758,-.118)]
metal=next(o for o in mouth.children if o.name.startswith('IC11_ThinMouthMachinedLip'))
assert max(min(abs(math.hypot(v.co.x,v.co.y)-r)+abs(v.co.z-z) for r,z in small) for v in metal.data.vertices)<1e-5
r_mid=(min(r for r,z in small)+max(r for r,z in small))*.5;z_mid=(min(z for r,z in small)+max(z for r,z in small))*.5
seat_profile=[(r_mid+(r-r_mid)*1.16,z_mid+(z-z_mid)*1.20) for r,z in small]
seat_tool=lathe('FixedMetalLipSeatTool',seat_profile,'ConchDarkMetal',mouth);bpy.context.view_layer.update()
# A single convex swept cutter avoids slivers from many overlapping Boolean cuts.
# Its depth stays in the front lip (-0.142..-0.085); it does not thin the iris storage wall.
bm=bmesh.new()
for fraction in [0.,.18]:
 shift=Vector((0,-.12*fraction,.16*fraction))
 for v in seat_tool.data.vertices:bm.verts.new(v.co+shift)
bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
unused=[v for v in bm.verts if not v.link_faces]
if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));data=bpy.data.meshes.new('IO15_ContinuousUnseatingRelief');bm.to_mesh(data);bm.free()
sweep=bpy.data.objects.new('IO15_UnseatingSweepTool',data);b.col.objects.link(sweep);sweep.parent=mouth;sweep.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
for name in ['IC11_RolledThroatPorcelain_Upper','IC11_RolledThroatPorcelain_Lower']:
 obj=bpy.data.objects[name];obj.data=obj.data.copy();bpy.context.view_layer.objects.active=obj
 mod=obj.modifiers.new('Guided metal-lip disengagement relief','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=sweep if name.endswith('Upper') else seat_tool;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(sweep,do_unlink=True);bpy.data.objects.remove(seat_tool,do_unlink=True)
# Connect the forward hub to a seated diaphragm; preserve the visible original hub and forks.
stem=b.cyl('ContinuousHubShaft',.030,.377,'ConchNickel',mouth,(0,0,.1015),None,64)
b.sphere('DiaphragmEnvelope',.35,'ConchDarkMetal',mouth,(0,0,.30),scale=(1,1,.10))
b.torus('DiaphragmSurround',.35,.012,'DiaphragmRubber',mouth,(0,0,.30))
b.sleeve('DiaphragmSeat',.38,.35,.026,'ConchNickel',mouth,(0,0,.30),96)
for i in range(3):
 a=i*math.tau/3;b.beam('DiaphragmFrameSpoke',(.376*math.cos(a),.376*math.sin(a),.31),(.553*math.cos(a),.553*math.sin(a),.35),.012,'ConchNickel',mouth)
# Envelopes keep their endpoints connected; final nested cylinders are a separate hardware task.
def support_basis(direction):
 z=direction.normalized();ref=Vector((0,0,1)) if abs(z.z)<.95 else Vector((0,1,0));x=ref.cross(z).normalized();y=z.cross(x);return Matrix((x,y,z)).transposed()
scene.frame_start=1;scene.frame_end=361;scene.render.fps=30;poses={}
for frame in range(1,362):
 seconds=(frame-1)/30;opening=smooth((seconds-.5)/3.) if seconds<6 else 1.-smooth((seconds-7.)/3.);release=smooth(opening/.30)
 for row in releases:
  o=bpy.data.objects[row['name']];o.matrix_basis=Matrix(row['home_matrix']);o.location+=Vector(row['offset'])*release;o.keyframe_insert('location',frame=frame)
 for row in rig:
  o=bpy.data.objects[row['name']];amount=smooth((opening-.30-max(0,row['order'])*.05)/.45) if row['kind']=='shell' else smooth((opening-.30)/.50);axis=Vector((0,0,1)) if row['kind']=='shell' else Vector((1,0,0));o.matrix_basis=Matrix(row['home_matrix'])@Quaternion(axis,row['angle']*amount).to_matrix().to_4x4();o.rotation_mode='QUATERNION';o.keyframe_insert('rotation_quaternion',frame=frame);o.keyframe_insert('location',frame=frame)
 for row in supports:
  o=bpy.data.objects[row['name']];a=Vector(row['anchor']);end=Vector(row['end'])+Vector(row['release_offset'])*release;direction=end-a;o.location=(a+end)*.5;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(row['home_direction']).rotation_difference(direction.normalized())@Matrix(row['home_rotation']).to_quaternion();o.scale=(1,1,direction.length/row['length'])
  for key in ['location','rotation_quaternion','scale']:o.keyframe_insert(key,frame=frame)
 iris=smooth(seconds/.5) if seconds<7 else 1.-smooth((seconds-10.)/.5)
 for row in prior['leaves']:
  o=bpy.data.objects[row['name']];o.rotation_euler.z=row['home']-row['travel']*iris;o.keyframe_insert('rotation_euler',frame=frame)
 if frame in [1,31,61,91,121,181,241,301,361]:
  bpy.context.view_layer.update();poses[str(frame)]={row['name']:pose(bpy.data.objects[row['name']].matrix_world) for row in releases+rig+supports}
scene.frame_set(1);bpy.context.view_layer.update()
for obj in list(b.col.objects):
 if obj.type=='MESH':
  bpy.context.view_layer.objects.active=obj
  for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));bpy.ops.object.select_all(action='DESELECT')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_opening_r15.glb';bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_extras=True)
runtime=[]
for row in releases+rig+supports:
 item={k:v for k,v in row.items() if k!='home_matrix'}
 if 'home_matrix' in row:item['home']=pose(Matrix(row['home_matrix']))
 for k in ['offset','anchor','end','home_direction','release_offset']:
  if k in item:item[k]=list(C.to_3x3()@Vector(item[k]))
 runtime.append(item)
(ROOT/'app/assets/collection/i_opening_rig_r15.json').write_text(json.dumps({'rig':runtime,'leaves':prior['leaves']},indent=2)+'\n');(OUT/'source_poses.json').write_text(json.dumps(poses,indent=2)+'\n')
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'input_source_sha256':sha(SOURCE),'shells':prior['shells'],'leaves':prior['leaves'],'rig':rig,'release_rig':releases,'support_envelopes':supports,'hood_hardware_envelopes':hood_envelopes,'release_step':step,'receiver_recut':recut,'fixed_upper_neck':rear.name,'hub_shaft':stem.name,'scope':'Guided-release + peeling layout, front hood separated from fixed receiver, actual hub shaft/diaphragm volume. Envelope supports are not production telescopes; full clearance, art/native/music acceptance remain.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_OPENING_R15_BUILT',step,flush=True)
