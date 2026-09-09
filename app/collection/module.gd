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
		var shape:=CollisionShape3D.new();shape.shape=node.mesh.create_trimesh_shape();body.add_child(shape);node.add_child(body);bodies.append(body)
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
		openness=move_toward(openness,0,delta*.55)
		if openness<=.001 and _motion_neutral():explosion=move_toward(explosion,1,delta*.42)
	else:
		explosion=move_toward(explosion,0,delta*.50)
		if explosion<=.001:openness=move_toward(openness,open_target,delta*.42)
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
	var trim:float=lerpf(.25,play.number("trim"),play.gain)
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
