extends Node3D

var host: Node3D
var clock := 0.0
var wake_time := 0.0
var mechanical_time := 0.0
var assemble_time := 0.0
var explode_time := 0.0
var arcs: MeshInstance3D
var arc_mesh := ImmediateMesh.new()
var spark_material: StandardMaterial3D
var steam_material: StandardMaterial3D
var sparks: Array = []
var steam: Array = []
var coil_segments: Array = []
var halo: MeshInstance3D
var halo_material: ShaderMaterial
var rng := RandomNumberGenerator.new()
var emission_clock := 0.0
var last_open := 0.0
var last_explode := 0.0
var centers: Dictionary = {}

func setup(owner_node: Node3D) -> void:
	host = owner_node
	rng.seed = 195507
	for p in host.parts:
		var center:=Vector3.ZERO
		for c in p.node.get_children():
			if c is MeshInstance3D:
				center=c.transform*c.get_aabb().get_center();break
		centers[p.node.name]=center
	spark_material = StandardMaterial3D.new()
	spark_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark_material.albedo_color = Color(1,.36,.07)
	spark_material.emission_enabled = true
	spark_material.emission = Color(1,.24,.025)
	spark_material.emission_energy_multiplier = 4.0
	var mesh := SphereMesh.new()
	mesh.radius = .006
	mesh.height = .012
	mesh.radial_segments = 8
	mesh.rings = 4
	for i in range(90):
		var particle := MeshInstance3D.new()
		particle.mesh = mesh
		particle.material_override = spark_material
		particle.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		particle.hide()
		add_child(particle)
		sparks.append({"node":particle,"velocity":Vector3.ZERO,"age":0.0,"life":0.0,"target":Vector3.ZERO,"magnetic":false})
	var smoke_shader := Shader.new()
	smoke_shader.code = """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
uniform float opacity=0.1;
void vertex(){ MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0],INV_VIEW_MATRIX[1],INV_VIEW_MATRIX[2],MODEL_MATRIX[3]); }
void fragment(){ vec2 p=UV*2.0-1.0; float d=dot(p,p); ALBEDO=vec3(0.66,0.61,0.49); ALPHA=exp(-d*4.0)*smoothstep(1.0,0.3,d)*opacity; }
"""
	for i in range(14):
		var puff := MeshInstance3D.new()
		var quad := QuadMesh.new()
		quad.size = Vector2(.21,.21)
		puff.mesh = quad
		var material := ShaderMaterial.new()
		material.shader = smoke_shader
		puff.material_override = material
		puff.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		puff.hide()
		add_child(puff)
		steam.append({"node":puff,"age":0.0,"life":0.0,"velocity":Vector3.ZERO})
	arcs = MeshInstance3D.new()
	arcs.mesh = arc_mesh
	arcs.material_override = spark_material
	arcs.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(arcs)
	# Individual inset circuit segments reveal power travelling around the pedestal.
	for i in range(48):
		var a := i*TAU/48.0
		var segment := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(.060,.003,.005)
		segment.mesh = box
		segment.position = Vector3(.883*cos(a),.676,.883*sin(a))
		segment.rotation.y = -a+PI/2
		segment.material_override = spark_material.duplicate()
		segment.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(segment)
		coil_segments.append(segment)
	var halo_shader := Shader.new()
	halo_shader.code = """
shader_type spatial;
render_mode unshaded, cull_back, depth_draw_never, blend_add;
uniform float intensity=0.0;
void fragment(){ float rim=pow(1.0-max(dot(NORMAL,VIEW),0.0),2.5); ALBEDO=vec3(1.0,0.14,0.015)*2.0; ALPHA=rim*intensity; }
"""
	halo = MeshInstance3D.new()
	var globe := SphereMesh.new()
	globe.radius=.34
	globe.height=.68
	halo.mesh=globe
	halo_material=ShaderMaterial.new()
	halo_material.shader=halo_shader
	halo.material_override=halo_material
	halo.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(halo)

func trigger(action: int) -> void:
	match action:
		0: wake_time=2.3
		1: mechanical_time=2.1
		2: mechanical_time=1.5
		3: explode_time=2.5
		4: assemble_time=2.9
		5: pass
		6:
			assemble_time=2.6
			mechanical_time=2.6

func emit_spark(origin: Vector3, velocity: Vector3, life: float, magnetic := false, target := Vector3.ZERO) -> void:
	for s in sparks:
		if s.life<=0:
			s.node.global_position=origin
			s.node.show()
			s.velocity=velocity
			s.life=life
			s.age=0.0
			s.target=target
			s.magnetic=magnetic
			return

func tick(delta: float) -> void:
	clock+=delta
	wake_time=maxf(0,wake_time-delta)
	mechanical_time=maxf(0,mechanical_time-delta)
	assemble_time=maxf(0,assemble_time-delta)
	explode_time=maxf(0,explode_time-delta)
	var core: Vector3 = host.named("P_Solar_Crystal").global_position
	var boost := sin(clampf(host.overload/7.0,0,1)*PI)
	halo.global_position=core
	halo_material.set_shader_parameter("intensity",host.power*(.025+boost*.15)*(1.0-host.explosion))
	halo.scale=Vector3.ONE*(1.0+sin(clock*4.0)*.018)
	for i in range(coil_segments.size()):
		var m: StandardMaterial3D = coil_segments[i].material_override
		var phase := fposmod(i/48.0-clock*.18,1.0)
		var value: float = .015+host.power*.06
		if wake_time>0: value+=pow(maxf(0,1.0-abs(phase-.5)*7),2.0)*wake_time*.7
		value+=boost*(.22+.18*sin(clock*9+i*.26))
		m.emission_energy_multiplier=value
		m.albedo_color=Color(.40,.075,.008)*maxf(.03,value*.3)
	# Mechanical sparks only during release or seating; suspended parts stay readable.
	emission_clock+=delta
	if emission_clock>.055:
		emission_clock=0
		if mechanical_time>0 and absf(host.openness-last_open)>.0001:
			var i := int(clock*9)%6
			var origin: Vector3=host.named("PETAL_HINGE_%02d"%i).global_position
			emit_spark(origin,Vector3(rng.randf_range(-.15,.15),.18,rng.randf_range(-.15,.15)),.24)
		if explode_time>0 or assemble_time>0:
			var i := rng.randi_range(0,host.parts.size()-1)
			var p: Dictionary=host.parts[i]
			var local_center: Vector3=centers[p.node.name]
			var endpoint: Vector3=p.node.global_transform*local_center
			var target: Vector3=p.node.get_parent().global_transform*(p.home*local_center)
			if endpoint.distance_to(target)>.06:
				var start: Vector3=endpoint.lerp(target,rng.randf())
				var velocity: Vector3=(target-endpoint).normalized()*.8
				if explode_time>0: velocity=-velocity
				emit_spark(start,velocity,.30,assemble_time>0,target)
		if boost>.2:
			var direction:=Vector3(rng.randf_range(-1,1),rng.randf_range(-1,1),rng.randf_range(-1,1)).normalized()
			emit_spark(core+direction*.30,direction*.55,.38)
			if rng.randf()>.6:
				for puff in steam:
					if puff.life<=0:
						var source: Vector3 = host.named("P_Thermal_Valve_0").global_transform*Vector3(.89,2.62,-.10)
						puff.node.global_position=source
						puff.age=0.0;puff.life=.75;puff.velocity=Vector3(.035,.22,0)
						puff.node.show();break
	for s in sparks:
		if s.life<=0: continue
		s.age+=delta
		if s.age>=s.life: s.life=0;s.node.hide();continue
		if s.magnetic: s.velocity+=(s.target-s.node.global_position)*delta*2.0
		else: s.velocity.y-=delta*.3
		s.node.global_position+=s.velocity*delta
		var fade: float=1.0-s.age/s.life
		s.node.scale=Vector3(.65,2.8,.65)*fade
		if s.velocity.length_squared()>.0001: s.node.quaternion=Quaternion(Vector3.UP,s.velocity.normalized())
	for puff in steam:
		if puff.life<=0: continue
		puff.age+=delta
		if puff.age>=puff.life:puff.life=0;puff.node.hide();continue
		puff.node.global_position+=puff.velocity*delta
		puff.node.scale=Vector3.ONE*(.7+puff.age*1.7)
		puff.node.material_override.set_shader_parameter("opacity",sin(puff.age/puff.life*PI)*.09)
	arc_mesh.clear_surfaces()
	if boost>.25 and host.openness>.6 and host.explosion<.05:
		arc_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
		for j in range(3):
			var a:=clock*(1.4+j*.3)+j*TAU/3
			var last:=core+Vector3(cos(a),sin(a),sin(a*.7))*.29
			for k in range(1,8):
				var aa:=a+k*.07
				var rr:=.29+k*.038
				var pt:=core+Vector3(cos(aa)*rr,sin(aa)*rr,sin(a*.7)*rr)+Vector3(rng.randf_range(-.012,.012),rng.randf_range(-.012,.012),0)
				arc_mesh.surface_add_vertex(last);arc_mesh.surface_add_vertex(pt);last=pt
		arc_mesh.surface_end()
	last_open=host.openness
	if last_explode>.002 and host.explosion<=.002 and assemble_time>0:
		for i in range(6):
			var pos:Vector3=host.named("PETAL_HINGE_%02d"%i).global_position
			for j in range(3):emit_spark(pos,Vector3(rng.randf_range(-.2,.2),.2,rng.randf_range(-.2,.2)),.18)
	last_explode=host.explosion
