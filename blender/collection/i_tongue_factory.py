"""Reusable authored tongue/coil components; does not clear or save the caller's scene."""
import bpy,bmesh,math,hashlib
import numpy as np
from mathutils import Matrix,Vector
from i_tongue_path import TonguePath

def add_tongue(index,root,asset_directory,mouth,col,steps=256):
 path=TonguePath(index,rows=360,columns=16);prefix='IAM_Tongue%d'%index
 def empty(s,parent=mouth):
  o=bpy.data.objects.new(prefix+'_'+s,None);col.objects.link(o);o.parent=parent;return o
 def link(o,name,material,parent,loc=(0,0,0)):
  o.name=prefix+'_'+name
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(bpy.data.materials['Collection_'+material]);return o
 def cylinder(name,r,length,material,parent,loc=(0,0,0),segments=64):
  bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=length);o=link(bpy.context.object,name,material,parent,loc)
  for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
  return o
 def box(name,dim,parent,loc,mat='A_Nickel',basis=None):
  bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.scale=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o,name,mat,parent,loc)
  if basis is not None:o.matrix_basis=basis;o.location=loc
  return o
 # Remove only this member's old static leaves and obsolete two-ended support pins.
 for o in list(bpy.data.objects):
  if o.name.startswith('IAM_Eyelid_%d_'%index) or o.name.startswith('IAM_EyelidRoot_%d_'%index) or o.name in ['IAM_EyelidStackSeat_'+str(index*2),'IAM_EyelidStackSeat_'+str(index*2+1),'IAM_EyelidCaptiveHead_'+str(index*2),'IAM_EyelidCaptiveHead_'+str(index*2+1)]:bpy.data.objects.remove(o,do_unlink=True)
 width=float(path.material_width.max());drum_width=width+.028;flange_axis=drum_width/2+.008
 slot_basis=Matrix((Vector(path.roll_side),Vector(path.outward),Vector(path.back))).transposed().to_4x4();u=(.220-path.turn_end[2]-path.entry_radius)/path.straight_z;center=Vector(path.guide(np.array([u]))[0])
 tool=box('GuideSlotTool',(width+.027,.020,.200),mouth,center,'A_Dark',slot_basis);carrier=bpy.data.objects['IAM_EyelidFixedCarrier']
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=carrier;mod=carrier.modifiers.new('Tongue %d passage'%index,'BOOLEAN');mod.operation='DIFFERENCE';mod.object=tool;mod.solver='EXACT';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
 drive=empty('Drive');drive['feed']=0.;meshes=[];faces=path.topology();stride=(path.rows+1)*(path.columns+1)
 for skin in range(2):
  pos,_=path.vertices(0,skin);m=bpy.data.meshes.new(prefix+'_FoilMesh%d'%skin);m.from_pydata(pos.tolist(),[],faces);m.update();o=bpy.data.objects.new(prefix+'_Foil%d'%skin,m);col.objects.link(o);o.parent=mouth
  m.materials.append(bpy.data.materials['Collection_A_LeafNickel' if skin==0 else 'Collection_A_LeafNickelReverse'])
  for f in m.polygons:f.use_smooth=True
  bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
  uv=m.uv_layers.new(name='ContinuousMaterialUV');data_uv=m.uv_layers.new(name='TongueRowData')
  for face in m.polygons:
   for li in face.loop_indices:
    vi=m.loops[li].vertex_index;j=(vi%stride)//(path.columns+1);w=(vi%stride)%(path.columns+1)/path.columns;uv.data[li].uv=(float(path.material_s[j]/path.length)*3,w*.45);data_uv.data[li].uv=((j+.5)/(path.rows+1),w+2*(vi//stride))
  o.shape_key_add(name='Basis')
  for k in range(1,steps+1):
   positions,_=path.vertices(k/steps,skin);key=o.shape_key_add(name='feed_%03d'%k);key.data.foreach_set('co',positions.astype(np.float32).ravel());key.value=0.
   d=key.driver_add('value').driver;d.type='SCRIPTED';v=d.variables.new();v.name='feed';v.type='SINGLE_PROP';v.targets[0].id=drive;v.targets[0].data_path='["feed"]';d.expression='max(0,1-abs(feed*%d-%d))'%(steps,k)
  meshes.append(o.name)
  print('TONGUE_SET_MORPHS',index,skin,flush=True)
 state=path.frames(0)[4];carriage=empty('SpoolCarriage');carriage.location=state['axis'];local_y=np.cross(path.roll_side,path.outward);spin_sign=float(np.dot(local_y,path.back));orientation=Matrix((Vector(path.outward),Vector(local_y),Vector(path.roll_side))).transposed().to_4x4();orient=empty('SpoolOrientation',carriage);orient.matrix_basis=orientation;spool=empty('Spool',orient)
 cylinder('SpoolCore',path.r0-.005,drum_width,'A_Dark',spool)
 profile=[(path.r0+.0009,-.010),(path.r0+.0013,-.010),(path.r0+.0013,.010),(path.r0+.0009,.010)];vs=[];fs=[];n=24
 for radius,z in profile:
  for j in range(n+1):a=-.13+.26*j/n;vs.append((radius*math.cos(a),radius*math.sin(a),z))
 for k in range(4):
  for j in range(n):fs.append((k*(n+1)+j,k*(n+1)+j+1,((k+1)%4)*(n+1)+j+1,((k+1)%4)*(n+1)+j))
 fs.extend([tuple(k*(n+1) for k in range(3,-1,-1)),tuple(k*(n+1)+n for k in range(4))]);m=bpy.data.meshes.new(prefix+'_CurvedClamp');m.from_pydata(vs,[],fs);o=bpy.data.objects.new(prefix+'_LeaderOuterJaw',m);col.objects.link(o);o.parent=spool;m.materials.append(bpy.data.materials['Collection_A_Nickel']);bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 box('LeaderInnerJaw',(.001,.008,.020),spool,(path.r0-.0054,0,0));box('LeaderBridge',(.0063,.001,.020),spool,(path.r0-.00225,.0045,0))
 flange_radius=path.frames(1)[4]['outer_radius']+.009
 for z in [-flange_axis,flange_axis]:
  cylinder('SpoolFlange',flange_radius,.005,'A_Nickel',spool,(0,0,z),96);cylinder('AxleEnd',.012,.025,'A_Bronze',orient,(0,0,z+(.015 if z>0 else -.015)),48)
 guide=empty('GuideRoller');guide.matrix_basis=orientation;guide.location=path.turn_end+path.back*path.entry_radius;cylinder('GuideMandrel',path.entry_radius-.005,width+.025,'A_Nickel',guide)
 for z in [-(width/2+.020),width/2+.020]:cylinder('GuideFlange',.023,.005,'A_Bronze',guide,(0,0,z),64)
 fields={name:np.ones((steps+1,path.rows+1,4),dtype=np.float32) for name in ['center','width','normal']};states=[]
 for k in range(steps+1):
  c,w,n,q,st=path.frames(k/steps);states.append(st)
  for name,vec in [('center',c),('width',w*path.material_width[:,None]),('normal',n)]:fields[name][k,:,:3]=vec[:,[0,2,1]]*np.array([1,1,-1])
  fields['center'][k,:,3]=1+path.profile_height(q)
 directory=asset_directory/str(index);directory.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='32';scene.render.image_settings.exr_codec='ZIP';textures={}
 for name,data in fields.items():
  im=bpy.data.images.new(prefix+'_'+name,width=path.rows+1,height=steps+1,float_buffer=True,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(data[::-1].ravel());file=directory/(name+'.exr');im.save_render(str(file),scene=scene);textures[name]=str(file.relative_to(root))
 result={'tongue_index':index,'mesh_names':meshes,'drive':drive.name,'carriage':carriage.name,'spool':spool.name,'spin_sign':spin_sign,'pose_steps':steps,'rows':path.rows+1,'states':states,'motion_textures':textures,'texture_sha256':{name:hashlib.sha256((root/file).read_bytes()).hexdigest() for name,file in textures.items()},'field_pixel_sha256':{name:hashlib.sha256(data.astype('<f4').tobytes()).hexdigest() for name,data in fields.items()},'field_sample_front_center':fields['center'][0,180].tolist(),'field_sample_stored_center':fields['center'][-1,180].tolist(),'visible_length':path.length,'total_material_length':path.total_length,'drum_width':drum_width,'flange_radius':flange_radius}
 return result,path
