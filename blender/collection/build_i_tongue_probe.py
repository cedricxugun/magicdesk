"""One retained tongue / actual morph mesh and driven spool, isolated from the main App."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_tongue_path import TonguePath
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/tongue_probe';OUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((OUT.parent/'build.json').read_text());src=ROOT/seed['source'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));target=ROOT/'blender/collection/I_tongue_probe.blend'
if target.exists():
 prev=json.loads((OUT/'build.json').read_text());assert sha(target)==prev['source_sha256'],'Unrecorded tongue edits'
 (target.parent/'checkpoints'/('I-tongue-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
mouth=bpy.data.objects['IAM_Mouth'];col=bpy.data.collections['MODULE_IAM'];scene=bpy.context.scene
for o in list(bpy.data.objects):
 if o.name.startswith('IAM_Eyelid_0_') or o.name.startswith('IAM_EyelidRoot_0_') or o.name in ['IAM_EyelidStackSeat_0','IAM_EyelidStackSeat_1','IAM_EyelidCaptiveHead_0','IAM_EyelidCaptiveHead_1']:bpy.data.objects.remove(o,do_unlink=True)
def empty(name,parent=mouth):
 o=bpy.data.objects.new(name,None);col.objects.link(o);o.parent=parent;return o
drive=empty('IAM_TongueDrive0');drive['feed']=0.;path=TonguePath(0,rows=360,columns=16);faces=path.topology();keys=256
def box(name,dimensions,parent,loc,material='A_Nickel',basis=None):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.scale=dimensions;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent
 if basis is not None:o.matrix_basis=basis
 o.location=loc;o.data.materials.append(bpy.data.materials['Collection_'+material]);return o
# A real machined passage through the rear carrier and liner, not hidden intersecting material.
slot_basis=Matrix((Vector(path.roll_side),Vector(path.outward),Vector(path.back))).transposed().to_4x4()
slot_u=(.220-path.turn_end[2]-path.entry_radius)/path.straight_z;slot_center=Vector(path.guide(np.array([slot_u]))[0])
tool=box('IAM_TongueGuideSlotTool',(.337,.020,.200),mouth,slot_center,'A_Dark',slot_basis)
for name in ['IAM_EyelidFixedCarrier']:
 o=bpy.data.objects[name]
 if o.data.users>1:o.data=o.data.copy()
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Retained guide passage','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(tool,do_unlink=True)
meshes=[];states=[]
reverse_material=bpy.data.materials['Collection_A_LeafNickel'].copy();reverse_material.name='Collection_A_LeafNickelReverse'
reverse_bsdf=next(n for n in reverse_material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');reverse_bsdf.inputs['Base Color'].default_value=(.30,.29,.265,1)
for skin in range(2):
 pos,state=path.vertices(0,skin);m=bpy.data.meshes.new('TongueFoilMesh');m.from_pydata(pos.tolist(),[],faces);m.update()
 o=bpy.data.objects.new('IAM_TongueFoil_'+str(skin),m);col.objects.link(o);o.parent=mouth;m.materials.append(bpy.data.materials['Collection_A_LeafNickel'] if skin==0 else reverse_material)
 for f in m.polygons:f.use_smooth=True
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 uv=m.uv_layers.new(name='ContinuousMaterialUV');data_uv=m.uv_layers.new(name='TongueRowData');stride=(path.rows+1)*(path.columns+1)
 for f in m.polygons:
  for li in f.loop_indices:
   vi=m.loops[li].vertex_index;idx=vi%stride;j=idx//(path.columns+1);k=idx%(path.columns+1);uv.data[li].uv=(float(path.material_s[j]/path.length)*3,k/path.columns*.45);data_uv.data[li].uv=((j+.5)/(path.rows+1),k/path.columns+2*(vi//stride))
 o.shape_key_add(name='Basis')
 for k in range(1,keys+1):
  positions,st=path.vertices(k/keys,skin);key=o.shape_key_add(name='feed_%02d'%k);key.data.foreach_set('co',positions.astype(np.float32).ravel());key.value=0.
  driver=key.driver_add('value').driver;driver.type='SCRIPTED';var=driver.variables.new();var.name='feed';var.type='SINGLE_PROP';var.targets[0].id=drive;var.targets[0].data_path='["feed"]';driver.expression='max(0,1-abs(feed*%d-%d))'%(keys,k)
 meshes.append(o.name)
 print('TONGUE_MORPHS',skin,flush=True)
def cylinder(name,r,length,material,parent,loc=(0,0,0),segments=64):
 bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=length)
 o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(bpy.data.materials['Collection_'+material])
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o
def revolved(name,profile,material='A_Nickel',segments=160):
 verts=[];faces=[];sm=[]
 for radius,z in profile:
  for j in range(segments):a=j*math.tau/segments;verts.append((radius*math.cos(a),radius*math.sin(a),z))
 for p in range(len(profile)):
  nxt=(p+1)%len(profile)
  for j in range(segments):faces.append((p*segments+j,p*segments+(j+1)%segments,nxt*segments+(j+1)%segments,nxt*segments+j));sm.append(abs(profile[p][1]-profile[nxt][1])>1e-7)
 m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(verts,[],faces);m.materials.append(bpy.data.materials['Collection_'+material]);o=bpy.data.objects.new(name,m);col.objects.link(o);o.parent=mouth
 for face,smooth in zip(m.polygons,sm):face.use_smooth=smooth
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
 loose=[e for e in bm.edges if not e.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();return o
# The original artwork has front sockets and axial prongs; the former radial side rods were wrong.
head_parent=next(o for o in bpy.data.objects if o.type=='MESH' and 'CentralResonatorCap' in o.name).parent
for o in list(bpy.data.objects):
 if o.type=='MESH' and any(word in o.name for word in ['CentralResonatorCap','HeadBronzeCollar','TineRoot','EnamelTine','TineRoundedTip']):bpy.data.objects.remove(o,do_unlink=True)
head=revolved('IAM_CentralResonatorCap_Axial',[(0,-.129),(.060,-.129),(.070,-.121),(.085,-.095),(.086,-.080),(.086,-.073),(.086,-.069),(.063,-.042),(.038,-.032),(.030,-.031),(.030,.415),(0,.415)])
head.parent=head_parent
head.data.materials.append(bpy.data.materials['Collection_A_Bronze'])
for face in head.data.polygons:
 if -.08001<face.center.z<-.07299:face.material_index=1
for i,y in enumerate([-.045,0.,.045]):
 for radius,length,z in [(.008,.055,-.118),(.0124,.006,-.129)]:
  tool=cylinder('AxialSocketDrill',radius,length,'A_Dark',head_parent,(0,y,z),64);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=head;mod=head.modifiers.new('Bored front socket','BOOLEAN');mod.operation='DIFFERENCE';mod.object=tool;mod.solver='EXACT';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
 socket=revolved('IAM_TineSocketAxial_'+str(i),[(.0069,-.145),(.011,-.145),(.012,-.140),(.012,-.127),(.0078,-.127),(.0078,-.111),(.0069,-.111)],'A_Bronze',64);socket.parent=head_parent;socket.location.y=y
 cylinder('IAM_TineStemAxial_'+str(i),.0065,.111,'A_Nickel',head_parent,(0,y,-.1845),48)
 cylinder('IAM_TineEnamelAxial_'+str(i),.009,.068,'A_Red',head_parent,(0,y,-.274),64)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.009);tip=bpy.context.object;tip.name='IAM_TineRoundedAxial_'+str(i)
 for collection in list(tip.users_collection):collection.objects.unlink(tip)
 col.objects.link(tip);tip.parent=head_parent;tip.location=(0,y,-.308);tip.data.materials.append(bpy.data.materials['Collection_A_Red'])
 for face in tip.data.polygons:face.use_smooth=True
revolved('IAM_HeadAcousticNeck',[(.034,-.031),(.043,-.025),(.043,.096),(.05,.126),(.067,.172),(.091,.230),(.095,.237),(.095,.252),(.081,.270),(.038,.283),(.033,.282),(.033,-.031)],'A_Dark')
# Exact booleans may leave coincident seam vertices at a counterbore on the lathe seam.
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
loose=[e for e in bm.edges if not e.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()
base=path.frames(0)[4];carriage=empty('IAM_TongueSpoolCarriage');carriage.location=base['axis']
spool=empty('IAM_TongueSpool',carriage);local_y=np.cross(path.roll_side,path.outward);spin_sign=float(np.dot(local_y,path.back));orientation=Matrix((Vector(path.outward),Vector(local_y),Vector(path.roll_side))).transposed().to_4x4();orient=empty('IAM_TongueSpoolOrientation',carriage);orient.matrix_basis=orientation;spool.parent=orient
cylinder('IAM_TongueSpoolCore',path.r0-.005,.338,'A_Dark',spool)
# Curved retaining saddle follows the first wrap; a flat cap touched the next wrap during interpolation.
jaw_profile=[(path.r0+.0009,-.010),(path.r0+.0013,-.010),(path.r0+.0013,.010),(path.r0+.0009,.010)];jaw_v=[];jaw_f=[];segments=24
for radius,z in jaw_profile:
 for j in range(segments+1):a=-.13+.26*j/segments;jaw_v.append((radius*math.cos(a),radius*math.sin(a),z))
for p in range(4):
 for j in range(segments):jaw_f.append((p*(segments+1)+j,p*(segments+1)+j+1,((p+1)%4)*(segments+1)+j+1,((p+1)%4)*(segments+1)+j))
jaw_f.extend([tuple(p*(segments+1) for p in range(3,-1,-1)),tuple(p*(segments+1)+segments for p in range(4))]);m=bpy.data.meshes.new('FormedRetainingSaddle');m.from_pydata(jaw_v,[],jaw_f);m.materials.append(bpy.data.materials['Collection_A_Nickel'])
jaw=bpy.data.objects.new('IAM_TongueLeaderOuterJaw',m);col.objects.link(jaw);jaw.parent=spool;bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
box('IAM_TongueLeaderInnerJaw',(.001,.008,.020),spool,(path.r0-.0054,0,0))
box('IAM_TongueLeaderJawBridge',(.0063,.001,.020),spool,(path.r0-.00225,.0045,0))
for z in [-.177,.177]:
 cylinder('IAM_TongueSpoolFlange',.076,.005,'A_Nickel',spool,(0,0,z),96)
 cylinder('IAM_TongueAxleEnd',.012,.025,'A_Bronze',orient,(0,0,z+(.015 if z>0 else -.015)),48)
guide=empty('IAM_TongueGuideRoller');guide.matrix_basis=orientation;guide.location=path.turn_end+path.back*path.entry_radius
cylinder('IAM_TongueGuideMandrel',path.entry_radius-.005,.335,'A_Nickel',guide)
for z in [-.175,.175]:cylinder('IAM_TongueGuideFlange',.023,.005,'A_Bronze',guide,(0,0,z),64)
# Coiling is authored in the source; no object visibility/scale tricks or discarded material.
for frame in range(1,338):
 t=(frame-1)/60
 v=max(0,min(1,(t-.3)/2)) if t<3.3 else 1-max(0,min(1,(t-3.3)/2))
 # An ID property must remain a float even during exact 0/1 holds, or Blender quantizes it.
 amount=float(v*v*(3-2*v));drive['feed']=float(amount);drive.keyframe_insert(data_path='["feed"]',frame=frame)
 state=path.frames(amount)[4];carriage.location=state['axis'];carriage.keyframe_insert('location',frame=frame);spool.rotation_euler.z=spin_sign*state['angle'];spool.keyframe_insert('rotation_euler',frame=frame)
scene.frame_start=1;scene.frame_end=337;scene.render.fps=60;scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True);bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_tongue_probe.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True)
# Bake small ROW motion fields, rather than shipping hundreds of complete mesh targets to the GPU.
field_dir=ROOT/'app/assets/collection/art/I/tongue_probe';field_dir.mkdir(parents=True,exist_ok=True)
fields={name:np.ones((keys+1,path.rows+1,4),dtype=np.float32) for name in ['center','width','normal']}
for k in range(keys+1):
 amount=k/keys;c,w,n,q,st=path.frames(amount);bow=path.profile_height(q)
 for name,vec in [('center',c),('width',w*path.material_width[:,None]),('normal',n)]:fields[name][k,:,:3]=vec[:,[0,2,1]]*np.array([1,1,-1])
 fields['center'][k,:,3]=1+bow
scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='32';scene.render.image_settings.exr_codec='ZIP'
texture_paths={}
for name,values in fields.items():
 im=bpy.data.images.new('Tongue motion '+name,width=path.rows+1,height=keys+1,float_buffer=True,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(values[::-1].ravel());file=field_dir/(name+'.exr');im.save_render(str(file),scene=scene);texture_paths[name]=str(file.relative_to(ROOT))
samples=[]
for k in range(keys+1):
 p,st=path.vertices(k/keys);samples.append(st)
report={'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'tongue_index':0,'mesh_names':meshes,'pose_steps':keys,'rows':path.rows+1,'render_backend':'authored_row_motion_fields','motion_textures':texture_paths,'texture_sha256':{name:sha(ROOT/file) for name,file in texture_paths.items()},'field_sample_front_center':fields['center'][0,180].tolist(),'field_sample_stored_center':fields['center'][-1,180].tolist(),'drive':drive.name,'carriage':carriage.name,'spool':spool.name,'spin_sign':spin_sign,'states':samples,'visible_length':path.length,'leader_length':path.leader_length,'total_material_length':path.total_length,'scope':'One tape-spring tongue motion/packing probe with retained leader and driven spool. Source has dense morph poses; runtime uses authored row motion fields. Other two tongues static; bearing case, grip/return catches and complete driving hardware pending. Needs actual surface, shape and continuity validation; not full OPEN or App integration.'}
report['field_pixel_sha256']={name:hashlib.sha256(values.astype('<f4').tobytes()).hexdigest() for name,values in fields.items()}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_TONGUE_PROBE_BUILT',flush=True)
