"""Resume verified ground-impact fluid, compute real decay tail and wavelet detail.
Only independent physical_steam experiment/cache/output files are written.
"""
import bpy,math,pathlib,json,time,hashlib,numpy as np
from mathutils import Matrix,Vector,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'review'/'physical_steam'/'ground_burst64';OUT=ROOT/'app'/'assets'/'physical_steam'/'ground_steam128';OUT.mkdir(exist_ok=True);CACHE=P/'mantaflow_cache';FPS=24;END=120
bpy.ops.wm.open_mainfile(filepath=str(P/'Physical_Steam_Cache.blend'));S=bpy.context.scene;D=bpy.data.objects['PHYSICAL_STEAM_DOMAIN'];d=D.modifiers['Real Mantaflow gas'].domain_settings;meta=json.loads((ROOT/'app'/'assets'/'mechanism.json').read_text(encoding='utf-8'));C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def openness(t):
 if t<.32:return 0.
 if t<.70:return .035*ease((t-.32)/.38)
 if t<1.5:return .035+.805*(1-(1-(t-.7)/.8)**3)
 if t<2.2:return .84+.16*ease((t-1.5)/.7)
 return 1.
def matrix(q):
 rot=q['q'];return C.inverted()@Matrix.LocRotScale(Vector(q['p']),Quaternion((rot[3],rot[0],rot[1],rot[2])),Vector(q['s']))@C
start=d.cache_frame_pause_data
for f in range(start+1,END+1):
 value=openness((f-1)/FPS);x=value*100;lo=min(100,int(x));hi=min(100,lo+1);a=x-lo
 for c in meta['controls']:
  o=bpy.data.objects[c['name']];p0,q0,s0=matrix(c['samples'][lo]).decompose();p1,q1,s1=matrix(c['samples'][hi]).decompose();o.location=p0.lerp(p1,a);o.rotation_quaternion=q0.slerp(q1,a);o.scale=s0.lerp(s1,a)
  for path in ['location','rotation_quaternion','scale']:o.keyframe_insert(data_path=path,frame=f)
d.cache_frame_end=END;S.frame_end=END;S.frame_set(start)
# Preserve solver settings from the accepted pressure sample. Changing dissolve_speed
# invalidates Mantaflow's base cache; continuation must keep the existing solver state.
bpy.context.view_layer.objects.active=D;bpy.ops.object.select_all(action='DESELECT');D.select_set(True)
first=CACHE/'data'/'fluid_data_0001.vdb';before=(first.stat().st_mtime,hashlib.sha256(first.read_bytes()).hexdigest());t=time.perf_counter();r=bpy.ops.fluid.bake_data();base_seconds=time.perf_counter()-t;after=(first.stat().st_mtime,hashlib.sha256(first.read_bytes()).hexdigest());assert before==after,'Unexpected rebake of initial segment'
print('GROUND_TAIL_BAKED',start,END,base_seconds,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Physical_Steam_Cache.blend'),compress=True)
d.use_noise=True;d.noise_scale=2;d.noise_strength=1.10;d.noise_pos_scale=2.;d.noise_time_anim=.10;d.cache_frame_start=1;d.cache_frame_pause_noise=0;S.frame_set(1);t=time.perf_counter();r=bpy.ops.fluid.bake_noise();noise_seconds=time.perf_counter()-t
print('GROUND_WAVELET_BAKED',noise_seconds,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Physical_Steam_Cache.blend'),compress=True)
manifest={'method':'Mantaflow physical gas: down/out annular pressure jets, solid ground impact, moving six-petal collisions, 2x wavelet detail','simulation_fps':24,'sample_fps':12,'base_resolution':[64,64,39],'resolution':[128,128,78],'domain_blender_min':[-3.8,-3.8,-.12],'domain_blender_max':[3.8,3.8,4.5],'coordinate_mapping':'Godot(x,y,z)=Blender(x,z,-y). Raw float32 is x-fastest; reshape(nz,ny,nx).','density_format':'little-endian float32; exact unclamped physical density including values greater than 1','density_scale':4.0,'density_r8_note':'R8 preview stores clamp(density/4,0,1)*255; runtime should prefer full float32->R16F','cache_resumable':True,'cache_directory':str(CACHE),'cache_blend':str(P/'Physical_Steam_Cache.blend'),'pressure_source':{'ring_emitters':30,'position_radius':.66,'height':1.22,'emitter_radius':.13,'radial_speed':12.,'downward_speed':-6.,'ring_on_frame':8,'ring_off_frame':25,'cavity_emitters':6,'cavity_on_frame':18,'cavity_off_frame':39},'collision_proxies':{'ground_top_z':0.,'base_radius':1.36,'base_top_z':.60,'animated_shell_count':6},'timing':{'resumed_from_frame':start,'tail_end_frame':END,'tail_bake_seconds':base_seconds,'noise_bake_seconds':noise_seconds,'initial_cache_unchanged':True},'frames':[]}
peak=0.;peakmass=0.
for f in list(range(1,END+1,2))+[END]:
 S.frame_set(f);bpy.context.view_layer.update();e=D.evaluated_get(bpy.context.evaluated_depsgraph_get());ds=e.modifiers['Real Mantaflow gas'].domain_settings;base=list(ds.domain_resolution);a=np.array(ds.density_grid[:],dtype=np.float32);nbase=int(np.prod(base));factor=int(round((a.size/nbase)**(1/3))) if nbase and a.size else 0;res=[v*factor for v in base]
 if not a.size:raise RuntimeError('Missing baked wavelet frame '+str(f))
 assert factor==2 and a.size==int(np.prod(res)),(f,base,a.size,factor)
 assert np.isfinite(a).all();name='density_%04d'%f;a.astype('<f4').tofile(OUT/(name+'.f32'));np.round(np.clip(a/4,0,1)*255).astype(np.uint8).tofile(OUT/(name+'.u8'));mass=float(a.sum(dtype=np.float64));maximum=float(a.max());peak=max(peak,maximum);peakmass=max(peakmass,mass)
 z=(np.arange(res[2])+.5)/res[2]*4.62-.12;v=a.reshape(res[2],res[1],res[0]);groundmass=float(v[z<.35].sum(dtype=np.float64));belowground=float(v[z<0].sum(dtype=np.float64));row={'frame':f,'time':(f-1)/FPS,'resolution':res,'file_float32':name+'.f32','file_r8':name+'.u8','maximum':maximum,'mean':float(a.mean()),'sum_density':mass,'ground_layer_fraction':groundmass/max(mass,1e-12),'underground_density_sum':belowground,'nonzero':int(np.count_nonzero(a>1e-5)),'bytes':int(a.nbytes),'openness':openness((f-1)/FPS)};manifest['frames'].append(row)
 print('GROUND_WAVELET_EXPORTED',f,res,maximum,mass,flush=True)
manifest['maximum_density']=peak;manifest['peak_sum_density']=peakmass;manifest['last_to_peak_mass_ratio']=manifest['frames'][-1]['sum_density']/peakmass
for row in manifest['frames']:row['mass_relative_to_peak']=row['sum_density']/peakmass
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('GROUND_FINAL_MANIFEST',str(OUT/'manifest.json'),'tail ratio',manifest['last_to_peak_mass_ratio'],flush=True)
S.render.resolution_x=1400;S.render.resolution_y=1100;S.cycles.samples=72;S.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for device in prefs.devices:device.use=device.type!='CPU'
 S.cycles.device='GPU'
except Exception:pass
for f in [17,28,49,85,120]:
 S.frame_set(f);S.render.filepath=str(P/('ground_wavelet_%04d.png'%f));bpy.ops.render.render(write_still=True)
print('GROUND_WAVELET_REVIEW_READY',flush=True)
