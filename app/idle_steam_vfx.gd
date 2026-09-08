extends Node3D
## Independent continuous low-flow steam. It never changes model rotation,
## pressure timers, pressure burst_active, or any other controller's state.
## setup(host), load_manifest(converted_texture3d_manifest), tick(delta).
## During a high-pressure burst the caller supplies set_activity(0.0), then 1.0.
## Rotation history and the cache clock keep advancing while suppressed.

const HISTORY_STEP:=.1
const HISTORY_SPAN:=6.0
const HISTORY_COUNT:=61
var host:Node3D
var turntable:Node3D
var compositor:CompositorEffect
var idle_active:=false
var activity_target:=1.0
var gain:=0.0
var source_off_elapsed:=-1.0
var clock:=0.0
var quality_profile:="balanced"
var density_scale:=1.0
var physics_frames:Array[Texture3D]=[]
var frame_times:PackedFloat32Array=PackedFloat32Array()
var cache_bounds:=AABB(Vector3(-1.55,.5,-1.55),Vector3(3.10,3.75,3.10))
var loop_duration:=1.5
var fps:=12.0
var cell_size:=.03875
var history:Array[PackedFloat64Array]=[] # double-precision time and unwrapped yaw
var _previous_raw_yaw:=0.0
var _unwrapped_yaw:=0.0
var _next_history_time:=0.0
var _last_delta:=0.0
var _resolution_scale:=.4
var _max_steps:=96
var _step_multiplier:=.90
var last_error:=""

func setup(owner:Node3D)->void:
	if is_instance_valid(host):return
	host=owner
	turntable=host.get("turntable") as Node3D
	if turntable==null:turntable=host.named("TURNTABLE")
	var camera:Camera3D=host.get("camera")
	if turntable==null or camera==null:
		last_error="Idle steam requires the existing turntable and Camera3D.";push_error(last_error);return
	_previous_raw_yaw=turntable.rotation.y
	_unwrapped_yaw=_previous_raw_yaw
	for i in range(HISTORY_COUNT):history.append(PackedFloat64Array([-HISTORY_SPAN+i*HISTORY_STEP,_unwrapped_yaw]))
	_next_history_time=HISTORY_STEP
	compositor=load("res://idle_steam_compositor.gd").new()
	if camera.compositor==null:camera.compositor=Compositor.new()
	var effects:Array[CompositorEffect]=camera.compositor.compositor_effects.duplicate()
	# Draw low steam before an existing burst. Both write premultiplied RGBA
	# directly into the same full-resolution scene, never a desktop overlay.
	effects.insert(0,compositor);camera.compositor.compositor_effects=effects
	set_process(false)

func load_manifest(path:String)->bool:
	var data:Variant=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Dictionary or not data.has("frames"):
		last_error="Idle steam manifest is missing a frames array: "+path;return false
	var loaded:Array[Texture3D]=[]
	var times:=PackedFloat32Array()
	for index in range(data.frames.size()):
		var item:Variant=data.frames[index]
		var resource_path:=""
		if item is String:resource_path=item
		elif item is Dictionary:resource_path=str(item.get("resource",item.get("texture","")))
		if resource_path.is_empty():
			last_error="Idle steam needs the converted R16F Texture3D manifest; raw f32 source frames are not runtime resources.";return false
		if not resource_path.begins_with("res://") and not resource_path.is_absolute_path():resource_path=path.get_base_dir().path_join(resource_path)
		var texture:Variant=load(resource_path)
		if not texture is Texture3D:
			last_error="Idle steam frame is not a Texture3D: "+resource_path;return false
		loaded.append(texture)
		if item is Dictionary and item.has("time"):times.append(float(item.time))
	if loaded.is_empty():last_error="Idle steam cache is empty.";return false
	if not data.has("bounds_min") or not data.has("bounds_max"):
		last_error="Idle manifest bounds_min/max must use Godot x,y,z coordinates.";return false
	var mn:=Vector3(data.bounds_min[0],data.bounds_min[1],data.bounds_min[2])
	var mx:=Vector3(data.bounds_max[0],data.bounds_max[1],data.bounds_max[2])
	if mx.x<=mn.x or mx.y<=mn.y or mx.z<=mn.z:last_error="Invalid idle cache bounds.";return false
	physics_frames=loaded;cache_bounds=AABB(mn,mx-mn)
	fps=float(data.get("fps",data.get("sample_fps",12.0)))
	loop_duration=float(data.get("loop_duration_seconds",data.get("loop_duration",loaded.size()/fps)))
	if data.has("frame_times"):frame_times=PackedFloat32Array(data.frame_times)
	elif times.size()==loaded.size():frame_times=times
	else:
		frame_times=PackedFloat32Array()
		for index in range(loaded.size()):frame_times.append(index/fps)
	if frame_times.size()!=loaded.size() or loop_duration<=float(frame_times[-1]):
		last_error="Idle loop duration must include the last-frame-to-first-frame interval.";physics_frames.clear();return false
	density_scale=float(data.get("density_scale",1.0))
	var first:=loaded[0]
	cell_size=minf((mx.x-mn.x)/first.get_width(),minf((mx.y-mn.y)/first.get_height(),(mx.z-mn.z)/first.get_depth()))
	var yaw:=turntable.rotation.y
	var anchor:Transform3D=turntable.global_transform*Transform3D(Basis(Vector3.UP,-yaw),Vector3.ZERO)
	var radius:=Vector2(maxf(absf(mn.x),absf(mx.x)),maxf(absf(mn.z),absf(mx.z))).length()
	var warm:Dictionary={"active":true,"gain":1.0,"frame_a":loaded[0],"frame_b":loaded[mini(1,loaded.size()-1)],"mix":.5,
		"bounds_min":mn,"bounds_max":mx,"world_bounds":anchor*AABB(Vector3(-radius,mn.y,-radius),Vector3(radius*2,mx.y-mn.y,radius*2)),
		"world_to_anchor":anchor.affine_inverse(),"birth_angles":get_birth_angles(),"history_step":HISTORY_STEP,"current_angle":yaw,
		"step":cell_size*_step_multiplier,"max_steps":_max_steps,"resolution_scale":_resolution_scale,"density_scale":density_scale,
		"core_position":Vector3(0,2.2,0),"core_color":Color.WHITE,"core_energy":1.0,"core_range":2.8,"core_shadow_steps":3}
	compositor.request_prewarm(warm,loaded)
	last_error=""
	return true

func set_activity(amount:float)->void:
	activity_target=clampf(amount,0.0,1.0)

func set_quality(profile:String)->void:
	quality_profile=profile
	match profile:
		"high":_resolution_scale=.5;_max_steps=128;_step_multiplier=.68
		"performance":_resolution_scale=.3333333;_max_steps=96;_step_multiplier=1.0
		_:_resolution_scale=.4;_max_steps=96;_step_multiplier=.90

func _record_yaw(delta:float)->void:
	var old_time:=clock
	clock+=delta;_last_delta=delta
	var raw_yaw:=turntable.rotation.y
	var old_yaw:=_unwrapped_yaw
	_unwrapped_yaw+=wrapf(raw_yaw-_previous_raw_yaw,-PI,PI)
	_previous_raw_yaw=raw_yaw
	# Fixed 0.1s history, interpolated from actual frame poses. A pause writes
	# equal newest angles but leaves every older birth angle intact.
	if _next_history_time<clock-HISTORY_SPAN:_next_history_time=clock-HISTORY_SPAN
	while _next_history_time<=clock:
		var blend:=clampf((_next_history_time-old_time)/maxf(delta,.000001),0.0,1.0)
		history.append(PackedFloat64Array([_next_history_time,lerpf(old_yaw,_unwrapped_yaw,blend)]))
		_next_history_time+=HISTORY_STEP
	while history.size()>2 and history[1][0]<clock-HISTORY_SPAN-HISTORY_STEP:history.pop_front()

func _yaw_at_time(time:float)->float:
	if history.is_empty():return _unwrapped_yaw
	if time<=history[0][0]:return history[0][1]
	if time>=history[-1][0]:
		var span:=clock-history[-1][0]
		return lerpf(history[-1][1],_unwrapped_yaw,clampf((time-history[-1][0])/maxf(span,.000001),0.0,1.0))
	var lo:=0;var hi:=history.size()-1
	while hi-lo>1:
		var middle:=(lo+hi)/2
		if history[middle][0]<=time:lo=middle
		else:hi=middle
	return lerpf(history[lo][1],history[hi][1],inverse_lerp(history[lo][0],history[hi][0],time))

func get_birth_angles()->PackedFloat32Array:
	var result:=PackedFloat32Array()
	# Shift the entire continuous history by one common whole-turn offset.
	# This retains winding differences without long-running float32 precision loss.
	var current_wrapped:=wrapf(_unwrapped_yaw,-PI,PI)
	for index in range(HISTORY_COUNT):result.append(current_wrapped+_yaw_at_time(clock-index*HISTORY_STEP)-_unwrapped_yaw)
	return result

func tick(delta:float)->void:
	if host==null or turntable==null or compositor==null:return
	delta=maxf(0.0,delta)
	_record_yaw(delta)
	var power_value:Variant=host.get("power")
	var power:=clampf(float(power_value) if power_value!=null else 1.0,0.0,1.0)
	var power_target:Variant=host.get("power_target")
	var shutting_down:bool=(power_target!=null and float(power_target)<.01) or power<.001
	var explode_value:Variant=host.get("explosion")
	var exploded:=explode_value!=null and float(explode_value)>.02
	var desired:=activity_target*smoothstep(.02,.85,power)
	if shutting_down or exploded:desired=0.0
	if shutting_down or exploded or activity_target<.001:
		source_off_elapsed=maxf(0.0,source_off_elapsed)+delta
	else:source_off_elapsed=-1.0
	var fade_duration:=.8 if shutting_down else .20 if desired<gain else .65
	gain=move_toward(gain,desired,delta/maxf(.01,fade_duration))
	idle_active=gain>.001 and not physics_frames.is_empty()
	if not idle_active:
		compositor.configure({"active":false,"gain":0.0});return
	var phase:=fposmod(clock,loop_duration)
	var index:=0
	while index<physics_frames.size()-1 and phase>=frame_times[index+1]:index+=1
	var next_index:=(index+1)%physics_frames.size()
	var next_time:=loop_duration if next_index==0 else float(frame_times[next_index])
	var blend:=clampf(inverse_lerp(frame_times[index],next_time,phase),0.0,1.0)
	var yaw:=turntable.rotation.y
	var anchor_to_world:=turntable.global_transform*Transform3D(Basis(Vector3.UP,-yaw),Vector3.ZERO)
	var half_radius:=Vector2(maxf(absf(cache_bounds.position.x),absf(cache_bounds.end.x)),maxf(absf(cache_bounds.position.z),absf(cache_bounds.end.z))).length()
	var all_yaw_bounds:=AABB(Vector3(-half_radius,cache_bounds.position.y,-half_radius),Vector3(half_radius*2,cache_bounds.size.y,half_radius*2))
	var snapshot:Dictionary={
		"active":true,"gain":gain,"frame_a":physics_frames[index],"frame_b":physics_frames[next_index],"mix":blend,
		"source_off_elapsed":source_off_elapsed,
		"bounds_min":cache_bounds.position,"bounds_max":cache_bounds.end,"world_bounds":anchor_to_world*all_yaw_bounds,
		"world_to_anchor":anchor_to_world.affine_inverse(),"density_scale":density_scale,
		"birth_angles":get_birth_angles(),"history_step":HISTORY_STEP,"current_angle":wrapf(_unwrapped_yaw,-PI,PI),
		"step":cell_size*_step_multiplier,"max_steps":_max_steps,"resolution_scale":_resolution_scale,"core_shadow_steps":3,
		"lower_source":Vector4(.66,1.10,.085,.30),"valve_source":Vector4(.89,2.62,-.10,.62),"valve_flow":Vector4(.16,.22,.055,.25)}
	var effects:Variant=host.get("effects")
	if is_instance_valid(effects):
		var core:Variant=effects.get("core")
		if is_instance_valid(core):
			var bounce:Variant=core.get("bounce")
			if bounce is OmniLight3D:
				var open_value:Variant=host.get("openness")
				var openness:=float(open_value) if open_value!=null else 0.0
				var shell_transmission:=lerpf(.018,1.0,smoothstep(.025,.40,openness))
				snapshot.core_position=bounce.global_position;snapshot.core_color=bounce.light_color
				snapshot.core_energy=bounce.light_energy*shell_transmission;snapshot.core_range=bounce.omni_range
	compositor.configure(snapshot)

func get_diagnostics()->Dictionary:
	return {"idle_active":idle_active,"gain":gain,"time":clock,"history_samples":history.size(),"history_span":HISTORY_SPAN,"source_off_elapsed":source_off_elapsed,
		"unwrapped_yaw":_unwrapped_yaw,"birth_angles":get_birth_angles(),"frames":physics_frames.size(),"last_error":last_error,
		"compositor":compositor.get_diagnostics() if compositor!=null else {}}

func _exit_tree()->void:
	if host!=null and is_instance_valid(host):
		var camera:Camera3D=host.get("camera")
		if camera!=null and camera.compositor!=null:
			var effects:Array[CompositorEffect]=camera.compositor.compositor_effects.duplicate()
			effects.erase(compositor);camera.compositor.compositor_effects=effects
