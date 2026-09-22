"""R83 installed acoustic receiver and readable optics on the R82 shell.
Old sources remain intact. This scene is a mechanical/projection sequence,
not a claim of complete audio or final-art acceptance.
"""
import bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as P
OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1/installed_r1';OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_r82_music_receiver_r1.blend';assert not SRC.exists()
body=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())
core=json.loads((OUT.parent/'optical_core_build.json').read_text());placement=json.loads((OUT.parent/'optical_placement.json').read_text())
old=json.loads((R/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/body['source']));scene=bpy.context.scene;scene.frame_set(1)
col=bpy.data.collections['R82_NEW_FORM'];P.configure(col)
# Preserve closed ceramic geometry, all guide transforms and shared base.
def shape_sig(o):
 import struct
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for row in o.matrix_world:h.update(struct.pack('<4f',*row))
 return h.hexdigest()
protected={o.name:shape_sig(o)for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('R82_Porcelain')or o in bpy.data.objects['BASE_FIXED'].children_recursive)}
with bpy.data.libraries.load(str(R/core['source']),link=False)as(src,dst):dst.collections=['MODULE_IAM']
scene.collection.children.link(dst.collections[0])
module=bpy.data.objects['IAM_MODULE'];module.matrix_world=Matrix(placement['matrix_blender'])
mouth=bpy.data.objects['IAM_Mouth'];optics=bpy.data.objects['I_MusicOptics'];bpy.context.view_layer.update()
receiver=P.empty('I83_ReceiverRoot',bpy.data.objects['R82_COIL_ROOT']);receiver.matrix_world=mouth.matrix_world
rear=bpy.data.objects['R82_Fixed_Rear_Keel'];liner=bpy.data.objects['R82_Acoustic_Chamber_Liner']
# The old generic dark return duplicated the real cartridge housing.
obsolete=bpy.data.objects['R82_Aperture_Inner_Return'];obsolete_counts={'name':obsolete.name,'vertices':len(obsolete.data.vertices)}
bpy.data.objects.remove(obsolete,do_unlink=True)
def boolean(o,tool,operation):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o
 m=o.modifiers.new('Formed acoustic receiver','BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 bpy.data.objects.remove(tool,do_unlink=True)
def profile_mesh(name,rows,parent,ma):
 N=192;vs=[];fs=[]
 for z,r in rows:
  for j in range(N):a=math.tau*j/N;vs.append((r*math.cos(a),r*math.sin(a),z))
 for k in range(len(rows)-1):
  for j in range(N):fs.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
 fs +=[tuple(range(N-1,-1,-1)),tuple((len(rows)-1)*N+j for j in range(N))]
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=parent;me.materials.append(bpy.data.materials['Collection_'+ma])
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 return o
rows=[(-.16,.851),(-.09,.851),(.20,.873),(.24,.880),(.43,.858),(.48,.62),(.62,.50)]
for part in [rear,liner]:
 tool=profile_mesh('I83_ClearanceTool',rows,receiver,'A_Dark');boolean(part,tool,'DIFFERENCE')
 assert len(part.data.polygons)>100,'Unexpectedly erased fixed coil skin'
# Integral receiver band is fused to the structural metal back, then bored.
band=P.sleeve('I83_ReceiverBandTool',.902,.862,.036,receiver,(0,0,.248),'A_Nickel')
boolean(rear,band,'UNION')
fasteners=[]
for row in old['collar_clamps']:
 k=row['index'];a=row['angle'];r=row['stud_radius']
 station=P.empty('I83_ReceiverStation_'+str(k),receiver);station.rotation_euler.z=a
 pad=P.box('I83_ReceiverPadTool_'+str(k),(.066,.021,.018),station,(r+.012,0,.239),'A_Nickel',.002)
 boolean(rear,pad,'UNION')
 # Blind receiver pocket starts at the carrier mating face; original carrier
 # bore and a fitted insert guide the screw. Fine thread form remains a task.
 tool=P.cylinder('I83_BlindPocketTool',.0029,.016,station,(r,0,.236),'A_Dark',bevel=0)
 boolean(rear,tool,'DIFFERENCE')
 P.sleeve('I83_CarrierBushing_'+str(k),.00420,.0028,.0158,station,(r,0,.222),'A_Bronze')
 bolt=P.empty('I83_RetainingScrew_'+str(k),station)
 P.screw('I83_ScrewHead_'+str(k),bolt,(r,0,.2105),.006,(0,0,-1))
 P.sleeve('I83_HeadWasher_'+str(k),.0086,.0028,.0015,bolt,(r,0,.21325),'A_Bronze')
 P.cylinder('I83_ScrewShank_'+str(k),.0026,.030,bolt,(r,0,.227),'A_Nickel',bevel=.0002)
 fasteners.append({'id':k,'root':bolt.name,'axis_blender':[0,0,1],'station':station.name,'stud_radius':r,'receiver_front':.230,'receiver_back':.248,'shaft_end':.242,'thread_geometry_complete':False})
# Rounded transition: actual host ellipse to the cartridge's round front lip.
pars=body['shape_parameters'];theta=pars['END'];rr=pars['RMAX'];g=pars['GROW']
C=Vector(pars['SHIFT'])+Vector((rr*math.cos(theta),-.44,rr*math.sin(theta)))
front=Vector((rr*(g*math.cos(theta)-math.sin(theta)),-.44*3/1.25,rr*(g*math.sin(theta)+math.cos(theta)))).normalized();back=-front
radial=Vector((math.cos(theta),0,math.sin(theta)));radial=(radial-front*radial.dot(front)).normalized();across=radial.cross(front).normalized()
# Front circular rim at the actual core mouth plane; narrow short flare only.
origin=mouth.matrix_world.translation;scale=placement['scale'];front_center=origin+back*(-.108*scale)
vs=[];fs=[];N=192;L=24
for wall in [0,.006]:
 for j in range(L+1):
  t=j/L;e=t*t*(3-2*t)
  centre=front_center.lerp(C,e)
  rx=(.807*scale+.002)*(1-e)+(pars['RAD']*rr-.014)*e+wall
  ry=(.807*scale+.002)*(1-e)+(pars['DEPTH']*rr-.014)*e+wall
  for i in range(N):
   a=math.tau*i/N;vs.append(centre+radial*rx*math.cos(a)+across*ry*math.sin(a))
count=(L+1)*N
for layer in [0,1]:
 for j in range(L):
  for i in range(N):
   a=layer*count+j*N+i;q=(a,layer*count+j*N+(i+1)%N,layer*count+(j+1)*N+(i+1)%N,a+N);fs.append(q if layer==0 else q[::-1])
for j in [0,L]:
 for i in range(N):
  a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+count,a+count)if j==0 else(a+count,b+count,b,a))
me=bpy.data.meshes.new('I83_TransitionMesh');me.from_pydata(vs,[],fs);me.update();transition=bpy.data.objects.new('I83_Continuous_Throat_Transition',me);col.objects.link(transition);transition.parent=bpy.data.objects['R82_COIL_ROOT'];me.materials.append(bpy.data.materials['R82_Warm_Acoustic_Alloy'])
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for p in me.polygons:p.use_smooth=True
# Bodies stay at rest for the invariant check; source motion is retimed only afterward.
bpy.context.view_layer.update();drift=[n for n,h in protected.items()if shape_sig(bpy.data.objects[n])!=h];assert not drift,drift
# A mechanical review sequence: throat opens first, then the six covers.
seen=set()
for o in col.objects:
 if o.animation_data and o.animation_data.action:
  action=o.animation_data.action
  if action.name in seen:continue
  seen.add(action.name)
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:
       key.co.x+=60;key.handle_left.x+=60;key.handle_right.x+=60
      fc.update()
for group in core['tongues']:bpy.data.objects[group['drive']].animation_data_clear()
for f in range(1,431):
 if f<79:opening=max(0,min(1,(f-1)/78))
 elif f<350:opening=1.
 else:opening=max(0,1-(f-350)/78)
 for group in core['tongues']:
  lo,hi=group['window'];t=max(0,min(1,(opening-lo)/(hi-lo)))
  drive=bpy.data.objects[group['drive']];drive['feed']=t*t*(3-2*t);drive.keyframe_insert(data_path='["feed"]',frame=f)
# Material reveal is for this silent mechanism preview; real playback uses Godot.
sheet=bpy.data.objects['I_MoonlightStaff'];ma=sheet.data.materials[0];nodes=ma.node_tree.nodes;links=ma.node_tree.links
mix=next(n for n in nodes if n.type=='MIX_SHADER');old_input=mix.inputs[0].links[0].from_socket
multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.name='I83_ProjectionReveal'
links.new(old_input,multiply.inputs[0]);links.new(multiply.outputs[0],mix.inputs[0])
for f,val in [(1,0),(175,0),(195,1),(218,1),(232,0),(430,0)]:
 multiply.inputs[1].default_value=val;multiply.inputs[1].keyframe_insert('default_value',frame=f)
for name in ['I_CentralReadingLine']+[r['ray']for r in json.loads((OUT.parent/'optical_layout.json').read_text())['scanner']['tips']]:
 ob=bpy.data.objects[name];ob.hide_render=True # Render actual beam pass later in Godot; no wrong-state static rays.
# The focus target also makes the authored Blender heads follow pressure motion.
focus=P.empty('I83_AuthoredReadingFocus',mouth)
focus.location=Vector(json.loads((OUT.parent/'optical_layout.json').read_text())['scanner']['focus'])
for entry in core['physical_heads']:
 head=bpy.data.objects[entry['head']];con=head.constraints.new('TRACK_TO');con.target=focus;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
scene.frame_start=1;scene.frame_end=430;scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
report={'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'body_parent':body['source'],'body_parent_sha256':body['source_sha256'],'core_source':core['source'],'core_component':core['component'],'core_component_sha256':core['component_sha256'],'placement':placement,'retained_ceramic_and_base_meshes':len(protected),'retained_hashes':protected,'removed_generic_return':obsolete_counts,'modified_fixed_metal':[rear.name,liner.name],'receiver_fasteners':fasteners,'scope':'Installed source with replacement receiving space, integral metal band/pads and real-size optical carrier. New sockets, fasteners, transition, full core travel and visual continuity are unverified until checks. Silent 430-frame mechanism/reveal study, not audio playback acceptance.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
 for dv in p.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=64;cam=scene.camera;scene.render.resolution_x=1200;scene.render.resolution_y=1320
for name,f,loc,target,span in [('installed_closed',1,(-4,-7,3.65),(0,0,1.57),4.1),('installed_reading',205,(-4,-7,3.65),(0,0,1.57),4.1),('mouth_reading',205,(-3,-6,2.8),tuple(C),1.65)]:
 scene.frame_set(f);bpy.context.view_layer.update();cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R83_RECEIVER_SOURCE_READY',flush=True)
