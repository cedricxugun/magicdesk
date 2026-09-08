"""Independent physical steam experiment. Reads main asset, never writes production blend/GLB/GD.

Examples:
 blender -b --python bake_pressure_fluid.py -- --resolution 48 --frames 24 --name probe48
 blender -b --python bake_pressure_fluid.py -- --resolution 96 --frames 84 --name pressure96
"""
import bpy,math,json,pathlib,time,sys,argparse,hashlib,gzip,array
import numpy as np
from mathutils import Matrix,Vector,Quaternion

parser=argparse.ArgumentParser();parser.add_argument('--resolution',type=int,default=48);parser.add_argument('--frames',type=int,default=24);parser.add_argument('--name',default='probe48');parser.add_argument('--sample-step',type=int,default=2);parser.add_argument('--export-only',action='store_true');parser.add_argument('--skip-render',action='store_true')
parser.add_argument('--ring-radius',type=float,default=.075);parser.add_argument('--jet-speed',type=float,default=3.6);parser.add_argument('--ring-off',type=int,default=25);parser.add_argument('--cavity-radius',type=float,default=.14);parser.add_argument('--cavity-density',type=float,default=.80)
parser.add_argument('--ground-impact',action='store_true');parser.add_argument('--jet-down',type=float,default=-3.4)
parser.add_argument('--ring-height',type=float,default=1.135);parser.add_argument('--ring-position-radius',type=float,default=.53)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'app'/'assets'/'physical_steam'/args.name;REV=ROOT/'review'/'physical_steam'/args.name;CACHE=REV/'mantaflow_cache'
for p in [OUT,REV,CACHE]:p.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'blender'/'Helios_Incubator.blend';META=ROOT/'app'/'assets'/'mechanism.json';source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest();meta_sha=hashlib.sha256(META.read_bytes()).hexdigest();meta=json.loads(META.read_text(encoding='utf-8'))
fps=24;C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
bounds_min=(-3.8,-3.8,-.12) if args.ground_impact else (-3.1,-3.1,.50);bounds_max=(3.8,3.8,4.50) if args.ground_impact else (3.1,3.1,4.80)

def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def openness(t):
 if t<.32:return 0.
 if t<.70:return .035*ease((t-.32)/.38)
 if t<1.50:return .035+(.84-.035)*(1-(1-(t-.70)/.80)**3)
 if t<2.20:return .84+.16*ease((t-1.50)/.70)
 return 1.
def from_data(d):
 q=d['q'];return C.inverted()@Matrix.LocRotScale(Vector(d['p']),Quaternion((q[3],q[0],q[1],q[2])),Vector(d['s']))@C
def constant_keys(o,path,values):
 for f,v in values:setattr(o,path,v);o.keyframe_insert(data_path=path,frame=f)
 owner=o.id_data if not hasattr(o,'animation_data') else o
 if owner.animation_data and owner.animation_data.action:
  for la in owner.animation_data.action.layers:
   for st in la.strips:
    for bag in st.channelbags:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:k.interpolation='CONSTANT'
def add_effector(o):
 m=o.modifiers.new('Physical obstacle','FLUID');m.fluid_type='EFFECTOR';bpy.context.view_layer.update();m.effector_settings.surface_distance=.001;o.hide_render=True;o.display_type='WIRE';return m
def emit(name,location,radius,velocity,on,off,density=.65,parent=None):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=radius,location=location);o=bpy.context.object;o.name=name
 if parent:o.parent=parent;o.location=location
 o.hide_render=True;o.display_type='WIRE';m=o.modifiers.new('Pressure inflow','FLUID');m.fluid_type='FLOW';bpy.context.view_layer.update();f=m.flow_settings;f.flow_type='SMOKE';f.flow_behavior='INFLOW';f.surface_distance=1.05;f.volume_density=1.;f.density=density;f.temperature=.04;f.use_initial_velocity=True;f.velocity_coord=velocity;f.velocity_normal=0.;f.subframes=1
 constant_keys(f,'use_inflow',[(1,False),(on,True),(off,False)]);return o
def radius(t):
 ts=[0,.06,.16,.30,.47,.62,.76,.87,.95,1];rs=[.31,.43,.62,.78,.865,.84,.73,.565,.365,.17];j=next((i for i in range(9) if t<=ts[i+1]),8);u=(t-ts[j])/(ts[j+1]-ts[j]);return rs[j]*(1-u)+rs[j+1]*u

if not args.export_only:
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));S=bpy.context.scene;S.frame_start=1;S.frame_end=args.frames;S.render.fps=fps;S.frame_set(1)
 # Reuse actual rig and model only inside this separate cache scene.
 for p in meta['parts']:
  o=bpy.data.objects[p['name']];o.animation_data_clear();o.matrix_local=from_data(p['home'])
 for d in meta['controls']:bpy.data.objects[d['name']].animation_data_clear()
 turn=bpy.data.objects[meta['turntable']];turn.animation_data_clear();turn.rotation_mode='XYZ';turn.rotation_euler=(0,0,0)
 for b in meta['buttons']:
  o=bpy.data.objects[b['cap']];o.animation_data_clear();o.matrix_local=from_data(b['home'])
 for frame in range(1,args.frames+1):
  value=openness((frame-1)/fps);x=value*100;lo=min(100,int(x));hi=min(100,lo+1);a=x-lo
  for d in meta['controls']:
   o=bpy.data.objects[d['name']];p0,q0,s0=from_data(d['samples'][lo]).decompose();p1,q1,s1=from_data(d['samples'][hi]).decompose();o.rotation_mode='QUATERNION';o.location=p0.lerp(p1,a);o.rotation_quaternion=q0.slerp(q1,a);o.scale=s0.lerp(s1,a)
   for path in ['location','rotation_quaternion','scale']:o.keyframe_insert(data_path=path,frame=frame)
 # Six thickened closed shell proxies: enough voxel thickness to constrain the low resolution test.
 for i in range(6):
  nu=12;nv=32;verts=[];faces=[];half=math.radians(28.6)
  for layer in [0,1]:
   for j in range(nv+1):
    t=j/nv;r=radius(t)+(.016 if layer==0 else -.085)
    for k in range(nu+1):a=-half+2*half*k/nu;verts.append((r*math.cos(a)-.31,r*math.sin(a),2.68*t))
  stride=(nv+1)*(nu+1)
  for j in range(nv):
   for k in range(nu):
    v=j*(nu+1)+k;faces.extend([(v,v+1,v+nu+2,v+nu+1),(v+stride+nu+1,v+stride+nu+2,v+stride+1,v+stride)])
  rim=list(range(nu+1))+[j*(nu+1)+nu for j in range(1,nv+1)]+list(range(nv*(nu+1)+nu-1,nv*(nu+1)-1,-1))+[j*(nu+1) for j in range(nv-1,0,-1)]
  for j,a in enumerate(rim):b=rim[(j+1)%len(rim)];faces.append((a,a+stride,b+stride,b))
  me=bpy.data.meshes.new('PhysicalShellMesh_%02d'%i);me.from_pydata(verts,[],faces);o=bpy.data.objects.new('PHYS_Shell_%02d'%i,me);S.collection.objects.link(o);o.parent=bpy.data.objects['PETAL_HINGE_%02d'%i];add_effector(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=1.36 if args.ground_impact else 1.20,depth=.60 if args.ground_impact else .32,location=(0,0,.30 if args.ground_impact else .70));base=bpy.context.object;base.name='PHYS_BaseObstacle';add_effector(base)
 if args.ground_impact:
  bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.16));ground=bpy.context.object;ground.name='PHYS_GroundObstacle';ground.dimensions=(20,20,.32);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);add_effector(ground)
 # 30 real gas inflows form a ring around the lower shell; all velocities are radial world vectors.
 for i in range(30):
  a=i*math.tau/30;r=args.ring_position_radius+.012*math.sin(a*7);speed=args.jet_speed*(1+.08*math.sin(a*11));vz=args.jet_down if args.ground_impact else .12;o=emit('PHYS_RingJet_%02d'%i,(r*math.cos(a),r*math.sin(a),args.ring_height),args.ring_radius,(speed*math.cos(a),speed*math.sin(a),vz),8,args.ring_off,1.0 if args.ground_impact else .92)
  flow=o.modifiers['Pressure inflow'].flow_settings
  for f,mult in [(1,1.),(8,1.),(12,1.22),(18,1.),(args.ring_off-1,.70)]:flow.velocity_coord=(speed*mult*math.cos(a),speed*mult*math.sin(a),vz);flow.keyframe_insert(data_path='velocity_coord',frame=f)
 # Internal release becomes available as the seam opens; sources remain real volumes and
 # release outward from the lower cavity, then buoyancy rolls the gas up along the open petals.
 for i in range(6):
  a=-math.pi/2+i*math.tau/6;r=.40;emit('PHYS_CavityRelease_%02d'%i,(r*math.cos(a),r*math.sin(a),1.32),args.cavity_radius,(1.25*math.cos(a),1.25*math.sin(a),.40),18,39,args.cavity_density)
 bpy.ops.mesh.primitive_cube_add(size=1,location=tuple((bounds_min[i]+bounds_max[i])/2 for i in range(3)));domain=bpy.context.object;domain.name='PHYSICAL_STEAM_DOMAIN';domain.dimensions=tuple(bounds_max[i]-bounds_min[i] for i in range(3));bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=domain.modifiers.new('Real Mantaflow gas','FLUID');mod.fluid_type='DOMAIN';bpy.context.view_layer.update();d=mod.domain_settings;d.domain_type='GAS';d.resolution_max=args.resolution;d.use_adaptive_domain=False;d.use_noise=False;d.alpha=.10;d.beta=.08;d.vorticity=.62;d.use_dissolve_smoke=True;d.dissolve_speed=16;d.use_dissolve_smoke_log=True;d.time_scale=1.;d.cache_type='MODULAR';d.cache_data_format='OPENVDB';d.cache_resumable=True;d.cache_frame_start=1;d.cache_frame_end=args.frames;d.cache_directory=str(CACHE)
 for side in ['front','back','right','left','top','bottom']:setattr(d,'use_collision_border_'+side,False)
 material=bpy.data.materials.new('PHYSICAL_WHITE_STEAM');material.use_nodes=True;nt=material.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');vol=nt.nodes.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.88,.91,.95,1);vol.inputs['Density'].default_value=6.0;vol.inputs['Anisotropy'].default_value=.20;nt.links.new(vol.outputs['Volume'],out.inputs['Volume']);domain.data.materials.append(material)
 # Main camera unchanged in production; this separate scene widens framing for physical spread.
 S.camera.location=(.45,-10.2,5.2);S.camera.rotation_euler=(Vector((0,0,1.9))-S.camera.location).to_track_quat('-Z','Y').to_euler();S.camera.data.sensor_fit='HORIZONTAL';S.camera.data.sensor_width=36;S.camera.data.lens=52
 S.render.resolution_x=1200;S.render.resolution_y=1000;S.render.resolution_percentage=100;S.render.engine='CYCLES';S.cycles.samples=48;S.cycles.use_denoising=True;S.frame_set(1)
 bpy.context.view_layer.objects.active=domain;bpy.ops.object.select_all(action='DESELECT');domain.select_set(True)
 (REV/'simulation_parameters.json').write_text(json.dumps(vars(args)|{'domain_min':bounds_min,'domain_max':bounds_max,'source_blend_sha256':source_sha,'mechanism_sha256':meta_sha},indent=2),encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(REV/'Physical_Steam_Cache.blend'),compress=True)
 print('PHYSICAL_BAKE_STARTED',args.resolution,args.frames,flush=True);began=time.perf_counter();result=bpy.ops.fluid.bake_data();elapsed=time.perf_counter()-began
 print('PHYSICAL_BAKE_FINISHED',result,'seconds',elapsed,flush=True)
 (REV/'bake_timing.json').write_text(json.dumps({'resolution_max':args.resolution,'frames':args.frames,'seconds':elapsed,'result':str(result),'cache_files':len(list(CACHE.rglob('*')))},indent=2),encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(REV/'Physical_Steam_Cache.blend'),compress=True)
else:
 bpy.ops.wm.open_mainfile(filepath=str(REV/'Physical_Steam_Cache.blend'));S=bpy.context.scene;domain=bpy.data.objects['PHYSICAL_STEAM_DOMAIN'];d=domain.modifiers['Real Mantaflow gas'].domain_settings

manifest={'method':'Blender Mantaflow Navier-Stokes gas density simulation, not procedural billboard particles','resolution_max':args.resolution,'simulation_fps':fps,'sample_fps':fps/args.sample_step,'source_blend':str(SOURCE),'cache_blend':str(REV/'Physical_Steam_Cache.blend'),'cache_directory':str(CACHE),'cache_resumable':True,'domain_blender_min':bounds_min,'domain_blender_max':bounds_max,'coordinate_mapping':'Godot(x,y,z) = Blender(x,z,-y). Density raw stored x-fastest: index=x+nx*(y+ny*z), NumPy shape(z,y,x).','density_format':'little-endian float32 raw; uint8 preview normalized by density_scale','density_scale':1.0,'frames':[]}
maximum=0;frames=list(range(1,args.frames+1,args.sample_step))
if args.frames not in frames:frames.append(args.frames)
for f in frames:
 S.frame_set(f);bpy.context.view_layer.update();evaluated=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());read_domain=evaluated.modifiers['Real Mantaflow gas'].domain_settings;values=np.array(read_domain.density_grid[:],dtype=np.float32);res=list(read_domain.domain_resolution)
 if values.size and all(res) and values.size!=res[0]*res[1]*res[2]:raise RuntimeError('Unexpected density grid size '+str((res,values.size)))
 if not values.size:
  manifest['frames'].append({'frame':f,'time':(f-1)/fps,'resolution':res,'empty':True});continue
 finite=bool(np.isfinite(values).all());assert finite,'Nonfinite density';lo=float(values.min());high=float(values.max());maximum=max(maximum,high);base='density_%04d'%f
 values.astype('<f4').tofile(OUT/(base+'.f32'));quant=np.round(np.clip(values,0,1)*255).astype(np.uint8);quant.tofile(OUT/(base+'.u8'))
 manifest['frames'].append({'frame':f,'time':(f-1)/fps,'resolution':res,'file_float32':base+'.f32','file_r8':base+'.u8','minimum':lo,'maximum':high,'mean':float(values.mean()),'nonzero':int(np.count_nonzero(values>1e-5)),'bytes':int(values.nbytes),'openness':openness((f-1)/fps)})
 print('DENSITY_EXPORTED',f,res,'max',high,'occupied',int(np.count_nonzero(values>1e-5)),flush=True)
manifest['maximum_density']=maximum;(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha and hashlib.sha256(META.read_bytes()).hexdigest()==meta_sha,'Production asset changed externally during bake; no write performed by this script'
if not args.skip_render:
 S.frame_set(min(args.frames,28));S.render.filepath=str(REV/'physical_density_review.png')
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
  for device in prefs.devices:device.use=device.type!='CPU'
  S.cycles.device='GPU'
 except Exception:pass
 bpy.ops.render.render(write_still=True)
print('PHYSICAL_STEAM_READY',str(OUT/'manifest.json'),'peak',maximum,flush=True)
