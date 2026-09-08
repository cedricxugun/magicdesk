extends Node3D
## One continuous world-space density field. No billboards or stretching puffs.
## Toroidal impulse + six histories of world-advected interior steam.

var host:Node3D
var clock:=0.0
var volume:MeshInstance3D
var material:ShaderMaterial
var rings:Array[Dictionary]=[]
var streams:Array[Array]=[]
var hinges:Array[Node3D]=[]
var source_time:=-1.0
var source_strength:=1.0
var source_next:=.76
var rng:=RandomNumberGenerator.new()
var active_volume_count:=0
var peak_active_volumes:=0
var events:Array=[]
var particles:Array=[] # diagnostic compatibility; density is not represented by particles.
var physics_frames:Array[Texture3D]=[]
var physics_frame_bounds:Array[AABB]=[]
var physics_fps:=12.0
var physics_time:=-1.0
var physics_gain:=1.0
var physics_direction:=1.0
var physics_fade:=-1.0
var physics_fade_total:=.6
var physics_bounds:=AABB()
var physics_frame_times:Array=[]
var physics_time_offset:=0.0
var physics_cell_size:=.05
var quality_profile:="balanced"
var physics_pending:=""
var physics_pending_elapsed:=0.0
var physics_tail_fade:=.30
var compute_effect:CompositorEffect
var burst_active:=false
var idle_active:=false
var physics_playing:=false
var burst_latched:=false
var idle_controller:Node3D

func setup(owner:Node3D)->void:
	host=owner;rng.seed=194806
	for i in range(6):streams.append([]);hinges.append(host.named("PETAL_HINGE_%02d"%i))
	volume=MeshInstance3D.new();volume.name="ContinuousPressureField"
	var box:=BoxMesh.new();box.size=Vector3(6.8,3.9,6.8);volume.mesh=box
	volume.position=Vector3(0,1.95,0);volume.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	material=ShaderMaterial.new();material.shader=load("res://pressure_volume.gdshader")
	material.set_shader_parameter("curl_field",load("res://assets/pressure_curl_field.res"))
	material.set_shader_parameter("activity",0.0);volume.material_override=material;add_child(volume)
	if FileAccess.file_exists("res://assets/pressure_physics/manifest.json"):
		load_physics_manifest("res://assets/pressure_physics/manifest.json")
	_enable_idle_controller()
	# Visible with zero density at startup to precompile the pipeline.
	set_process(false)

func trigger(kind:String)->void:
	if host==null:return
	if not physics_frames.is_empty():
		_trigger_physics(kind);return
	match kind:
		"open":
			_cancel_sources(.45);source_time=0.0;source_next=.76;source_strength=1.0
			_add_ring(-.32,1.0,false)
		"ignition":_add_ring(-.08,.34,false)
		"close":_cancel_sources(.5);_add_ring(-.02,.63,true)
		"shutdown":_cancel_sources(.45);_add_ring(-.04,.76,true)
		"overload":
			_add_ring(-.02,.53,false)
			if float(host.openness)>.15:source_time=.74;source_next=.76;source_strength=.57
		"explode","cancel":_cancel_sources(.45)

func _add_ring(age:float,gain:float,inward:bool)->void:
	if rings.size()>=3:rings.pop_front()
	rings.append({"age":age,"gain":gain,"inward":inward,"fade":-1.0,"fade_duration":.45})

func _cancel_sources(duration:float)->void:
	source_time=-1.0
	for r in rings:r.fade=duration;r.fade_duration=duration
	for stream in streams:
		for p in stream:p.fade=duration;p.fade_duration=duration

func _radius(t:float)->float:
	var ts:=[0.0,.06,.16,.30,.47,.62,.76,.87,.95,1.0]
	var rs:=[.31,.43,.62,.78,.865,.84,.73,.565,.365,.17]
	for i in range(9):
		if t<=ts[i+1]:return lerpf(rs[i],rs[i+1],inverse_lerp(ts[i],ts[i+1],t))
	return .17

func _emit_streams()->void:
	if float(host.openness)<.018 or float(host.explosion)>.1:return
	for i in range(6):
		var h:=hinges[i]
		var t:=.20+.24*clampf((source_time-.76)/.78,0,1)
		var side:=sin(source_time*5.0+i)*.10
		var lp:=Vector3(_radius(t)-.31-.12,2.68*t,side)
		var tangent:=Vector3((_radius(t+.01)-_radius(t-.01))/.02,2.68,0).normalized()
		var wp:Vector3=h.global_transform*lp
		var radial:=Vector3(wp.x,0,wp.z).normalized()
		var circumferential:=Vector3(-radial.z,0,radial.x)
		var velocity:Vector3=h.global_basis*tangent*.58+Vector3(0,.14,0)+circumferential*.38
		streams[i].append({"pos":wp,"velocity":velocity,"local_birth":lp,"age":0.0,"life":2.15,"gain":source_strength,"fade":-1.0,"fade_duration":.45})

func _velocity_field(p:Vector3,t:float)->Vector3:
	# Each velocity component is independent of its own coordinate: div(v)=0.
	var a:=Vector3(sin(p.y*3.1+p.z*1.3+t*1.2),sin(p.z*2.7+p.x*1.5+t*.8),sin(p.x*2.9+p.y*1.7+t))*.23
	var b:=Vector3(sin(p.y*7.3+p.z*4.2-t*1.8),sin(p.z*6.7+p.x*3.6+t*1.4),sin(p.x*6.1+p.y*4.7-t))*.065
	return a+b

func tick(delta:float)->void:
	if host==null:return
	clock+=delta
	_sync_core_light()
	if not physics_frames.is_empty():
		_tick_physics(delta);_tick_idle(delta);return
	if source_time>=0:
		source_time+=delta
		while source_time>=source_next and source_next<=1.56:
			_emit_streams();source_next+=.08
		if source_time>1.60:source_time=-1.0
	var ring_data:=PackedVector4Array()
	var bounds_min:=Vector3.ONE*100.0;var bounds_max:=-Vector3.ONE*100.0
	var visible_rings:=0
	for i in range(rings.size()-1,-1,-1):
		var r:Dictionary=rings[i];r.age+=delta
		if float(r.fade)>=0:r.fade-=delta
		if float(r.age)>(1.0 if bool(r.inward) else 2.10) or (float(r.fade)<0 and float(r.fade)>-delta*1.1):rings.remove_at(i);continue
		var fade:=1.0 if float(r.fade)<0 else smoothstep(0.0,float(r.fade_duration),float(r.fade))
		ring_data.append(Vector4(r.age,float(r.gain)*fade,1.0 if bool(r.inward) else 0.0,float(i)*7.31))
		if float(r.age)>=0:
			visible_rings+=1
			var radius:=.96 if bool(r.inward) else .52+1.30*(1.0-exp(-float(r.age)*3.4))
			var ext:=radius+.75
			bounds_min=bounds_min.min(Vector3(-ext,.55,-ext));bounds_max=bounds_max.max(Vector3(ext,1.12+float(r.age)*.57+.72,ext))
	var ring_count:=ring_data.size()
	while ring_data.size()<3:ring_data.append(Vector4(-9,0,0,0))
	var point_data:=PackedVector4Array();var lower:=PackedVector4Array();var upper:=PackedVector4Array()
	var live_streams:=0
	for i in range(6):
		var stream:Array=streams[i]
		for k in range(stream.size()-1,-1,-1):
			var p:Dictionary=stream[k];p.age+=delta
			if float(p.fade)>=0:p.fade-=delta
			if float(p.age)>float(p.life) or (float(p.fade)<0 and float(p.fade)>-delta*1.1):stream.remove_at(k);continue
			var drift:Vector3=p.velocity*exp(-float(p.age)*.62)+Vector3(0,.14+float(p.age)*.13,0)
			var v1:=drift+_velocity_field(p.pos,clock)
			var vm:=drift+_velocity_field(p.pos+v1*delta*.5,clock+delta*.5)
			p.pos+=vm*delta
			if float(p.age)<.13:
				var attachment:Vector3=hinges[i].global_transform*p.local_birth
				p.pos=p.pos.lerp(attachment,.12*(1.0-float(p.age)/.13))
		if stream.size()<2:
			for k in range(4):point_data.append(Vector4.ZERO)
			lower.append(Vector4(0,0,0,0));upper.append(Vector4(0,0,0,0));continue
		live_streams+=1
		var mn:=Vector3.ONE*100;var mx:=-Vector3.ONE*100;var strength:=0.0
		for k in range(4):
			var ix:=int(round(float(k)*(stream.size()-1)/3.0));var p:Dictionary=stream[ix]
			var pos:Vector3=p.pos;var radius:=.075+.19*(1.0-exp(-float(p.age)*2.3))
			point_data.append(Vector4(pos.x,pos.y,pos.z,radius))
			mn=mn.min(pos-Vector3.ONE*(radius+.20));mx=mx.max(pos+Vector3.ONE*(radius+.20))
			var fade:=1.0 if float(p.fade)<0 else smoothstep(0.0,float(p.fade_duration),float(p.fade))
			strength+=float(p.gain)*fade*(1.0-smoothstep(.45,2.15,float(p.age)))
		lower.append(Vector4(mn.x,mn.y,mn.z,strength*.25));upper.append(Vector4(mx.x,mx.y,mx.z,0))
		bounds_min=bounds_min.min(mn);bounds_max=bounds_max.max(mx)
	material.set_shader_parameter("ring_data",ring_data)
	material.set_shader_parameter("ring_count",ring_count)
	material.set_shader_parameter("stream_points",point_data)
	material.set_shader_parameter("stream_lower",lower)
	material.set_shader_parameter("stream_upper",upper)
	material.set_shader_parameter("flow_time",clock)
	material.set_shader_parameter("core_position",host.named("P_Solar_Crystal").global_position)
	active_volume_count=1 if visible_rings>0 or live_streams>0 else 0
	material.set_shader_parameter("bounds_lower",bounds_min)
	material.set_shader_parameter("bounds_upper",bounds_max)
	peak_active_volumes=maxi(peak_active_volumes,active_volume_count)
	material.set_shader_parameter("activity",float(active_volume_count))
	events.clear()
	if source_time>=0:events.append(source_time)
	_tick_idle(delta)

func _enable_idle_controller()->void:
	if idle_controller!=null or not FileAccess.file_exists("res://assets/idle_steam_loop/manifest.json"):return
	var node:Node3D=load("res://idle_steam_vfx.gd").new()
	add_child(node);node.setup(host)
	if not node.load_manifest("res://assets/idle_steam_loop/manifest.json"):
		push_error("Idle physical steam could not load: "+str(node.last_error));node.queue_free();return
	idle_controller=node;idle_controller.set_quality(quality_profile)

func _tick_idle(delta:float)->void:
	if idle_controller==null:return
	idle_controller.set_activity(0.0 if is_burst_active() or not physics_pending.is_empty() else 1.0)
	idle_controller.tick(delta);idle_active=idle_controller.idle_active

func is_burst_active()->bool:
	return burst_active if not physics_frames.is_empty() else active_volume_count>0

func is_idle_active()->bool:return idle_active

func _sync_core_light()->void:
	var energy:=0.0;var color:=Color.WHITE;var radius:=1.0
	var position:Vector3=host.named("P_Solar_Crystal").global_position
	var effect_node=host.get("effects")
	if is_instance_valid(effect_node):
		var core_node=effect_node.get("core")
		if is_instance_valid(core_node):
			var bounce=core_node.get("bounce")
			if bounce is OmniLight3D:
				position=bounce.global_position;color=bounce.light_color
				energy=maxf(0.0,bounce.light_energy);radius=maxf(.01,bounce.omni_range)
	# An intact opaque shell transmits only the very small inspection-window leak.
	var shell_transmission:=lerpf(.018,1.0,smoothstep(.025,.40,float(host.openness)))
	material.set_shader_parameter("core_light_position",position)
	material.set_shader_parameter("core_light_color",color)
	material.set_shader_parameter("core_light_energy",energy*shell_transmission)
	material.set_shader_parameter("core_light_range",radius)

func load_physics_manifest(path:String)->bool:
	var data=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Dictionary or not data.has("frames"):return false
	var loaded:Array[Texture3D]=[]
	for frame_path in data.frames:
		var resolved:String=str(frame_path)
		if not resolved.begins_with("res://") and not resolved.is_absolute_path():resolved=path.get_base_dir().path_join(resolved)
		var texture=load(resolved)
		if not texture is Texture3D:return false
		loaded.append(texture)
	if loaded.is_empty():return false
	physics_frames=loaded;physics_fps=float(data.get("fps",12.0))
	physics_frame_times=data.get("frame_times",[]);physics_time_offset=float(data.get("time_offset",0.0))
	var mn:=Vector3(data.bounds_min[0],data.bounds_min[1],data.bounds_min[2])
	var mx:=Vector3(data.bounds_max[0],data.bounds_max[1],data.bounds_max[2])
	physics_bounds=AABB(mn,mx-mn);physics_frame_bounds.clear()
	for bounds in data.get("frame_bounds",[]):
		var a:=Vector3(bounds[0][0],bounds[0][1],bounds[0][2]);var b:=Vector3(bounds[1][0],bounds[1][1],bounds[1][2])
		physics_frame_bounds.append(AABB(a,b-a))
	var box:=volume.mesh as BoxMesh;box.size=(mx-mn)+Vector3.ONE*.06;volume.position=(mx+mn)*.5
	material.set_shader_parameter("physical_enabled",true)
	material.set_shader_parameter("physical_bounds_min",mn)
	material.set_shader_parameter("physical_bounds_max",mx)
	material.set_shader_parameter("physical_density_scale",float(data.get("density_scale",1.0)))
	var resolution=data.resolution
	var cell:=minf((mx.x-mn.x)/float(resolution[0]),minf((mx.y-mn.y)/float(resolution[1]),(mx.z-mn.z)/float(resolution[2])))
	material.set_shader_parameter("physical_step",cell*.50)
	physics_cell_size=cell;set_quality(quality_profile)
	material.set_shader_parameter("physical_occupancy_enabled",false)
	if data.has("occupancy"):
		var occ_path:String=str(data.occupancy)
		if not occ_path.begins_with("res://") and not occ_path.is_absolute_path():occ_path=path.get_base_dir().path_join(occ_path)
		material.set_shader_parameter("physical_occupancy",load(occ_path))
		var r=data.occupancy_resolution
		material.set_shader_parameter("physical_occupancy_size",Vector3(r[0],r[1],r[2]))
		material.set_shader_parameter("physical_occupancy_enabled",true)
	material.set_shader_parameter("density_frame_a",physics_frames[0]);material.set_shader_parameter("density_frame_b",physics_frames[0])
	material.set_shader_parameter("physical_gain",0.0)
	_enable_compute_renderer()
	print("PRESSURE_PHYSICS_CACHE_LOADED ",physics_frames.size()," frames ",resolution)
	return true

func _enable_compute_renderer()->void:
	if compute_effect!=null:return
	var camera=host.get("camera")
	if not camera is Camera3D:return
	compute_effect=load("res://steam_compositor.gd").new()
	var compositor:Compositor=camera.compositor
	if compositor==null:compositor=Compositor.new();camera.compositor=compositor
	var effects:Array[CompositorEffect]=compositor.compositor_effects
	effects.append(compute_effect);compositor.compositor_effects=effects
	volume.hide()
	var frame:=mini(16,physics_frames.size()-1)
	var transform:Transform3D=host.named("TURNTABLE").global_transform
	var warm:Dictionary={"active":true,"frame_a":physics_frames[frame],"frame_b":physics_frames[mini(frame+1,physics_frames.size()-1)],
		"mix":.5,"gain":1.0,"bounds_min":physics_bounds.position,"bounds_max":physics_bounds.end,"world_bounds":transform*physics_bounds,
		"cache_to_world":transform,"density_scale":material.get_shader_parameter("physical_density_scale"),
		"step":material.get_shader_parameter("physical_step"),"max_steps":material.get_shader_parameter("max_march_steps"),"resolution_scale":.5,
		"core_position":Vector3(0,2.2,0),"core_color":Color(1,.1,.04),"core_energy":1.0,"core_range":2.8,"core_shadow_steps":3}
	if bool(material.get_shader_parameter("physical_occupancy_enabled")):
		warm.occupancy=material.get_shader_parameter("physical_occupancy");warm.occupancy_size=material.get_shader_parameter("physical_occupancy_size")
	compute_effect.request_prewarm(warm,physics_frames)

func _configure_compute(cache_to_world:Transform3D,world_bounds:AABB)->void:
	if compute_effect==null:return
	var snapshot:Dictionary={"active":active_volume_count>0,
		"frame_a":material.get_shader_parameter("density_frame_a"),"frame_b":material.get_shader_parameter("density_frame_b"),
		"mix":material.get_shader_parameter("physical_mix"),"gain":material.get_shader_parameter("physical_gain"),
		"bounds_min":physics_bounds.position,"bounds_max":physics_bounds.end,"world_bounds":world_bounds,"cache_to_world":cache_to_world,
		"density_scale":material.get_shader_parameter("physical_density_scale"),"step":material.get_shader_parameter("physical_step"),
		"max_steps":material.get_shader_parameter("max_march_steps"),"resolution_scale":.5,
		"core_position":material.get_shader_parameter("core_light_position"),"core_color":material.get_shader_parameter("core_light_color"),
		"core_energy":material.get_shader_parameter("core_light_energy"),"core_range":material.get_shader_parameter("core_light_range"),
		"core_shadow_steps":material.get_shader_parameter("core_shadow_steps")}
	if bool(material.get_shader_parameter("physical_occupancy_enabled")):
		snapshot.occupancy=material.get_shader_parameter("physical_occupancy")
		snapshot.occupancy_size=material.get_shader_parameter("physical_occupancy_size")
	compute_effect.configure(snapshot)

func set_quality(profile:String)->void:
	quality_profile=profile
	if idle_controller!=null:idle_controller.set_quality(profile)
	if material==null:return
	match profile:
		"high":
			material.set_shader_parameter("max_march_steps",192)
			material.set_shader_parameter("physical_step",physics_cell_size*.48)
			material.set_shader_parameter("core_shadow_steps",4)
		"performance":
			material.set_shader_parameter("max_march_steps",96)
			material.set_shader_parameter("physical_step",physics_cell_size*.90)
			material.set_shader_parameter("core_shadow_steps",3)
		_:
			material.set_shader_parameter("max_march_steps",128)
			material.set_shader_parameter("physical_step",physics_cell_size*.68)
			material.set_shader_parameter("core_shadow_steps",3)

func _trigger_physics(kind:String)->void:
	var maximum:float=(physics_frames.size()-1)/physics_fps
	if not physics_frame_times.is_empty():maximum=float(physics_frame_times[-1])
	var already_releasing:=physics_playing and physics_time>=.25 and physics_time<maximum-.20 and physics_fade!=0.0
	match kind:
		"open":
			# The ground-impact release belongs only to a fresh closed-shell unlock.
			if burst_latched or float(host.openness)>.045 or float(host.explosion)>.015:return
			burst_latched=true
			if already_releasing:
				physics_pending=kind;physics_pending_elapsed=0.0
				physics_fade=.20;physics_fade_total=.20
				return
			physics_pending=""
			physics_playing=true
			physics_time=physics_time_offset
			physics_gain=1.0
			physics_direction=1.0;physics_fade=-1.0
		"ignition","overload":
			# Idle/core feedback owns these actions; never replay the ground burst.
			pass
		"close","shutdown","assemble":
			burst_latched=false
			physics_pending=""
			if physics_playing:physics_direction=1.0;physics_fade=.70;physics_fade_total=.70
		"explode","cancel":
			physics_pending=""
			if physics_playing:physics_fade=.45;physics_fade_total=.45

func _tick_physics(delta:float)->void:
	if physics_playing:physics_time+=delta*physics_direction
	if not physics_pending.is_empty():physics_pending_elapsed+=delta
	if physics_fade>=0:physics_fade=maxf(0,physics_fade-delta)
	if physics_fade==0.0 and not physics_pending.is_empty():
		physics_time=physics_pending_elapsed+physics_time_offset
		physics_gain=1.0;physics_direction=1.0;physics_fade=-1.0;physics_pending=""
	var maximum:float=(physics_frames.size()-1)/physics_fps
	if physics_frame_times.size()==physics_frames.size():maximum=float(physics_frame_times[-1])
	var active:=physics_playing and physics_time>=0.0 and physics_time<=maximum and physics_fade!=0.0
	if physics_time>maximum or physics_fade==0.0:physics_playing=false
	var sample:=clampf(physics_time*physics_fps,0,physics_frames.size()-1)
	if physics_frame_times.size()==physics_frames.size():
		var index:=0
		while index<physics_frame_times.size()-2 and physics_time>float(physics_frame_times[index+1]):index+=1
		sample=index+clampf(inverse_lerp(float(physics_frame_times[index]),float(physics_frame_times[mini(index+1,physics_frame_times.size()-1)]),physics_time),0,1)
	var lo:=int(sample);var hi:=mini(lo+1,physics_frames.size()-1)
	material.set_shader_parameter("density_frame_a",physics_frames[lo]);material.set_shader_parameter("density_frame_b",physics_frames[hi])
	material.set_shader_parameter("physical_mix",sample-lo)
	var fade:=1.0 if physics_fade<0 else smoothstep(0.0,physics_fade_total,physics_fade)
	# A short terminal fade is only a guard against the finite sampled sequence.
	# The producer simulates the actual dissipation; no density is reversed.
	if physics_tail_fade>0:fade*=1.0-smoothstep(maxf(0.0,maximum-physics_tail_fade),maximum,physics_time)
	material.set_shader_parameter("physical_gain",physics_gain*fade if active else 0.0)
	var bounds:=physics_bounds
	if physics_frame_bounds.size()==physics_frames.size():bounds=physics_frame_bounds[lo].merge(physics_frame_bounds[hi]).grow(.04)
	var cache_to_world:Transform3D=host.named("TURNTABLE").global_transform
	volume.global_transform=cache_to_world*Transform3D(Basis.IDENTITY,physics_bounds.get_center())
	var world_bounds:AABB=cache_to_world*bounds
	material.set_shader_parameter("world_to_physical",cache_to_world.affine_inverse())
	material.set_shader_parameter("bounds_lower",world_bounds.position);material.set_shader_parameter("bounds_upper",world_bounds.end)
	material.set_shader_parameter("core_position",host.named("P_Solar_Crystal").global_position)
	material.set_shader_parameter("activity",1.0 if active else 0.0)
	active_volume_count=1 if active else 0;peak_active_volumes=maxi(peak_active_volumes,active_volume_count)
	burst_active=active
	_configure_compute(cache_to_world,world_bounds)
	events.clear()
	if active:events.append(physics_time)
