extends CompositorEffect
## Real cached Mantaflow steam, half-resolution integration and depth-aware RGBA composite.
## configure() takes values/resources only. Never pass Nodes or mutable scene objects.
## frame_a/frame_b: Texture3D (or RD RIDs), cache_to_world: Transform3D,
## bounds_min/max: Vector3 in cache space, world_bounds: AABB,
## mix/gain/density_scale/step/max_steps, core_position/color/energy/range,
## optional occupancy: Texture3D, occupancy_size: Vector3, resolution_scale: .5.

const RAY_SHADER=preload("res://steam_raymarch.glsl")
const COMPOSITE_SHADER=preload("res://steam_composite.glsl")
var _mutex:=Mutex.new()
var _snapshot:Dictionary={}
var _rd:RenderingDevice
var _ray:RID
var _composite:RID
var _ray_pipeline:RID
var _composite_pipeline:RID
var _linear:RID
var _nearest:RID
var _parameters:RID
var _context:StringName
var _size_by_buffer:Dictionary={}
var _status:Dictionary={"ready":false,"frames":0,"error":""}
var _warm_snapshot:Dictionary={}
var _warm_frames:Array=[]
var _warmed_buffers:Dictionary={}
var _warm_color:RID

func request_prewarm(snapshot:Dictionary,frames:Array)->void:
	_mutex.lock();_warm_snapshot=snapshot.duplicate();_warm_frames=frames.duplicate();_mutex.unlock()

func _init()->void:
	effect_callback_type=EFFECT_CALLBACK_TYPE_POST_TRANSPARENT
	access_resolved_color=true
	access_resolved_depth=true
	_context=StringName("helios_steam_%s"%get_instance_id())
	enabled=true

func configure(snapshot:Dictionary)->void:
	_mutex.lock()
	_snapshot=snapshot.duplicate()
	_mutex.unlock()

func get_diagnostics()->Dictionary:
	_mutex.lock();var result:=_status.duplicate();_mutex.unlock();return result

func _notification(what:int)->void:
	if what==NOTIFICATION_PREDELETE:
		# Bind value RIDs, not this dying resource. All GPU lifetime work stays on
		# the rendering thread; pipelines/sets are dependents of their shaders.
		if _rd:
			RenderingServer.call_on_render_thread(_free_gpu_resources.bind(_rd,[_ray,_composite,_linear,_nearest,_parameters,_warm_color]))

static func _free_gpu_resources(device:RenderingDevice,rids:Array)->void:
	for rid in rids:
		if rid.is_valid():device.free_rid(rid)

func _initialize()->bool:
	if _ray_pipeline.is_valid():return true
	var started:=Time.get_ticks_usec()
	_rd=RenderingServer.get_rendering_device()
	if _rd==null:return false
	var ray_spirv:RDShaderSPIRV=RAY_SHADER.get_spirv()
	var comp_spirv:RDShaderSPIRV=COMPOSITE_SHADER.get_spirv()
	var errors:=ray_spirv.compile_error_compute+comp_spirv.compile_error_compute
	if not errors.is_empty():
		_mutex.lock();_status.error=errors;_mutex.unlock();push_error(errors);return false
	_ray=_rd.shader_create_from_spirv(ray_spirv)
	_composite=_rd.shader_create_from_spirv(comp_spirv)
	_ray_pipeline=_rd.compute_pipeline_create(_ray)
	_composite_pipeline=_rd.compute_pipeline_create(_composite)
	var sampler:=RDSamplerState.new()
	sampler.mag_filter=RenderingDevice.SAMPLER_FILTER_LINEAR
	sampler.min_filter=RenderingDevice.SAMPLER_FILTER_LINEAR
	sampler.repeat_u=RenderingDevice.SAMPLER_REPEAT_MODE_CLAMP_TO_EDGE
	sampler.repeat_v=RenderingDevice.SAMPLER_REPEAT_MODE_CLAMP_TO_EDGE
	sampler.repeat_w=RenderingDevice.SAMPLER_REPEAT_MODE_CLAMP_TO_EDGE
	_linear=_rd.sampler_create(sampler)
	sampler.mag_filter=RenderingDevice.SAMPLER_FILTER_NEAREST
	sampler.min_filter=RenderingDevice.SAMPLER_FILTER_NEAREST
	_nearest=_rd.sampler_create(sampler)
	_parameters=_rd.storage_buffer_create(336)
	var format:=RDTextureFormat.new();format.width=8;format.height=8;format.format=RenderingDevice.DATA_FORMAT_R16G16B16A16_SFLOAT
	format.usage_bits=RenderingDevice.TEXTURE_USAGE_STORAGE_BIT
	_warm_color=_rd.texture_create(format,RDTextureView.new(),[])
	_mutex.lock();_status.ready=true;_status.pipeline_init_ms=(Time.get_ticks_usec()-started)/1000.0;_mutex.unlock()
	return _ray_pipeline.is_valid() and _composite_pipeline.is_valid()

func _texture_rd(value:Variant)->RID:
	if value is Texture3D:return RenderingServer.texture_get_rd_texture(value.get_rid())
	if value is RID:return value
	return RID()

func _uniform(binding:int,type:int,ids:Array)->RDUniform:
	var uniform:=RDUniform.new();uniform.binding=binding;uniform.uniform_type=type
	for id in ids:uniform.add_id(id)
	return uniform

func _append_projection(data:PackedFloat32Array,m:Projection)->void:
	for column in [m.x,m.y,m.z,m.w]:data.append_array(PackedFloat32Array([column.x,column.y,column.z,column.w]))

func _append_vec(data:PackedFloat32Array,v:Vector3,w:float)->void:
	data.append_array(PackedFloat32Array([v.x,v.y,v.z,w]))

func _render_callback(callback_type:int,render_data:RenderData)->void:
	if callback_type!=EFFECT_CALLBACK_TYPE_POST_TRANSPARENT or not _initialize():return
	var callback_started:=Time.get_ticks_usec()
	var buffers:RenderSceneBuffersRD=render_data.get_render_scene_buffers()
	if buffers==null:return
	var buffer_id:=buffers.get_instance_id()
	_mutex.lock();var snapshot:=_snapshot.duplicate();var warm_snapshot:=_warm_snapshot.duplicate();var warm_frames:=_warm_frames.duplicate();_mutex.unlock()
	var warming:=not _warmed_buffers.has(buffer_id) and not warm_snapshot.is_empty()
	if warming:snapshot=warm_snapshot
	if snapshot.is_empty() or not bool(snapshot.get("active",true)) or float(snapshot.get("gain",0.0))<.001:return
	var texture_a:=_texture_rd(snapshot.get("frame_a"))
	var texture_b:=_texture_rd(snapshot.get("frame_b"))
	if not texture_a.is_valid() or not texture_b.is_valid():return
	var occ:=_texture_rd(snapshot.get("occupancy"));var has_occ:=occ.is_valid()
	if not has_occ:occ=texture_a
	var scene:RenderSceneData=render_data.get_render_scene_data()
	if buffers==null or scene==null:return
	var full_size:=buffers.get_internal_size()
	if full_size.x<1 or full_size.y<1:return
	var scale:=clampf(float(snapshot.get("resolution_scale",.5)),.25,1.0)
	var low_size:=Vector2i(maxi(1,ceili(full_size.x*scale)),maxi(1,ceili(full_size.y*scale)))
	if _size_by_buffer.get(buffer_id,Vector2i.ZERO)!=low_size:
		buffers.clear_context(_context);_size_by_buffer[buffer_id]=low_size
	var usage:=RenderingDevice.TEXTURE_USAGE_SAMPLING_BIT|RenderingDevice.TEXTURE_USAGE_STORAGE_BIT
	if not buffers.has_texture(_context,"volume"):
		var allocation_started:=Time.get_ticks_usec()
		buffers.create_texture(_context,"volume",RenderingDevice.DATA_FORMAT_R16G16B16A16_SFLOAT,usage,RenderingDevice.TEXTURE_SAMPLES_1,low_size,buffers.get_view_count(),1,false,false)
		buffers.create_texture(_context,"depth",RenderingDevice.DATA_FORMAT_R32_SFLOAT,usage,RenderingDevice.TEXTURE_SAMPLES_1,low_size,buffers.get_view_count(),1,false,false)
		_mutex.lock();_status.volume_allocation_ms=(Time.get_ticks_usec()-allocation_started)/1000.0;_status.allocation_during_prewarm=warming;_status.allocation_count=int(_status.get("allocation_count",0))+1;_mutex.unlock()
	for view in range(buffers.get_view_count()):
		var volume:=buffers.get_texture_slice(_context,"volume",view,0,1,1)
		var low_depth:=buffers.get_texture_slice(_context,"depth",view,0,1,1)
		var color:=buffers.get_color_layer(view)
		var depth:=buffers.get_depth_layer(view)
		var camera:=scene.get_cam_transform()
		camera.origin+=camera.basis*scene.get_view_eye_offset(view)
		var world_to_cache:Transform3D=snapshot.get("world_to_cache",Transform3D.IDENTITY)
		if snapshot.has("cache_to_world"):world_to_cache=(snapshot.cache_to_world as Transform3D).affine_inverse()
		var cache_min:Vector3=snapshot.get("bounds_min",Vector3(-3.8,-.12,-3.8))
		var cache_max:Vector3=snapshot.get("bounds_max",Vector3(3.8,4.5,3.8))
		var world_bounds:AABB=snapshot.get("world_bounds",world_to_cache.affine_inverse()*AABB(cache_min,cache_max-cache_min))
		var data:=PackedFloat32Array()
		_append_projection(data,scene.get_view_projection(view).inverse())
		_append_projection(data,Projection(camera))
		_append_projection(data,Projection(world_to_cache))
		_append_vec(data,cache_min,float(snapshot.get("step",.04)))
		_append_vec(data,cache_max,clampf(float(snapshot.get("mix",0.0)),0.0,1.0))
		_append_vec(data,world_bounds.position,float(snapshot.get("gain",1.0)))
		_append_vec(data,world_bounds.end,float(snapshot.get("density_scale",1.0)))
		_append_vec(data,snapshot.get("core_position",Vector3(0,2.2,0)),float(snapshot.get("core_range",1.0)))
		var core_color:Color=snapshot.get("core_color",Color.WHITE)
		if not bool(snapshot.get("core_color_linear",false)):core_color=core_color.srgb_to_linear()
		_append_vec(data,Vector3(core_color.r,core_color.g,core_color.b),float(snapshot.get("core_energy",0.0)))
		data.append_array(PackedFloat32Array([full_size.x,full_size.y,low_size.x,low_size.y]))
		data.append_array(PackedFloat32Array([snapshot.get("max_steps",192),snapshot.get("core_shadow_steps",3),1.0 if has_occ else 0.0,snapshot.get("depth_softness",.09)]))
		_append_vec(data,snapshot.get("occupancy_size",Vector3(32,20,32)),0.0)
		var bytes:=data.to_byte_array();_rd.buffer_update(_parameters,0,bytes.size(),bytes)
		var ray_uniforms:Array[RDUniform]=[
			_uniform(0,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_nearest,depth]),
			_uniform(1,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_linear,texture_a]),
			_uniform(2,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_linear,texture_b]),
			_uniform(3,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_nearest,occ]),
			_uniform(4,RenderingDevice.UNIFORM_TYPE_IMAGE,[volume]),
			_uniform(5,RenderingDevice.UNIFORM_TYPE_IMAGE,[low_depth]),
			_uniform(6,RenderingDevice.UNIFORM_TYPE_STORAGE_BUFFER,[_parameters])]
		var comp_uniforms:Array[RDUniform]=[
			_uniform(0,RenderingDevice.UNIFORM_TYPE_IMAGE,[color]),
			_uniform(1,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_nearest,depth]),
			_uniform(2,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_linear,volume]),
			_uniform(3,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_nearest,low_depth]),
			_uniform(4,RenderingDevice.UNIFORM_TYPE_STORAGE_BUFFER,[_parameters])]
		var ray_set:=UniformSetCacheRD.get_cache(_ray,0,ray_uniforms)
		var comp_set:=UniformSetCacheRD.get_cache(_composite,0,comp_uniforms)
		if warming:
			# Build every adjacent density binding now, not when animation reaches it.
			for frame in range(warm_frames.size()):
				ray_uniforms[1]=_uniform(1,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_linear,_texture_rd(warm_frames[frame])])
				ray_uniforms[2]=_uniform(2,RenderingDevice.UNIFORM_TYPE_SAMPLER_WITH_TEXTURE,[_linear,_texture_rd(warm_frames[mini(frame+1,warm_frames.size()-1)])])
				UniformSetCacheRD.get_cache(_ray,0,ray_uniforms)
			# Dispatch the real composite pipeline only into an invisible 8x8 target.
			comp_uniforms[0]=_uniform(0,RenderingDevice.UNIFORM_TYPE_IMAGE,[_warm_color])
			comp_set=UniformSetCacheRD.get_cache(_composite,0,comp_uniforms)
		var list:=_rd.compute_list_begin()
		_rd.compute_list_bind_compute_pipeline(list,_ray_pipeline)
		_rd.compute_list_bind_uniform_set(list,ray_set,0)
		_rd.compute_list_dispatch(list,ceili(low_size.x/8.0),ceili(low_size.y/8.0),1)
		_rd.compute_list_add_barrier(list)
		_rd.compute_list_bind_compute_pipeline(list,_composite_pipeline)
		_rd.compute_list_bind_uniform_set(list,comp_set,0)
		_rd.compute_list_dispatch(list,1 if warming else ceili(full_size.x/8.0),1 if warming else ceili(full_size.y/8.0),1)
		_rd.compute_list_end()
	_mutex.lock();_status.frames=int(_status.frames)+1;_status.full_size=str(full_size);_status.low_size=str(low_size);_mutex.unlock()
	if warming:
		_warmed_buffers[buffer_id]=true
		_mutex.lock();_status.warmed=true;_status.warm_pair_count=warm_frames.size();_status.warmup_cpu_ms=(Time.get_ticks_usec()-callback_started)/1000.0;_status.warmup_visible_writes=0;_mutex.unlock()
		print("STEAM_GPU_PREWARM ",get_diagnostics())
	elif not _status.has("first_active_cpu_ms"):
		_mutex.lock();_status.first_active_cpu_ms=(Time.get_ticks_usec()-callback_started)/1000.0;_status.first_active_allocation_count=_status.get("allocation_count",0);_mutex.unlock()
