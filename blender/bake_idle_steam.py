"""Independent low-flow physical standby steam. Never updates production assets/runtime."""
import bpy,math,pathlib,json,time,argparse,sys,hashlib,numpy as np
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--frames',type=int,default=72);parser.add_argument('--resolution',type=int,default=48);parser.add_argument('--name',default='idle_probe48');parser.add_argument('--noise',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--no-render',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=pathlib.Path(__file__).resolve().parents[1];REV=ROOT/'review'/'physical_steam'/args.name;OUT=ROOT/'app'/'assets'/'physical_steam'/args.name;CACHE=REV/'mantaflow_cache'
for p in [REV,OUT,CACHE]:p.mkdir(parents=True,exist_ok=True)
MAIN=ROOT/'blender'/'Helios_Incubator.blend';META=ROOT/'app'/'assets'/'mechanism.json';before_main=hashlib.sha256(MAIN.read_bytes()).hexdigest();before_meta=hashlib.sha256(META.read_bytes()).hexdigest();bbox_min=[-1.55,-1.55,.50];bbox_max=[1.55,1.55,4.25]
def effector(o):
 f=o.modifiers.new('Standby collision','FLUID');f.fluid_type='EFFECTOR';bpy.context.view_layer.update();f.effector_settings.surface_distance=.001;o.hide_render=True;o.display_type='WIRE'
def profile(t):
 ts=[0,.06,.16,.30,.47,.62,.76,.87,.95,1];rs=[.31,.43,.62,.78,.865,.84,.73,.565,.365,.17];j=next((i for i in range(9) if t<=ts[i+1]),8);u=(t-ts[j])/(ts[j+1]-ts[j]);return rs[j]*(1-u)+rs[j+1]*u
def source(name,position,rad,velocity,density):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=rad,location=position);o=bpy.context.object;o.name=name;o.hide_render=True;o.display_type='WIRE';m=o.modifiers.new('Continuous actual gas emission','FLUID');m.fluid_type='FLOW';bpy.context.view_layer.update();f=m.flow_settings;f.flow_type='SMOKE';f.flow_behavior='INFLOW';f.use_inflow=True;f.surface_distance=.7;f.volume_density=1.;f.density=density;f.temperature=.10;f.use_initial_velocity=True;f.velocity_coord=velocity;f.subframes=1;return o
if not args.resume:
 bpy.ops.wm.open_mainfile(filepath=str(MAIN));S=bpy.context.scene;S.frame_set(1);bpy.context.view_layer.update()
 for o in S.objects:
  if o.animation_data:o.animation_data_clear()
 core=bpy.data.materials.get('Solar_Core_Emission')
 if core and core.use_nodes:
  if core.node_tree.animation_data:core.node_tree.animation_data_clear()
  ps=core.node_tree.nodes.get('Principled BSDF')
  if ps:ps.inputs['Emission Strength'].default_value=.8
 S.frame_start=1;S.frame_end=args.frames;S.render.fps=24
 for i in range(6):
  nu=12;nv=32;verts=[];faces=[];half=math.radians(28.6)
  for layer in [0,1]:
   for j in range(nv+1):
    t=j/nv;r=profile(t)+(.008 if layer==0 else -.08)
    for k in range(nu+1):a=-half+2*half*k/nu;verts.append((r*math.cos(a)-.31,r*math.sin(a),2.68*t))
  stride=(nu+1)*(nv+1)
  for j in range(nv):
   for k in range(nu):
    v=j*(nu+1)+k;faces.extend([(v,v+1,v+nu+2,v+nu+1),(v+stride+nu+1,v+stride+nu+2,v+stride+1,v+stride)])
  rim=list(range(nu+1))+[j*(nu+1)+nu for j in range(1,nv+1)]+list(range(nv*(nu+1)+nu-1,nv*(nu+1)-1,-1))+[j*(nu+1) for j in range(nv-1,0,-1)]
  for j,a in enumerate(rim):b=rim[(j+1)%len(rim)];faces.append((a,a+stride,b+stride,b))
  me=bpy.data.meshes.new('IdleShellMesh_%02d'%i);me.from_pydata(verts,[],faces);o=bpy.data.objects.new('IDLE_COLLIDER_SHELL_%02d'%i,me);S.collection.objects.link(o);o.parent=bpy.data.objects['PETAL_HINGE_%02d'%i];effector(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=1.36,depth=.60,location=(0,0,.30));o=bpy.context.object;o.name='IDLE_COLLIDER_BASE';effector(o)
 for i in range(6):
  a=i*math.tau/6;r=.66;source('IDLE_SEAM_SOURCE_%02d'%i,(r*math.cos(a),r*math.sin(a),1.10),.032,(.035*math.cos(a),.035*math.sin(a),.085),.070)
 # Actual raised thermal valve: detail_helios.py j=0 base(.89,.10,2.02) + .59m anode.
 source('IDLE_SIDE_VALVE_SOURCE',(.89,.10,2.62),.031,(.025,0,.16),.100)
 bpy.ops.mesh.primitive_cube_add(size=1,location=tuple((a+b)/2 for a,b in zip(bbox_min,bbox_max)));D=bpy.context.object;D.name='IDLE_STEAM_DOMAIN';D.dimensions=tuple(b-a for a,b in zip(bbox_min,bbox_max));bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);m=D.modifiers.new('Actual idle Mantaflow gas','FLUID');m.fluid_type='DOMAIN';bpy.context.view_layer.update();d=m.domain_settings;d.domain_type='GAS';d.resolution_max=args.resolution;d.use_adaptive_domain=False;d.use_noise=False;d.alpha=.28;d.beta=.12;d.vorticity=.32;d.use_dissolve_smoke=True;d.dissolve_speed=8;d.use_dissolve_smoke_log=True;d.time_scale=1.;d.cache_type='MODULAR';d.cache_data_format='OPENVDB';d.cache_resumable=True;d.cache_frame_start=1;d.cache_frame_end=args.frames;d.cache_directory=str(CACHE)
 for side in ['front','back','right','left','top','bottom']:setattr(d,'use_collision_border_'+side,False)
 mat=bpy.data.materials.new('IDLE_LOW_FLOW_WHITE_STEAM');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();v=nt.nodes.new('ShaderNodeVolumePrincipled');v.inputs['Color'].default_value=(.88,.91,.95,1);v.inputs['Density'].default_value=6.;v.inputs['Anisotropy'].default_value=.20;out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(v.outputs['Volume'],out.inputs['Volume']);D.data.materials.append(mat)
 S.camera.location=(.65,-7.65,3.95);S.camera.rotation_euler=(Vector((0,0,1.95))-S.camera.location).to_track_quat('-Z','Y').to_euler();S.camera.data.sensor_fit='HORIZONTAL';S.camera.data.sensor_width=36;S.camera.data.lens=55;S.render.resolution_x=1200;S.render.resolution_y=1400;S.render.resolution_percentage=100;S.render.engine='CYCLES';S.cycles.samples=72;S.cycles.use_denoising=True
else:
 bpy.ops.wm.open_mainfile(filepath=str(REV/'Idle_Steam_Cache.blend'));S=bpy.context.scene;D=bpy.data.objects['IDLE_STEAM_DOMAIN'];d=D.modifiers['Actual idle Mantaflow gas'].domain_settings;d.cache_directory=str(CACHE);S.frame_end=args.frames;d.cache_frame_end=args.frames
start=d.cache_frame_pause_data;S.frame_set(max(1,start));bpy.context.view_layer.objects.active=D;bpy.ops.object.select_all(action='DESELECT');D.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=str(REV/'Idle_Steam_Cache.blend'),compress=True)
t=time.perf_counter();bpy.ops.fluid.bake_data();base_seconds=time.perf_counter()-t;print('IDLE_BASE_BAKED',start,args.frames,base_seconds,flush=True);bpy.ops.wm.save_as_mainfile(filepath=str(REV/'Idle_Steam_Cache.blend'),compress=True);noise_seconds=0.
if args.noise:
 d.use_noise=True;d.noise_scale=2;d.noise_strength=.65;d.noise_pos_scale=1.7;d.noise_time_anim=.10;d.cache_frame_pause_noise=0;S.frame_set(1);t=time.perf_counter();bpy.ops.fluid.bake_noise();noise_seconds=time.perf_counter()-t;bpy.ops.wm.save_as_mainfile(filepath=str(REV/'Idle_Steam_Cache.blend'),compress=True);print('IDLE_NOISE_BAKED',noise_seconds,flush=True)
manifest={'method':'Independent continuous low-flow Mantaflow gas for standby; not a loop cut from the pressure burst','simulation_fps':24,'sample_fps':12,'source_blend':str(MAIN),'cache_blend':str(REV/'Idle_Steam_Cache.blend'),'cache_directory':str(CACHE),'domain_blender_min':bbox_min,'domain_blender_max':bbox_max,'coordinate_mapping':'Godot(x,y,z)=Blender(x,z,-y). Raw x-fastest; reshape(nz,ny,nx).','density_format':'little-endian float32, no light baked; R8 preview density/1*255','density_scale':1.,'turntable_bake_rotation':0.,'collisions':'Six closed shell proxies + base; low upward flow, no ground blast.','source_parameters':{'seam_count':6,'seam_radius':.66,'seam_height':1.10,'seam_density':.070,'seam_velocity_up':.085,'side_valve_position':[.89,.10,2.62],'side_valve_density':.100,'side_valve_velocity_up':.16},'timing':{'base_bake_seconds':base_seconds,'noise_bake_seconds':noise_seconds},'frames':[]}
for f in list(range(1,args.frames+1,2))+([args.frames] if args.frames%2==0 else []):
 S.frame_set(f);bpy.context.view_layer.update();e=D.evaluated_get(bpy.context.evaluated_depsgraph_get());dd=e.modifiers['Actual idle Mantaflow gas'].domain_settings;base=list(dd.domain_resolution);a=np.array(dd.density_grid[:],dtype=np.float32);factor=int(round((a.size/np.prod(base))**(1/3)));res=[x*factor for x in base];assert a.size==np.prod(res) and np.isfinite(a).all()
 name='density_%04d'%f;a.astype('<f4').tofile(OUT/(name+'.f32'));np.round(np.clip(a,0,1)*255).astype(np.uint8).tofile(OUT/(name+'.u8'));manifest['frames'].append({'frame':f,'time':(f-1)/24,'resolution':res,'file_float32':name+'.f32','file_r8':name+'.u8','maximum':float(a.max()),'mean':float(a.mean()),'sum_density':float(a.sum(dtype=np.float64)),'bytes':int(a.nbytes)})
manifest['resolution']=manifest['frames'][-1]['resolution'];manifest['loop_start_time']=(args.frames//2)/24;manifest['loop_end_time']=(args.frames-1)/24;manifest['loop_crossfade_seconds']=.50;steady=[f['sum_density'] for f in manifest['frames'] if f['time']>=manifest['loop_start_time']];manifest['loop_mass_variation_cv']=float(np.std(steady)/max(np.mean(steady),1e-12));manifest['loop_note']='Play startup once. In last .50s of loop, crossfade to the first .50s of the loop; wrap to loop_start+.50. Crossfade density fields, not camera billboards.'
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('IDLE_DENSITY_READY',str(OUT/'manifest.json'),'res',manifest['resolution'],'steady CV',manifest['loop_mass_variation_cv'],flush=True)
assert hashlib.sha256(MAIN.read_bytes()).hexdigest()==before_main and hashlib.sha256(META.read_bytes()).hexdigest()==before_meta
if not args.no_render:
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
  for x in prefs.devices:x.use=x.type!='CPU'
  S.cycles.device='GPU'
 except Exception:pass
 for f in [args.frames//2,args.frames]:
  S.frame_set(f);S.render.filepath=str(REV/('idle_actual_%04d.png'%f));bpy.ops.render.render(write_still=True)
print('IDLE_REVIEW_READY',flush=True)
