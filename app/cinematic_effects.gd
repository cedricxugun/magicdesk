extends Node3D

var host: Node3D
var pressure: Node3D
var core: Node3D
var shell_markings: Node3D
var clock:=0.0
var event_time:=-1.0
var event_kind:=""
var coil_segments:Array=[]
var sparks:Array=[]
var centers:Dictionary={}
var rng:=RandomNumberGenerator.new()
var emission_clock:=0.0
var release_fired:=false
var last_explosion:=0.0
var charge_materials:Array[ShaderMaterial]=[]

func setup(owner_node:Node3D)->void:
	host=owner_node
	rng.seed=73911
	for file in ["pressure_vfx.gd","core_vfx.gd","shell_marking_vfx.gd"]:
		if not ResourceLoader.exists("res://"+file):continue
		var module:=Node3D.new()
		module.set_script(load("res://"+file))
		add_child(module)
		module.setup(host)
		if file.begins_with("pressure"):pressure=module
		elif file.begins_with("core"):core=module
		else:shell_markings=module
	host.core_materials.clear()
	host.core_light.light_energy=0.0
	for ring in host.pulse_rings:ring.queue_free()
	host.pulse_rings.clear()
	_make_charge_channels()
	for p in host.parts:
		var center:=Vector3.ZERO
		for c in p.node.get_children():
			if c is MeshInstance3D:center=c.transform*c.get_aabb().get_center();break
		centers[p.node.name]=center
	var material:=StandardMaterial3D.new()
	material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	material.emission_enabled=true
	material.albedo_color=Color(1,.47,.22)
	material.emission=Color(1,.25,.10)
	material.emission_energy_multiplier=2.0
	var spark_mesh:=SphereMesh.new()
	spark_mesh.radius=.0035;spark_mesh.height=.007
	spark_mesh.radial_segments=8;spark_mesh.rings=4
	for i in range(90):
		var p:=MeshInstance3D.new()
		p.mesh=spark_mesh;p.material_override=material
		p.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		p.hide();add_child(p)
		sparks.append({"node":p,"velocity":Vector3.ZERO,"age":0.0,"life":0.0})
	for i in range(48):
		var angle:=i*TAU/48.0
		var n:=MeshInstance3D.new()
		var mesh:=BoxMesh.new();mesh.size=Vector3(.047,.004,.006)
		n.mesh=mesh;n.position=Vector3(.886*cos(angle),.680,.886*sin(angle))
		n.rotation.y=-angle+PI/2
		n.material_override=material.duplicate()
		n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(n);coil_segments.append(n)
	trigger("ignition")

func _shell_radius(t:float)->float:
	var ts:=[0.0,.06,.16,.30,.47,.62,.76,.87,.95,1.0]
	var rs:=[.31,.43,.62,.78,.865,.84,.73,.565,.365,.17]
	var j:=8
	for i in range(9):
		if t<=ts[i+1]:j=i;break
	var u:float=(t-ts[j])/(ts[j+1]-ts[j]);var h:float=ts[j+1]-ts[j]
	var m0:float=(rs[j+1]-rs[maxi(0,j-1)])/(ts[j+1]-ts[maxi(0,j-1)])
	var m1:float=(rs[mini(9,j+2)]-rs[j])/(ts[mini(9,j+2)]-ts[j])
	return (2*u*u*u-3*u*u+1)*rs[j]+(u*u*u-2*u*u+u)*h*m0+(-2*u*u*u+3*u*u)*rs[j+1]+(u*u*u-u*u)*h*m1

func _make_charge_channels()->void:
	for i in range(6):
		var frame:Node3D=host.named("P_Petal_%02d_RibFrame"%i)
		var material:=ShaderMaterial.new();material.shader=load("res://charge_filament.gdshader")
		charge_materials.append(material)
		# One fine conductor in each actual recessed mechanical seam, not a shell outline.
		var angle:=deg_to_rad(27.2)
		var points:PackedVector3Array=[]
		for j in range(65):
			var t:=.045+.91*j/64.0;var r:=_shell_radius(t)-.003
			points.append(Vector3(r*cos(angle)-.31,2.68*t,-r*sin(angle)))
		var mesh:=ImmediateMesh.new();mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
		for j in range(points.size()-1):
			var direction:Vector3=(points[j+1]-points[j]).normalized()
			var side:=direction.cross(Vector3.FORWARD).normalized()
			var up:=direction.cross(side).normalized()
			for k in range(6):
				var a:=k*TAU/6;var b:=(k+1)*TAU/6
				var va:Vector3=(side*cos(a)+up*sin(a))*.004
				var vb:Vector3=(side*cos(b)+up*sin(b))*.004
				for data in [[points[j]+va,va,float(j)/64],[points[j+1]+va,va,float(j+1)/64],[points[j+1]+vb,vb,float(j+1)/64],[points[j]+va,va,float(j)/64],[points[j+1]+vb,vb,float(j+1)/64],[points[j]+vb,vb,float(j)/64]]:
					mesh.surface_set_normal(data[1].normalized());mesh.surface_set_uv(Vector2(0,data[2]));mesh.surface_add_vertex(data[0])
		mesh.surface_end()
		var n:=MeshInstance3D.new();n.name="Recessed_Charge_Conductor";n.mesh=mesh;n.material_override=material
		frame.add_child(n)

func trigger(kind:String)->void:
	event_kind="open" if kind=="core_open" else kind;event_time=0.0;release_fired=false
	if pressure and kind!="core_open":pressure.trigger("close" if kind=="assemble" else kind)
	if core:core.trigger("open" if kind=="core_open" else kind)
	if shell_markings:shell_markings.trigger("open" if kind=="core_open" else kind)

func emit_spark(origin:Vector3,velocity:Vector3,life:float)->void:
	for s in sparks:
		if s.life<=0:
			s.node.global_position=origin;s.node.show()
			s.velocity=velocity;s.age=0.0;s.life=life
			return

func tick(delta:float)->void:
	clock+=delta
	if event_time>=0:event_time+=delta
	if core:core.tick(delta)
	if pressure:pressure.tick(delta)
	if shell_markings:shell_markings.tick(delta)
	var power:float=host.power
	var activation:float=host.activation_energy
	var overload:float=sin(clampf(host.overload/7.0,0,1)*PI)
	for m in charge_materials:
		m.set_shader_parameter("power",power*(1.0-smoothstep(.03,.35,float(host.explosion))))
		m.set_shader_parameter("running",float(host.openness))
		m.set_shader_parameter("release",activation*.75+overload*.35)
		var sweep:float=event_time/1.12 if event_kind in ["ignition","open"] and event_time<1.6 else -2.0
		m.set_shader_parameter("sweep",sweep)
	for i in range(coil_segments.size()):
		var m:StandardMaterial3D=coil_segments[i].material_override
		var energy:=.035*power
		if event_kind in ["ignition","open"] and event_time<1.3:
			var progress:=event_time/1.3
			var distance:=absf(i/48.0-progress)
			energy+=exp(-distance*distance*170.0)*1.5
		energy+=activation*.13+overload*.20
		if host.shutdown_time>=0:energy*=maxf(0,1.0-host.shutdown_time/2.5)
		m.albedo_color=Color(.20,.008,.003)*energy
		m.emission=Color(1,.025,.012)
		m.emission_energy_multiplier=energy
	if event_kind=="open" and event_time>.34 and not release_fired:
		release_fired=true
		for i in range(6):
			var origin:Vector3=host.named("PETAL_HINGE_%02d"%i).global_position
			for j in range(3):emit_spark(origin,Vector3(rng.randf_range(-.32,.32),.20,rng.randf_range(-.32,.32)),.16)
	emission_clock+=delta
	if emission_clock>.06:
		emission_clock=0.0
		if event_kind in ["explode","assemble"] and event_time<2.7:
			var p:Dictionary=host.parts[rng.randi_range(0,host.parts.size()-1)]
			var center:Vector3=centers[p.node.name]
			var origin:Vector3=p.node.global_transform*center
			var destination:Vector3=p.node.get_parent().global_transform*(p.home*center)
			if origin.distance_to(destination)>.04:
				var motion:Vector3=(destination-origin).normalized()
				if event_kind=="explode":motion=-motion
				emit_spark(origin,motion*.32,.19)
	if last_explosion>.002 and host.explosion<=.002 and event_kind=="assemble":
		for i in range(6):
			var origin:Vector3=host.named("PETAL_HINGE_%02d"%i).global_position
			emit_spark(origin,Vector3(0,.2,0),.14)
	last_explosion=host.explosion
	for s in sparks:
		if s.life<=0:continue
		s.age+=delta
		if s.age>=s.life:s.life=0.0;s.node.hide();continue
		s.velocity.y-=delta*.75
		s.node.global_position+=s.velocity*delta
		s.node.scale=Vector3(.6,3.0,.6)*(1.0-s.age/s.life)
		if s.velocity.length_squared()>.0001:s.node.quaternion=Quaternion(Vector3.UP,s.velocity.normalized())
