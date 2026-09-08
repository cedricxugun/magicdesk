extends Node3D

var host:Node3D
var crystal:Node3D
var lift:Node3D
var middle_axle:Node3D
var inner_axle:Node3D
var time:=0.0
var reveal_time:=-1.0
var open_time:=-1.0
var reveal_pending:=false
var settle_time:=-1.0
var last_display_time:=-1.0
var thermal_phase:=0.0
var next_overload_arc:=.18
var ignition_time:=-1.0
var overload_time:=-1.0
var shutdown_time:=-1.0
var last_open:=0.0
var reveal_events:=0
var next_idle_arc:=7.2
var surface_material:ShaderMaterial
var filament_material:ShaderMaterial
var corona:MeshInstance3D
var corona_material:ShaderMaterial
var bounce:OmniLight3D
var arc_light:OmniLight3D
var arc_instance:MeshInstance3D
var arc_contact:MeshInstance3D
var arc_mesh:=ArrayMesh.new()
var lightning_material:ShaderMaterial
var lower_bearing:Node3D
var support_post:Node3D
var pedestal:Node3D
var orbit_particles:Node3D
var terminals:Array[Node3D]=[]
var terminal_contacts:Array[Vector3]=[]
var arc_material:StandardMaterial3D
var arc_segments:Array=[]
var random:=RandomNumberGenerator.new()
var active_arc_age:=0.0
var active_arc_life:=0.0
var active_endpoint:=0
var active_branch:=false
var arc_seed:=0.0
var warm_ticks:=3
var arc_is_overload:=false

func setup(owner_node:Node3D)->void:
	host=owner_node
	crystal=host.named("P_Solar_Crystal")
	lift=host.named("CORE_LIFT")
	middle_axle=host.named("P_Middle_Trunnions")
	inner_axle=host.named("P_Inner_Trunnions")
	lower_bearing=host.named("P_Core_Bottom_Bearing")
	support_post=host.named("P_Core_Support_Post")
	var mechanism:Variant=host.get("metadata")
	var contacts:Dictionary=mechanism.get("electrical_contacts",{}) if mechanism is Dictionary else {}
	for name in ["Thermal_Valve_Frame","Thermal_Valve_Frame.001","Thermal_Valve_Frame.002"]:
		terminals.append(host.named(name))
		var point:Array=contacts.get(name,[0,.59,0])
		terminal_contacts.append(Vector3(point[0],point[1],point[2]))
	random.seed=19551107
	surface_material=ShaderMaterial.new()
	surface_material.shader=load("res://core_surface.gdshader")
	surface_material.set_shader_parameter("plasma_art",load("res://assets/core_plasma.png"))
	filament_material=ShaderMaterial.new()
	filament_material.shader=surface_material.shader
	filament_material.set_shader_parameter("filament",1.0)
	_replace_materials(host.model)
	corona=MeshInstance3D.new()
	var quad:=QuadMesh.new();quad.size=Vector2(1.32,1.32)
	corona.mesh=quad
	corona_material=ShaderMaterial.new();corona_material.shader=load("res://core_corona.gdshader")
	corona.material_override=corona_material
	corona.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(corona)
	bounce=OmniLight3D.new();add_child(bounce)
	bounce.light_color=Color(1.0,0.025,0.010)
	bounce.omni_range=2.20
	bounce.omni_attenuation=1.5
	bounce.light_size=.16
	bounce.shadow_enabled=true
	bounce.shadow_normal_bias=.08
	bounce.shadow_bias=.08
	bounce.light_energy=0.0
	arc_light=OmniLight3D.new();add_child(arc_light)
	arc_light.light_color=Color(1.0,.24,.16)
	arc_light.omni_range=.34
	arc_light.light_energy=0.0
	arc_material=StandardMaterial3D.new()
	arc_material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	arc_material.albedo_color=Color(1,.64,.48)
	arc_material.emission_enabled=true
	arc_material.emission=Color(1,.42,.27)
	arc_material.emission_energy_multiplier=6.5
	arc_instance=MeshInstance3D.new()
	_build_lightning_topology()
	arc_instance.mesh=arc_mesh
	lightning_material=ShaderMaterial.new();lightning_material.shader=load("res://core_beam.gdshader")
	lightning_material.set_shader_parameter("beam_art",load("res://assets/lightning_beam.png"))
	arc_instance.material_override=lightning_material
	arc_instance.custom_aabb=AABB(Vector3(-2,-1,-2),Vector3(4,5,4))
	arc_instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(arc_instance)
	arc_contact=MeshInstance3D.new()
	var contact_mesh:=SphereMesh.new();contact_mesh.radius=.019;contact_mesh.height=.038
	contact_mesh.radial_segments=12;contact_mesh.rings=6
	arc_contact.mesh=contact_mesh;arc_contact.material_override=arc_material
	arc_contact.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(arc_contact);arc_contact.hide()
	pedestal=Node3D.new();pedestal.set_script(load("res://core_pedestal_vfx.gd"));add_child(pedestal);pedestal.setup(host)
	orbit_particles=Node3D.new();orbit_particles.set_script(load("res://orbit_particles.gd"));add_child(orbit_particles);orbit_particles.setup(host)
	tick(0.0)

func _replace_materials(node:Node)->void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var mat=node.get_active_material(i)
			if mat is StandardMaterial3D:
				if mat.resource_name.contains("Solar_Core_Emission"):
					node.set_surface_override_material(i,surface_material)
				elif mat.resource_name.contains("Amber_Light"):
					node.set_surface_override_material(i,filament_material)
	for child in node.get_children():_replace_materials(child)

func trigger(kind:String)->void:
	if pedestal:pedestal.trigger(kind)
	if orbit_particles:orbit_particles.trigger(kind)
	match kind:
		"ignition":ignition_time=0.0;shutdown_time=-1.0
		"open":open_time=0.0;reveal_time=-1.0;settle_time=-1.0;reveal_pending=true;reveal_events=0;shutdown_time=-1.0
		"close", "explode", "cancel", "assemble":
			open_time=-1.0;reveal_time=-1.0;reveal_pending=false;settle_time=-1.0;overload_time=-1.0;active_arc_life=0.0
		"overload":overload_time=0.0;next_overload_arc=.80;shutdown_time=-1.0
		"shutdown":shutdown_time=0.0;open_time=-1.0;reveal_time=-1.0;reveal_pending=false;overload_time=-1.0;active_arc_life=0.0

func _envelope(age:float,duration:float)->float:
	if age<0.0 or age>duration:return 0.0
	var attack:=smoothstep(0.0,.22,age)
	var release:=1.0-smoothstep(duration*.35,duration,age)
	return attack*release

func tick(delta:float)->void:
	if crystal==null:return
	# The mechanism passes warped simulation time. Visible electrical contacts
	# retain their readable display duration while their trigger follows openness.
	var display_value:Variant=host.get("activation_display_time")
	if display_value!=null and float(display_value)>=0.0:
		var display_time:=float(display_value)
		if last_display_time>=0.0 and display_time>last_display_time:
			delta=minf(display_time-last_display_time,.10)
		last_display_time=display_time
	else:last_display_time=-1.0
	time+=delta
	if ignition_time>=0:ignition_time+=delta
	if open_time>=0:open_time+=delta
	if reveal_time>=0:reveal_time+=delta
	# One clock owns the seven-second mechanical and visual overload. Never let
	# warped opening time or a shorter local envelope move its peak forward.
	var overload_left:=clampf(float(host.get("overload")),0.0,7.0)
	if overload_time>=0.0:
		overload_time=7.0-overload_left if overload_left>0.0 else -1.0
	if shutdown_time>=0:shutdown_time+=delta
	var opened:=clampf(float(host.openness),0.0,1.0)
	if reveal_pending and opened>.45:
		reveal_pending=false;reveal_time=0.0;settle_time=-1.0
	if reveal_time>=0.0 and opened>=.985 and settle_time<0.0:settle_time=0.0
	if settle_time>=0.0:settle_time+=delta
	var assembled:=1.0-smoothstep(.03,.48,float(host.explosion))
	var power:=clampf(float(host.power),0.0,1.0)
	var shutdown_fade:=1.0
	if shutdown_time>=0.0:shutdown_fade=1.0-smoothstep(.08,1.8,shutdown_time)
	var heat:=power*shutdown_fade
	var reveal:=0.0
	if reveal_time>=0.0:
		reveal=smoothstep(.45,.72,opened)*(1.0-smoothstep(.30,1.25,maxf(0.0,settle_time)))
	var overload:=pow(sin(overload_left/7.0*PI),2.0) if overload_left>0.0 and shutdown_time<0.0 else 0.0
	var ignition:=_envelope(ignition_time,1.6)
	var charge:=_envelope(open_time,.80)
	var breath:=.94+.09*sin(time*1.80)+.025*sin(time*.73+1.6)
	var surge:=maxf(reveal,overload*1.35)*assembled
	thermal_phase+=delta*(.65+reveal*.9+overload*1.55)
	surface_material.set_shader_parameter("heat",heat*breath*(.8+.2*assembled))
	surface_material.set_shader_parameter("surge",surge)
	surface_material.set_shader_parameter("flow_time",thermal_phase)
	filament_material.set_shader_parameter("heat",heat*(.62+.38*maxf(ignition,charge)))
	filament_material.set_shader_parameter("surge",maxf(maxf(ignition,charge)*.35,overload*.55))
	filament_material.set_shader_parameter("flow_time",thermal_phase)
	var core_position:Vector3=crystal.global_position
	corona.global_position=core_position
	corona.visible=opened>.07 and heat>.008 and assembled>.05
	corona_material.set_shader_parameter("opacity",heat*assembled*smoothstep(.28,.65,opened)*(.18+reveal*.24+overload*.26))
	corona_material.set_shader_parameter("flow_time",thermal_phase)
	corona_material.set_shader_parameter("surge",surge)
	bounce.global_position=core_position
	bounce.light_energy=heat*assembled*smoothstep(.28,.70,opened)*(.65+reveal*2.6+overload*3.4)*breath
	# Only the brief release illuminates the petal interiors strongly. The settled
	# core retains a small warm reflection, leaving the ivory and nickel neutral.
	bounce.omni_range=2.20+maxf(reveal*.55,overload*.60)
	if opened>.45 and assembled>.9 and heat>.15 and shutdown_time<0.0:
		if reveal_time>=0 and reveal_events==0 and opened>.65:
			_start_arc(1,1.10)
			reveal_events=1
		if overload_time>=.80 and overload_time<6.05 and active_arc_life<=0.0 and overload_time>=next_overload_arc:
			var duration:=.36 if overload_time<1.55 else .56+overload*.44
			_start_arc(random.randi_range(0,3),duration,true)
			next_overload_arc=overload_time+duration+lerpf(.30,.025,overload)
		if settle_time>1.3 and overload<=.01 and time>next_idle_arc and active_arc_life<=0.0:
			_start_arc(random.randi_range(0,3),.36)
			next_idle_arc=time+random.randf_range(3.8,6.0)
	if arc_is_overload and overload_left<=0.0:active_arc_life=0.0
	_update_arc(delta,heat*assembled*(lerpf(.16,1.0,overload) if arc_is_overload else 1.0))
	if pedestal:pedestal.tick(delta)
	if orbit_particles:orbit_particles.tick(delta)
	last_open=opened

func _start_arc(endpoint:int,duration:float,from_overload:bool=false)->void:
	active_endpoint=endpoint;active_arc_age=0.0;active_arc_life=duration
	arc_is_overload=from_overload
	active_branch=from_overload
	arc_seed=random.randf_range(0,1000)

func _bearing_endpoint(index:int)->Vector3:
	# These coordinates lie on the actual middle and inner trunnion shafts.
	if index<2 and middle_axle!=null:
		return middle_axle.global_transform*Vector3(.625 if index==0 else -.625,0,0)
	if inner_axle!=null:
		return inner_axle.global_transform*Vector3(0,.465 if index==2 else -.465,0)
	return crystal.global_position+Vector3(0,-.465,0)

func _build_lightning_topology()->void:
	var vertices:=PackedVector3Array();var colors:=PackedColorArray();var uv:=PackedVector2Array();var indices:=PackedInt32Array()
	for channel in range(9):
		var base:=vertices.size()
		for segment in range(25):
			for side in range(2):
				vertices.append(Vector3.ZERO);uv.append(Vector2(float(segment)/24.0,float(side)));colors.append(Color(float(channel)/10.0,0,0,1))
		for segment in range(24):
			var a:=base+segment*2;var b:=a+2
			indices.append_array(PackedInt32Array([a,b,b+1,a,b+1,a+1]))
	var arrays:=[];arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_COLOR]=colors;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
	arc_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)

func _main_arc_point(t:float,a:Vector3,b:Vector3,bow:Vector3,_seed:float)->Vector3:
	return a.lerp(b,t)+sin(t*PI)*bow

func _update_arc(delta:float,intensity:float)->void:
	arc_light.light_energy=0.0;arc_contact.hide()
	active_arc_age+=delta
	if active_arc_age>active_arc_life or intensity<.02:active_arc_life=0.0
	var life_factor:=0.0
	if active_arc_life>0.0:
		life_factor=smoothstep(0.0,.035,active_arc_age)*(1.0-smoothstep(active_arc_life-.09,active_arc_life,active_arc_age))*intensity
	var center:Vector3=crystal.global_position
	var endpoints:Array[Vector3]=[_bearing_endpoint(0),_bearing_endpoint(1),center+Vector3(0,-.70,0),center+Vector3(0,-.86,0)]
	if lower_bearing:endpoints[2]=lower_bearing.global_transform*Vector3(0,-.70,0)
	if support_post:endpoints[3]=support_post.global_transform*Vector3(0,.19,0)
	var starts:=PackedVector4Array();var ends:=PackedVector4Array();var bows:=PackedVector4Array()
	var active_channels:=4 if active_arc_life>.5 else 1
	for channel in range(4):
		var endpoint:Vector3=endpoints[channel]
		var a:Vector3=to_local(center+(endpoint-center).normalized()*.255)
		var b:Vector3=to_local(endpoint)
		var bow:Vector3=Vector3((-.10 if channel%2==0 else .10),.03,.10)
		var seed:=arc_seed+float(channel)*3.71
		starts.append(Vector4(a.x,a.y,a.z,1.0 if channel<active_channels else 0.0))
		ends.append(Vector4(b.x,b.y,b.z,0))
		bows.append(Vector4(bow.x,bow.y,bow.z,seed))
	for channel in range(2):
		var base:=channel
		var a:Vector3=_main_arc_point(.47,Vector3(starts[base].x,starts[base].y,starts[base].z),Vector3(ends[base].x,ends[base].y,ends[base].z),Vector3(bows[base].x,bows[base].y,bows[base].z),bows[base].w)
		var b:Vector3=to_local(_bearing_endpoint(2+channel))
		starts.append(Vector4(a.x,a.y,a.z,.75 if active_channels>1 else 0.0));ends.append(Vector4(b.x,b.y,b.z,0));bows.append(Vector4(-.03,.025,.04,arc_seed+21.0+channel))
	# Long secondary discharge follows the real high-voltage anodes. These paths
	# span the open chamber instead of hiding all electricity inside the gyroscope.
	for channel in range(3):
		var origin:Vector3=endpoints[2] if channel!=1 else endpoints[3]
		var target:Vector3=center+Vector3(.85 if channel==0 else -.58,0,0)
		if terminals[channel]!=null:target=terminals[channel].global_transform*terminal_contacts[channel]
		var a:Vector3=to_local(origin)
		var b:Vector3=to_local(target)
		starts.append(Vector4(a.x,a.y,a.z,1.0 if active_channels>1 else 0.0));ends.append(Vector4(b.x,b.y,b.z,0))
		bows.append(Vector4(.12 if channel==0 else -.12,.06,.13,arc_seed+41.0+channel))
	lightning_material.set_shader_parameter("arc_start",starts)
	lightning_material.set_shader_parameter("arc_end",ends)
	lightning_material.set_shader_parameter("arc_bow",bows)
	lightning_material.set_shader_parameter("live",life_factor)
	lightning_material.set_shader_parameter("pulse_time",active_arc_age)
	# Topology and both transparent layers stay resident even with live=0.
	arc_instance.visible=true
	if life_factor>.02:
		arc_light.global_position=endpoints[2];arc_light.omni_range=.48;arc_light.light_energy=.85*life_factor
		arc_contact.global_position=endpoints[2];arc_contact.scale=Vector3.ONE*(.7+.3*sin(active_arc_age*17.0));arc_contact.show()
