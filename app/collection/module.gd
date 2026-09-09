extends Node3D
## A Blender-authored upper assembly. It never owns a base or window.

var host: Node3D
var data: Dictionary
var asset: Node3D
var parts: Array = []
var controls: Array = []
var motions: Array = []
var bodies: Array[StaticBody3D] = []
var materials: Array[ShaderMaterial] = []
var material_cache:Dictionary={}
var emissive_materials:Array[ShaderMaterial]=[]
var meshes: Array[MeshInstance3D] = []
var effect: Node3D
var openness := 0.0
var explosion := 0.0
var open_target := 0.0
var explode_target := 0.0
var power := 1.0
var phase := 0.0
var burst := 0.0
var pending_burst := false
var clock := 0.0
var scan := 0.0
var bounds := AABB()
var stowing := false
var interactive:=true
var play:RefCounted
var interactive_rig:Array=[]
var yaw_velocity:=0.0
var instrument_materials:Array[ShaderMaterial]=[]

func v3(v:Array)->Vector3:return Vector3(v[0],v[1],v[2])

func pose(p:Dictionary)->Transform3D:
	return Transform3D(Basis(Quaternion(p.q[0],p.q[1],p.q[2],p.q[3]))*Basis.from_scale(v3(p.s)),v3(p.p))

func named(label:String)->Node3D:return asset.find_child(label,true,false) as Node3D

func setup(owner:Node3D,definition:Dictionary,packed:PackedScene)->void:
	host=owner;data=definition
	play=load("res://collection/play_state.gd").new();play.setup(self)
	asset=packed.instantiate();add_child(asset)
	for p in data.parts:
		var node:=named(p.name)
		assert(node!=null,"Missing collection part "+str(p.name))
		parts.append({"node":node,"home":pose(p.home),"offset":v3(p.offset),"stage":float(p.stage),"route":p.get("route",[])})
	for c in data.controls:
		var samples:Array[Transform3D]=[]
		for sample in c.samples:samples.append(pose(sample))
		controls.append({"node":named(c.name),"samples":samples})
	for m in data.motions:motions.append({"node":named(m.name),"home":named(m.name).transform,"axis":m.axis,"speed":float(m.speed),"amplitude":float(m.amplitude),"phase":float(m.phase),"pose":Quaternion.IDENTITY})
	for item in data.get("interactive_rig",[]):interactive_rig.append({"node":named(item.name),"kind":str(item.kind),"home":pose(item.home)})
	_collect(asset)
	apply_pose()
	bounds=_bounds()
	effect=load("res://collection/effects.gd").new();add_child(effect);effect.setup(self)

func _collect(node:Node)->void:
	if node is MeshInstance3D:
		meshes.append(node)
		var body:=StaticBody3D.new();body.collision_layer=4;body.collision_mask=0
		var shape:=CollisionShape3D.new()
		if play.instrument or play.g_instrument:
			# These shapes serve pointer picking, not mechanism dynamics. Avoid
			# cooking hundreds of thousands of detail triangles on first select.
			var box:=BoxShape3D.new();var bounds:AABB=node.mesh.get_aabb();box.size=bounds.size.max(Vector3.ONE*.002)
			shape.shape=box;shape.position=bounds.get_center()
		else:shape.shape=node.mesh.create_trimesh_shape()
		body.add_child(shape);node.add_child(body);bodies.append(body)
		for surface in range(node.mesh.get_surface_count()):
			var original:Material=node.get_active_material(surface)
			if not original is StandardMaterial3D:continue
			if material_cache.has(original.get_instance_id()):
				node.set_surface_override_material(surface,material_cache[original.get_instance_id()]);continue
			var mat:=ShaderMaterial.new();mat.shader=load("res://collection/surface.gdshader")
			mat.set_shader_parameter("scan_fabric",load("res://assets/collection/art/wormhole_fabric.png"))
			mat.set_shader_parameter("tint",original.albedo_color)
			mat.set_shader_parameter("metallic",original.metallic)
			mat.set_shader_parameter("roughness",original.roughness)
			mat.set_shader_parameter("has_color",original.albedo_texture!=null)
			mat.set_shader_parameter("has_roughness",original.roughness_texture!=null)
			mat.set_shader_parameter("has_normal",original.normal_texture!=null)
			if original.albedo_texture:mat.set_shader_parameter("color_map",original.albedo_texture)
			if original.roughness_texture:mat.set_shader_parameter("roughness_map",original.roughness_texture)
			if original.normal_texture:mat.set_shader_parameter("normal_map",original.normal_texture)
			mat.set_shader_parameter("coat",.38 if original.resource_name.contains("Ivory") else .10)
			if play.g_instrument:
				mat.set_shader_parameter("coat",.55 if original.resource_name.contains("Porcelain") else .12)
				if original.resource_name.contains("OpticalGlass"):
					mat.set_shader_parameter("coat",.65);mat.set_shader_parameter("roughness_floor",.08)
				if original.resource_name.contains("PlayerPorcelain"):mat.set_shader_parameter("coat",.55)
				if original.resource_name.contains("RecordBlack"):mat.set_shader_parameter("record_vinyl",true)
				mat.set_shader_parameter("normal_depth",.065)
				mat.set_shader_parameter("anisotropy_strength",.23 if original.metallic>.8 else 0.0)
				if original.resource_name.contains("Signal"):
					mat.set_shader_parameter("emission_color",Color(1,.57,.19));mat.set_shader_parameter("emission_energy",1.5);emissive_materials.append(mat)
			if play.instrument:
				mat.set_shader_parameter("roughness_scale",.88 if original.metallic>.8 else 1.0)
				mat.set_shader_parameter("roughness_floor",.13 if original.metallic>.8 else .18)
				mat.set_shader_parameter("normal_depth",.075)
				mat.set_shader_parameter("anisotropy_strength",.32 if original.resource_name.contains("Chrome") else .12 if original.metallic>.8 else 0.0)
				if original.resource_name.contains("Signal"):
					mat.set_shader_parameter("instrument_gain",0.0)
					mat.set_shader_parameter("instrument_profile",load("res://assets/collection/art/F/field_atlas.png"))
					instrument_materials.append(mat)
			if original.resource_name.contains("Glow"):
				mat.set_shader_parameter("emission_color",Color(1,.09,.025))
				mat.set_shader_parameter("emission_energy",1.0)
				emissive_materials.append(mat)
			node.set_surface_override_material(surface,mat);materials.append(mat)
			material_cache[original.get_instance_id()]=mat
	for child in node.get_children():
		if not child is StaticBody3D:_collect(child)

func activate(index:int)->void:
	stowing=false
	if data.id=="M" and index==1:
		effect.orbit_paused=not effect.orbit_paused
		effect.resume()
		return
	if data.id=="M" and index==4 and explosion<.001:
		effect.reseed();return
	match index:
		1:
			pending_burst=false;burst=0
			if explosion>.001:explode_target=0;open_target=1
			else:open_target=0.0 if open_target>.5 else 1.0
		2:explode_target=0;open_target=1;pending_burst=true
		3:open_target=0;explode_target=1;burst=0;pending_burst=false
		4:open_target=0;explode_target=0;burst=0;pending_burst=false
	if open_target>0:effect.resume()
	else:effect.request_quiet()

func stow()->void:
	open_target=0;explode_target=0;pending_burst=false;burst=0
	stowing=true
	if effect:effect.request_quiet()

func settled()->bool:
	return openness<.001 and explosion<.001 and open_target==0 and explode_target==0 and _motion_neutral() and (effect==null or effect.ready_to_fold())

func tick(delta:float,enabled_power:float)->void:
	clock+=delta;power=enabled_power
	play.tick(delta)
	_update_motions(delta)
	for mat in emissive_materials:mat.set_shader_parameter("power",power*(effect.quiet_gain if effect else 1.0))
	if open_target==0 and (stowing or explode_target>0 or openness>.001 or explosion>.001) and effect and not effect.ready_to_fold():
		apply_pose();effect.tick(delta);_sync_colliders();return
	# Fold before extracting, reassemble before opening. The two operations
	# cannot fight over the same assembly during interrupted actions.
	if explode_target>0:
		openness=move_toward(openness,0,delta*(1.5 if data.has("record_player") else .55))
		if openness<=.001 and _motion_neutral():explosion=move_toward(explosion,1,delta*.42)
	else:
		explosion=move_toward(explosion,0,delta*.50)
		if explosion<=.001:openness=move_toward(openness,open_target,delta*(1.5 if data.has("record_player") else .42))
	if pending_burst and openness>.999 and explosion<.001:
		pending_burst=false;burst=7.0
		if effect:effect.trigger_burst()
	burst=maxf(0,burst-delta)
	if explosion<.001:phase+=delta*power*(1.0+sin(burst/7.0*PI)*2.0)
	apply_pose()
	if effect:effect.tick(delta)
	_sync_colliders()

func apply_pose()->void:
	_apply_interactive_rig()
	for c in controls:
		var f:float=clampf(play.pose_fraction(str(c.node.name),openness),0,1)*(c.samples.size()-1)
		var lo:=int(f);var desired:Transform3D=c.samples[lo].interpolate_with(c.samples[mini(lo+1,c.samples.size()-1)],f-lo)
		if c.node.transform!=desired:c.node.transform=desired
	if play.instrument:_apply_f_kinematics()
	if play.g_instrument:play.g_instrument.apply()
	for m in motions:
		var desired:Transform3D=m.home;desired.basis=m.home.basis*Basis(m.pose)
		if m.node.transform!=desired:m.node.transform=desired
	for p in parts:
		var desired:Transform3D=p.home
		var progress:=smoothstep(p.stage*.25,1.0,explosion)
		if p.route.is_empty():desired.origin+=p.offset*progress
		else:
			for i in range(p.route.size()-1):
				var first:Dictionary=p.route[i];var last:Dictionary=p.route[i+1]
				if explosion<=float(last.at):
					desired.origin+=v3(first.offset).lerp(v3(last.offset),smoothstep(float(first.at),float(last.at),explosion));break
		if p.node.transform!=desired:p.node.transform=desired

func _apply_interactive_rig()->void:
	if interactive_rig.is_empty():return
	var trim:float=play.instrument.preload_value if play.instrument else lerpf(.25,play.number("trim"),play.gain)
	var brake:float=play.number("brake")*play.gain
	for item in interactive_rig:
		var desired:Transform3D=item.home
		match item.kind:
			"trim_gear":desired.basis=item.home.basis*Basis(Vector3.BACK,-(trim-.25)*2.2)
			"counter_gear":desired.basis=item.home.basis*Basis(Vector3.BACK,(trim-.25)*3.6)
			"trim_carriage":
				var a:=deg_to_rad(141.0-trim*28.0)
				desired.origin=Vector3(-.1+.836*cos(a),1.8+.836*sin(a),.147)
				desired.basis=Basis(Vector3.BACK,a)
			"brake_left":desired.origin.x+=.014*brake
			"brake_right":desired.origin.x-=.014*brake
		item.node.transform=desired

func advance_yaw(delta:float,target:float)->void:
	if not play.instrument:rotation.y=target;return
	var error:=wrapf(target-rotation.y,-PI,PI)
	var desired:=clampf(error*7.0,-1.5,1.5)
	yaw_velocity=move_toward(yaw_velocity,desired,delta*3.0)
	rotation.y+=yaw_velocity*delta

func _apply_f_kinematics()->void:
	var physics:RefCounted=play.instrument.physics
	var angle:float=physics.theta
	var h:Vector3=physics.H;var q:Vector3=physics.Q
	var k:Array=physics.right_kinematics(angle)
	var top:Vector3=k[3];var lower:Vector3=k[0]
	var delta:=lerpf(-65.0*PI/180.0,physics.DELTA,smoothstep(0.0,1.0,openness))
	var left_start:=h+Vector3(0,0,physics.counter_depth)
	var left_end:=left_start+Vector3(physics.left_length*cos(angle+delta),physics.left_length*sin(angle+delta),0)
	var links:={"F_C_UpperFourBar":[h,top],"F_C_LowerFourBar":[q,lower],"F_C_Coupler":[top,lower],"F_C_CounterArm":[left_start,left_end]}
	for label in links:
		var a:Vector3=links[label][0];var b:Vector3=links[label][1];var direction:=b-a
		var node:Node3D=named(label)
		node.transform=Transform3D(Basis(Quaternion(Vector3.UP,direction.normalized()))*Basis.from_scale(Vector3(1,direction.length(),1)),(a+b)*.5)
		for i in range(2):named(label+"_end"+str(i)).position=links[label][i]
	named("F_C_PrismHanger").position=lower;named("F_C_PearlHanger").position=left_end
	var unrotate:=Basis(Vector3.UP,-rotation.y)
	named(str(data.f_physics.plumb_pivot)).basis=Basis(Quaternion(Vector3.DOWN,(unrotate*physics.direction).normalized()))
	named(str(data.f_physics.prism_pivot)).basis=Basis(Quaternion(Vector3.DOWN,(unrotate*physics.right_direction).normalized()))
	var latch:float=play.instrument.travel_latch
	named(str(data.f_physics.spring_preload)).basis=Basis(Vector3.BACK,-play.instrument.preload_value*.60)
	named(str(data.f_physics.receiver_lift)).position.y=.24*smoothstep(.10,.65,openness)
	named(str(data.f_physics.receiver_slide)).position.z=-.245*smoothstep(.65,1.0,openness)
	named(str(data.f_physics.brake_rotor)).basis=Basis(Vector3.BACK,angle)
	for item in data.f_physics.get("transport_guides",[]):
		var node:Node3D=named(item.name)
		node.position=v3(item.home)+Vector3(float(item.sign)*.040*(1.0-latch),0,0)

func _update_motions(delta:float)->void:
	for m in motions:
		var value:float=phase*m.speed+m.phase
		if m.amplitude>0:value=sin(value)*m.amplitude
		if open_target>.01 and not stowing:value=play.motion_angle(str(m.node.name),value)
		if explode_target>0 or explosion>.001 or stowing:value=0
		var axis:=Vector3.UP if m.axis=="y" else Vector3.RIGHT if m.axis=="x" else Vector3.BACK
		var target:=Quaternion(axis,value)
		m.pose=m.pose.slerp(target,1.0-exp(-delta*10)).normalized()
		if value==0 and absf(m.pose.dot(Quaternion.IDENTITY))>.999999:m.pose=Quaternion.IDENTITY

func _motion_neutral()->bool:
	return motions.all(func(m):return absf(m.pose.dot(Quaternion.IDENTITY))>.999999)

func set_scan(value:float)->void:
	scan=value
	var minimum:=bounds.position.y
	var maximum:=bounds.end.y
	for mat in materials:
		mat.set_shader_parameter("scan_amount",value)
		mat.set_shader_parameter("scan_min",minimum)
		mat.set_shader_parameter("scan_max",maximum)

func set_interactive(enabled:bool)->void:
	interactive=enabled;_sync_colliders()

func _sync_colliders()->void:
	for body in bodies:
		var mesh:Node3D=body.get_parent()
		var enabled:bool=interactive and mesh.is_visible_in_tree()
		if str(mesh.name).begins_with("N_Membrane") and openness>.25:enabled=false
		var layer:=4 if enabled else 0
		if body.collision_layer!=layer:body.collision_layer=layer

func _bounds()->AABB:
	var result:=AABB();var first:=true
	for mesh in meshes:
		var bb:=mesh.global_transform*mesh.get_aabb()
		if first:result=bb;first=false
		else:result=result.merge(bb)
	return result

func diagnostics()->Dictionary:
	return {"id":data.id,"parts":parts.size(),"controls":controls.size(),"openness":openness,"explosion":explosion,"burst":burst,"base_owned":false,"finite":parts.all(func(p):return p.node.global_position.is_finite()),"authored_fx":effect.atlas.resource_path if effect!=null else ""}
