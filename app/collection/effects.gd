extends Node3D
## Authored atlas + Blender geometry, with state-controlled real-time composition.

var module:Node3D
var atlas:Texture2D
var field:MeshInstance3D
var field_mat:ShaderMaterial
var quiet:=false
var quiet_gain:=1.0
var orbit_paused:=false
var orbit_time:=0.0
var orbit_speed:=1.0
var burst_age:=-1.0
var reseed_age:=-1.0
var worlds:Array=[]
var black_core:MeshInstance3D
var throat:MeshInstance3D
var throat_mat:ShaderMaterial
var probe_entry:Node3D
var probe_exit:Node3D
var probe_basis:Basis
var probe_t:=0.0
var probe_running:=false
var probe_returning:=false
var membranes:Array=[]
var lines:Array=[]
var light:OmniLight3D
var throat_pose_a:=Transform3D()
var throat_pose_b:=Transform3D()
var capillaries:Array[ShaderMaterial]=[]
var f_visuals:Node3D
var g_visuals:Node3D

func setup(owner:Node3D)->void:
	module=owner
	if module.play.g_instrument:
		g_visuals=load("res://collection/g_visuals.gd").new();add_child(g_visuals);g_visuals.setup(module);g_visuals.tick(0,0)
		atlas=g_visuals.atlas;return
	if module.play.instrument:
		f_visuals=load("res://collection/f_visuals.gd").new();add_child(f_visuals);f_visuals.setup(module);f_visuals.tick(0,0)
		atlas=f_visuals.atlas
		return
	atlas=load("res://assets/collection/art/fx_atlas.png")
	var id:String=module.data.id
	var tiles:Dictionary={"F":0,"G":1,"I":2,"J":3,"K":4,"L":5,"M":6,"N":7}
	field_mat=_material(float(tiles[id]))
	field=MeshInstance3D.new();var quad:=QuadMesh.new();quad.size=Vector2(1.2,1.2);field.mesh=quad;field.material_override=field_mat
	field.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(field)
	light=OmniLight3D.new();light.omni_range=1.6;light.light_energy=0;light.light_color=Color(1,.12,.035);light.shadow_enabled=false;add_child(light)
	if id=="M":
		for item in module.data.planets:
			var node:Node3D=module.named(item.node)
			var surface:Array=[];_planet_surfaces(node,surface)
			worlds.append({"node":node,"mesh":module.named(item.mesh),"radius":float(item.radius),"orbit":float(item.orbit),"phase":float(item.phase),"basis":node.basis,"surfaces":surface})
		black_core=module.named(module.data.black_core)
		var black:=StandardMaterial3D.new();black.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;black.albedo_color=Color.BLACK;black_core.material_override=black
		field_mat.set_shader_parameter("image_scale",Vector2(1,.72))
	if id=="N":_setup_rift()
	if id=="J":
		for mesh in module.meshes:
			if str(mesh.name).contains("Capillary"):
				var mat:=ShaderMaterial.new();mat.shader=load("res://collection/capillary.gdshader");mat.set_shader_parameter("atlas",atlas);mesh.material_override=mat;module.materials.append(mat);capillaries.append(mat)
	tick(0)

func _material(tile:float)->ShaderMaterial:
	var m:=ShaderMaterial.new();m.shader=load("res://collection/atlas.gdshader");m.set_shader_parameter("atlas",atlas);m.set_shader_parameter("tile",tile);return m

func _planet_surfaces(node:Node,into:Array)->void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var original:Material=node.get_active_material(i)
			if original is ShaderMaterial:
				var mat:ShaderMaterial=original.duplicate();node.set_surface_override_material(i,mat);into.append(mat);module.materials.append(mat)
	for child in node.get_children():_planet_surfaces(child,into)

func trigger_burst()->void:
	quiet=false;burst_age=0;reseed_age=-1
	if module.data.id=="N":probe_running=true;probe_returning=false;probe_t=0

func resume()->void:
	quiet=false

func request_quiet()->void:
	quiet=true
	if probe_t>.001:probe_running=false;probe_returning=true

func ready_to_fold()->bool:
	if g_visuals:return quiet and quiet_gain<.001 and module.play.g_instrument.ready_to_fold()
	if f_visuals:return quiet and quiet_gain<.001 and module.play.instrument.ready_to_fold()
	return quiet and quiet_gain<.001 and not probe_returning

func reseed()->void:
	quiet=false;reseed_age=0;burst_age=-1

func _socket(key:String)->Node3D:
	return module.named(str(module.data.sockets[key]))

func tick(delta:float)->void:
	if g_visuals:
		quiet_gain=move_toward(quiet_gain,0.0 if quiet else 1.0,delta*1.8)
		g_visuals.tick(delta,quiet_gain);return
	if f_visuals:
		quiet_gain=move_toward(quiet_gain,0.0 if quiet else 1.0,delta*1.8)
		f_visuals.tick(delta,quiet_gain);return
	var manual:bool=module.play!=null and module.play.gain>.001 and not quiet
	if manual and module.data.id=="M":
		orbit_speed=module.play.number("orbit")
		burst_age=float(module.play.response.capture_age)
		reseed_age=float(module.play.response.rebuild)
	if not quiet and not orbit_paused:orbit_time+=delta*orbit_speed
	if burst_age>=0 and not (manual and module.data.id=="M"):burst_age+=delta
	if reseed_age>=0 and not (manual and module.data.id=="M"):reseed_age+=delta
	if probe_returning:
		probe_t=move_toward(probe_t,0,delta*.55)
		if probe_t<=0:probe_returning=false
	quiet_gain=move_toward(quiet_gain,0.0 if quiet and not probe_returning else 1.0,delta*1.8)
	var power:float=module.power*quiet_gain
	var active:float=module.openness*(1.0-module.explosion)*power
	var climax:float=sin(clampf(module.burst/7.0,0,1)*PI)
	var origin:Node3D=_socket("field")
	field.global_transform=origin.global_transform
	field_mat.set_shader_parameter("strength",active*(.35+climax))
	light.global_position=origin.global_position;light.light_energy=active*(.10+climax*.35)
	match str(module.data.id):
		"F":
			field.visible=false
			var tip:Vector3=_socket("weight_tip").global_position
			_update_links([tip],Vector3(tip.x,origin.global_position.y,tip.z),active*(.4+float(module.play.response.balance)*1.8) if manual else active*1.8)
		"G":
			field.scale=Vector3(.78,.86,1)
			if manual:field_mat.set_shader_parameter("strength",active*(.10+float(module.play.response.imprint)*1.8))
			_update_links([_socket("page_0").global_position,_socket("page_2").global_position,_socket("page_4").global_position],origin.global_position,active)
		"I":
			field.scale=Vector3.ONE*(.72+.2*sin(module.clock*(.7+module.play.number("frequency")*2.0))) if manual else Vector3.ONE*(.72+.2*sin(module.clock*1.3))
			if manual:field_mat.set_shader_parameter("strength",active*(.08+float(module.play.response.echo)*1.8))
			field.global_position+=origin.global_basis.z*.10
		"J":
			field.visible=false
			for i in range(capillaries.size()):
				capillaries[i].set_shader_parameter("pulse",module.clock*.32-i*.12)
				capillaries[i].set_shader_parameter("strength",active*(.22+module.play.number("light")*(1.2 if i%3==int(module.play.number("branch")) else .25)) if manual else active*(.55+climax*1.5))
		"K":
			field.rotate_object_local(Vector3.RIGHT,-PI/2);field.scale=Vector3(1.0,.23,1)
			field_mat.set_shader_parameter("image_scale",Vector2(1,.25))
			field_mat.set_shader_parameter("flow",fposmod(module.play.number("feed")*.12,1.0) if manual else fmod(module.phase*.035,1.0))
			var tips:Array=[];var points:Array=[]
			for i in range(3):
				var stylus:Node3D=module.named("K_C_StylusLift"+str(i))
				var contact:float=module.play.number("stylus") if manual and i==int(module.play.number("channel")) else 0.0 if manual else maxf(0,sin(module.phase*4+i*TAU/3))
				stylus.position.y-=.055*contact*module.openness
				var tip:Vector3=_socket("needle_"+str(i)).global_position
				tips.append(tip);points.append(Vector3(tip.x,origin.global_position.y,tip.z))
			_update_links(tips,points,active*module.play.number("stylus")*clampf(float(module.play.response.feed_motion)*12,0,1) if manual else active)
		"L":
			field.scale=Vector3(.16,.16,1)
			var target:Vector3=origin.global_position
			if manual:target+=Vector3(module.play.response.aim.x,module.play.response.aim.y,0);field.global_position=target
			_aim_lenses(target)
			var endpoints:Array=[]
			for i in range(3):endpoints.append(target+Vector3((i-1)*.24,abs(i-1)*.12,0)*(1.0-float(module.play.response.focus_quality)) if manual else target)
			_update_links([_socket("lens_0").global_position,_socket("lens_1").global_position,_socket("lens_2").global_position],endpoints,active*module.play.number("aperture") if manual else active*smoothstep(.90,.995,float(module.openness)))
		"M":_tick_worlds(delta,power,origin)
		"N":_tick_rift(delta,active)
	if module.data.id not in ["M","N"]:field.scale*=float(module.data.get("display_calibration",{}).get("scale",1.0))

func _update_links(points:Array,target:Variant,gain:float)->void:
	while lines.size()<points.size():
		var mesh:=MeshInstance3D.new();var cylinder:=CylinderMesh.new();cylinder.top_radius=.003;cylinder.bottom_radius=.003;cylinder.height=1;cylinder.radial_segments=6
		mesh.mesh=cylinder;mesh.material_override=_material(0);mesh.material_override.set_shader_parameter("image_scale",Vector2(.04,1));mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(mesh);lines.append(mesh)
	for i in range(lines.size()):
		var a:Vector3=points[i];var destination:Vector3=target[i] if target is Array else target;var direction:=destination-a
		if direction.length()<.00001:lines[i].hide();continue
		lines[i].global_position=(a+destination)*.5
		lines[i].global_basis=Basis(Quaternion(Vector3.UP,direction.normalized()))*Basis.from_scale(Vector3(1,direction.length(),1))
		lines[i].visible=gain>.015
		lines[i].material_override.set_shader_parameter("strength",gain)

func _aim_lenses(target:Vector3)->void:
	var amount:=smoothstep(.25,.9,float(module.openness))
	for name in module.data.get("look_pivots",[]):
		var pivot:Node3D=module.named(name)
		var start:Transform3D=pivot.global_transform
		var basis:Basis=start.basis
		var scale:Vector3=basis.get_scale()
		for iteration in range(6):
			var eye:Vector3=start.origin+basis*Vector3(0,.20,0)
			basis=Basis.looking_at(target-eye,Vector3.UP,true)*Basis.from_scale(scale)
		pivot.global_transform=start.interpolate_with(Transform3D(basis,start.origin),amount)

func _tick_worlds(_delta:float,power:float,origin:Node3D)->void:
	var center:Vector3=origin.global_position
	var swallowing:=burst_age>=0 and reseed_age<0
	var black_gain:=smoothstep(.2,1.6,burst_age) if swallowing else 0.0
	if reseed_age>=0:black_gain=1.0-smoothstep(0.0,1.2,reseed_age)
	black_core.visible=black_gain*power>.015 and module.explosion<.001
	black_core.global_position=center
	black_core.scale=Vector3.ONE*maxf(.01,black_gain)
	field.global_position=center;field.global_basis=origin.global_basis
	field.rotate_object_local(Vector3.RIGHT,-PI/2+.20);field.scale=Vector3.ONE*(.72+.28*black_gain)
	field_mat.set_shader_parameter("strength",black_gain*power*1.7)
	field_mat.set_shader_parameter("spin",orbit_time*.46)
	light.light_energy=black_gain*power*.8
	for i in range(worlds.size()):
		var world:Dictionary=worlds[i]
		var ingest:=smoothstep(1.0+i*1.7,3.1+i*1.7,burst_age) if swallowing else 0.0
		var rebuild:=smoothstep(.2+i*.15,2.6+i*.15,reseed_age) if reseed_age>=0 else 1.0
		var radius:float=world.orbit*(1.0-ingest*.93)
		var angle:float=orbit_time*(.45+.12*i)+world.phase+ingest*TAU*1.7
		var offset:=Vector3(cos(angle)*radius,sin(angle*.8+i)*radius*.18,sin(angle)*radius)
		world.node.global_position=center+origin.global_basis*offset
		world.node.visible=power>.015 and ingest<.998 and module.explosion<.001
		var scale:=Vector3.ONE*maxf(.002,1.0-ingest*.72)
		for material in world.surfaces:material.set_shader_parameter("formation",rebuild*power)
		world.node.basis=world.basis*Basis(Vector3.UP,orbit_time*.6)*Basis.from_scale(scale)
		if world.mesh is MeshInstance3D and world.mesh.get_blend_shape_count()>0:
			world.mesh.set_blend_shape_value(0,ingest)
		if ingest>.05:
			var direction:Vector3=(center-world.node.global_position).normalized()
			world.node.global_basis=Basis(Quaternion(Vector3.RIGHT,direction))*Basis.from_scale(scale)
	if reseed_age>3.2:reseed_age=-1;burst_age=-1

func _setup_rift()->void:
	field.visible=false
	for i in range(module.data.membranes.size()):
		var mesh:MeshInstance3D=module.named(module.data.membranes[i])
		var mat:=ShaderMaterial.new();mat.shader=load("res://collection/membrane.gdshader");mat.set_shader_parameter("atlas",atlas);mesh.material_override=mat
		membranes.append({"node":mesh,"mat":mat})
		module.materials.append(mat)
	throat=MeshInstance3D.new();throat_mat=ShaderMaterial.new();throat_mat.shader=load("res://collection/conduit.gdshader");throat_mat.set_shader_parameter("fabric",load("res://assets/collection/art/wormhole_fabric.png"));throat.material_override=throat_mat;throat.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(throat)
	probe_entry=module.named(module.data.probe)
	probe_exit=probe_entry.duplicate();add_child(probe_exit);probe_basis=probe_entry.basis
	_disable_probe_bodies(probe_exit)
	_duplicate_probe_materials(probe_entry);_duplicate_probe_materials(probe_exit)

func _disable_probe_bodies(node:Node)->void:
	if node is StaticBody3D:node.collision_layer=0
	for child in node.get_children():_disable_probe_bodies(child)

func _duplicate_probe_materials(node:Node)->void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var material:Material=node.get_active_material(i)
			if material is ShaderMaterial:
				var copy:ShaderMaterial=material.duplicate();node.set_surface_override_material(i,copy);module.materials.append(copy)
	for child in node.get_children():_duplicate_probe_materials(child)

func _clip_probe(node:Node,normal:Vector3,origin:Vector3,enabled:bool)->void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var mat:Material=node.get_active_material(i)
			if mat is ShaderMaterial:
				mat.set_shader_parameter("clip_enabled",enabled);mat.set_shader_parameter("clip_normal",normal);mat.set_shader_parameter("clip_d",-origin.dot(normal))
	for child in node.get_children():_clip_probe(child,normal,origin,enabled)

func _tick_rift(delta:float,active:float)->void:
	var a:Node3D=_socket("port_0");var b:Node3D=_socket("port_1")
	for i in range(membranes.size()):
		var opening:=smoothstep(i*.1,.82+i*.1,float(module.openness))
		membranes[i].node.set_blend_shape_value(0,opening)
		membranes[i].mat.set_shader_parameter("opening",opening);membranes[i].mat.set_shader_parameter("power",module.power)
	if probe_running:
		probe_t=move_toward(probe_t,1,delta*.36)
		if probe_t>=1:probe_running=false
	if module.play.gain>.001 and not quiet:
		probe_running=false
		probe_t=move_toward(probe_t,float(module.play.response.probe_target) if module.openness>.95 else 0.0,delta*.85)
	throat.visible=active>.02
	throat_mat.set_shader_parameter("strength",active*(.30+.60*float(module.play.response.focus_quality)) if module.play.gain>.001 else active*.9)
	throat_mat.set_shader_parameter("flow",fmod(orbit_time*.035,1.0))
	if active>.02 and (throat.mesh==null or not a.transform.is_equal_approx(throat_pose_a) or not b.transform.is_equal_approx(throat_pose_b)):
		_build_throat(a,b);throat_pose_a=a.transform;throat_pose_b=b.transform
	if module.explosion>.001:
		probe_exit.hide();return
	var forward_a:Vector3=a.global_basis.z.normalized();var forward_b:Vector3=b.global_basis.z.normalized()
	probe_entry.global_position=a.global_position+forward_a*(.62-probe_t*1.24)
	probe_exit.global_transform=probe_entry.global_transform
	probe_exit.global_basis=Basis(Vector3.UP,PI)*probe_entry.global_basis
	probe_exit.global_position=b.global_position+forward_b*(-.62+probe_t*1.24)
	probe_entry.visible=probe_t<.9;probe_exit.visible=probe_t>.1
	_clip_probe(probe_entry,forward_a,a.global_position,probe_t>0)
	_clip_probe(probe_exit,forward_b,b.global_position,true)

func _build_throat(a:Node3D,b:Node3D)->void:
	var first:Vector3=a.global_position;var last:Vector3=b.global_position
	var unit_scale:float=module.data.get("display_calibration",{}).get("scale",1.0)
	var c1:=first-a.global_basis.z*.55;var c2:=last-b.global_basis.z*.55
	var vertices:=PackedVector3Array();var uv:=PackedVector2Array();var indices:=PackedInt32Array()
	const LENGTH=24
	const RING=18
	for i in range(LENGTH+1):
		var t:=float(i)/LENGTH;var s:=1.0-t
		var center:=first*s*s*s+3*c1*s*s*t+3*c2*s*t*t+last*t*t*t
		var tangent:=(-3*first*s*s+3*c1*(s*s-2*s*t)+3*c2*(2*s*t-t*t)+3*last*t*t).normalized()
		var side:=tangent.cross(Vector3.UP).normalized();var up:=side.cross(tangent).normalized()
		var neck:=.22+.78*pow(absf(2*t-1),1.35)
		for j in range(RING+1):
			var angle:=float(j)/RING*TAU
			vertices.append(to_local(center+(side*cos(angle)*lerpf(.57,.47,t)*neck+up*sin(angle)*lerpf(.50,.30,t)*neck)*unit_scale))
			uv.append(Vector2(float(j)/RING,t))
	for i in range(LENGTH):
		for j in range(RING):
			var k:=i*(RING+1)+j;indices.append_array(PackedInt32Array([k,k+1,k+RING+2,k,k+RING+2,k+RING+1]))
	var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
	var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);throat.mesh=mesh
