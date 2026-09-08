extends SceneTree

var world: Node3D
var view: SubViewport
var env: Environment
var materials := {}
var model: Node3D
var mode := "baseline"
var pose := "closed"
var core_stage := "steady"
var turn_angle := 0.0
var output := "H:/model/output/helios_incubator/review/core_R3"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--mode="): mode=arg.trim_prefix("--mode=")
		if arg.begins_with("--stage="): core_stage=arg.trim_prefix("--stage=")
		if arg.begins_with("--pose="): pose=arg.trim_prefix("--pose=")
		if arg.begins_with("--angle="): turn_angle=float(arg.trim_prefix("--angle="))
	root.size=Vector2i(32,32)
	root.position=Vector2i(-32000,-32000)
	root.unfocusable=true
	root.title="HELIOS lighting verification"
	call_deferred("run")

func run() -> void:
	view=SubViewport.new()
	view.size=Vector2i(1200,1400)
	if pose=="open":view.size.x=2200
	view.transparent_bg=true
	view.own_world_3d=true
	view.msaa_3d=Viewport.MSAA_4X
	view.use_taa=false
	view.scaling_3d_scale=1.0
	view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	world=Node3D.new();world.set_script(load("res://core_probe_host.gd")); view.add_child(world)
	model=load("res://assets/helios_model.glb").instantiate()
	world.add_child(model)
	world.model=model
	world.openness=0.0 if pose=="closed" else 0.55 if core_stage=="reveal" else 1.0
	collect(model)
	model.find_child("TURNTABLE",true,false).rotation.y=turn_angle
	if pose=="open":
		var meta=JSON.parse_string(FileAccess.get_file_as_string("res://assets/mechanism.json"))
		for c in meta.controls:
			var p=c.samples[55 if core_stage=="reveal" else 100]
			model.find_child(c.name,true,false).transform=Transform3D(Basis(Quaternion(p.q[0],p.q[1],p.q[2],p.q[3])).scaled(Vector3(p.s[0],p.s[1],p.s[2])),Vector3(p.p[0],p.p[1],p.p[2]))
		model.find_child(meta.gyro.outer,true,false).rotation.y=.65
		model.find_child(meta.gyro.middle,true,false).rotation.x=1.05
		model.find_child(meta.gyro.inner,true,false).rotation.y=1.2
	var camera=Camera3D.new();world.add_child(camera)
	camera.position=Vector3(.65,3.95,7.65)
	camera.look_at(Vector3(0,1.92,0))
	camera.fov=34.0
	camera.current=true
	var we=WorldEnvironment.new();world.add_child(we)
	env=Environment.new();we.environment=env
	env.background_mode=Environment.BG_CLEAR_COLOR
	env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy=.60
	env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var sky=Sky.new();var pano=PanoramaSkyMaterial.new()
	pano.panorama=load("res://assets/studio_small_09_4k.exr")
	pano.energy_multiplier=.30
	sky.sky_material=pano;sky.radiance_size=Sky.RADIANCE_SIZE_1024
	env.sky=sky;env.sky_rotation=Vector3(0,.65,0)
	env.tonemap_mode=Environment.TONE_MAPPER_AGX
	env.tonemap_exposure=1.0
	env.ssao_enabled=true;env.ssao_radius=.12;env.ssao_intensity=1.4
	env.ssil_enabled=true;env.ssil_radius=1.0
	for d in [[Vector3(-3.2,4.8,4),24.0,Color(1,.94,.85),Vector2(2.6,4)], [Vector3(3.5,4,-2),32.0,Color(.85,.90,1),Vector2(1.2,3.5)], [Vector3(0,2.5,6),7.0,Color(1,.97,.9),Vector2(4,2)]]:
		var light=AreaLight3D.new();world.add_child(light)
		light.position=d[0];light.look_at(Vector3(0,1.8,0))
		light.light_energy=d[1];light.light_color=d[2]
		light.shadow_enabled=true;light.area_size=d[3]
		light.area_range=18;light.area_attenuation=2;light.area_normalize_energy=true
		light.light_size=.65;light.shadow_normal_bias=.10
	if mode!="baseline":
		load("res://quality_lighting.gd").apply(world,env,materials)
	var core_fx=Node3D.new();core_fx.set_script(load("res://core_vfx.gd"));world.add_child(core_fx);core_fx.setup(world)
	core_fx.trigger("ignition" if pose=="closed" else "overload" if core_stage=="overload" else "open")
	var duration=0.8 if pose=="closed" else 1.25 if core_stage=="reveal" else 1.2 if core_stage=="overload" else 4.0
	var benchmark_start=Time.get_ticks_usec()
	for i in range(80):
		core_fx.tick(duration/80.0)
		await process_frame
	print("CORE_RENDER_FRAME_MS=",(Time.get_ticks_usec()-benchmark_start)/80000.0)
	if core_stage=="arc":
		core_fx.overload_time=1.2
		core_fx._start_arc(1,1.10)
		core_fx.active_branch=true
		core_fx.tick(.02)
		await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(output)
	var fname=core_stage+"_"+pose+("_"+str(turn_angle) if turn_angle!=0 else "")
	view.get_texture().get_image().save_png(output.path_join(fname+".png"))
	print("CAPTURED "+mode)
	DirAccess.make_dir_recursive_absolute(output.path_join("lightning_frames"))
	core_fx.trigger("overload");core_fx.overload_time=1.0;core_fx.next_overload_arc=9.0;core_fx.reveal_events=3
	core_fx._start_arc(1,1.10)
	for frame in range(30):
		core_fx.tick(1.0/30.0)
		if frame==24:core_fx._start_arc(0,.90)
		await process_frame
		await RenderingServer.frame_post_draw
		view.get_texture().get_image().save_png(output.path_join("lightning_frames/%03d.png"%frame))
	var actual_positions=[]
	for p in core_fx.orbit_particles.particles:
		if float(p.life)>0:actual_positions.append([p.node.global_position.x,p.node.global_position.y,p.node.global_position.z])
	FileAccess.open(output.path_join("orbit_extent.json"),FileAccess.WRITE).store_string(JSON.stringify({"center":str(core_fx.crystal.global_position),"particle_positions":actual_positions,"count":actual_positions.size()},"  "))
	var alive_count=0
	for p in core_fx.orbit_particles.particles:
		if float(p.life)>0:alive_count+=1
	print("ORBIT_ACTIVE_AFTER_2S=",alive_count)
	var checks={}
	world.openness=1.0;world.explosion=0.0;world.power=1.0
	core_fx.trigger("overload");core_fx.overload_time=1.0;core_fx._start_arc(1,.90);core_fx.tick(.12)
	await process_frame
	await RenderingServer.frame_post_draw
	view.get_texture().get_image().save_png(output.path_join("contact_arc_open.png"))
	checks["arc_has_real_geometry"]=core_fx.arc_mesh.get_surface_count()>0
	if core_fx.arc_mesh.get_surface_count()>0:
		var arc_vertices=core_fx.arc_mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		var finite=true
		for point in arc_vertices:
			if not point.is_finite():finite=false
		checks["arc_all_vertices_finite"]=finite
		checks["arc_vertex_count"]=arc_vertices.size()
	world.explosion=.65;core_fx.tick(.033)
	checks["explosion_cancels_arcs"]=core_fx.lightning_material.get_shader_parameter("live")==0.0
	checks["explosion_cancels_corona"]=not core_fx.corona.visible
	checks["explosion_cancels_bounce"]=core_fx.bounce.light_energy==0.0
	world.explosion=0.0;core_fx.trigger("shutdown");core_fx.tick(2.2)
	checks["shutdown_core_cold"]=core_fx.surface_material.get_shader_parameter("heat")==0.0
	checks["shutdown_bounce_off"]=core_fx.bounce.light_energy==0.0
	world.openness=0.0;core_fx.trigger("ignition");core_fx.tick(.8)
	checks["reignite_restores_heat"]=core_fx.surface_material.get_shader_parameter("heat")>0.0
	checks["closed_corona_hidden"]=not core_fx.corona.visible
	world.openness=.30;core_fx.trigger("open");core_fx.tick(2.0)
	checks["no_hidden_reveal_peak"]=core_fx.surface_material.get_shader_parameter("surge")==0.0
	world.openness=.76;core_fx.tick(.033)
	checks["reveal_peak_when_visible"]=core_fx.surface_material.get_shader_parameter("surge")>.98
	world.openness=.95;core_fx.tick(.50)
	checks["reveal_holds_through_opening"]=core_fx.surface_material.get_shader_parameter("surge")>.98
	world.openness=1.0;core_fx.tick(.033);core_fx.tick(1.5)
	checks["reveal_returns_to_idle_after_settle"]=core_fx.surface_material.get_shader_parameter("surge")==0.0
	FileAccess.open("H:/model/output/helios_incubator/tests/core_vfx_verification.json",FileAccess.WRITE).store_string(JSON.stringify(checks,"  "))
	print("CORE_VFX_VERIFIED ",checks)
	quit()

func collect(node:Node) -> void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var m=node.get_active_material(i)
			if m is StandardMaterial3D and not (m.resource_name.contains("Solar_Core") or m.resource_name.contains("Amber_Light")):
				var key:String=m.resource_name
				if not materials.has(key):
					var sm=ShaderMaterial.new();sm.shader=load("res://surface.gdshader")
					if mode.contains("twosided"):
						var ss=Shader.new();ss.code=FileAccess.get_file_as_string("res://surface.gdshader").replace("render_mode diffuse_burley", "render_mode cull_disabled, diffuse_burley");sm.shader=ss
					sm.set_shader_parameter("base_color",m.albedo_color)
					sm.set_shader_parameter("metalness",m.metallic)
					sm.set_shader_parameter("surface_roughness",m.roughness)
					sm.set_shader_parameter("use_color_map",m.albedo_texture!=null)
					sm.set_shader_parameter("use_rough_map",m.roughness_texture!=null)
					sm.set_shader_parameter("use_normal_map",m.normal_texture!=null)
					if m.albedo_texture: sm.set_shader_parameter("color_map",m.albedo_texture)
					if m.roughness_texture: sm.set_shader_parameter("rough_map",m.roughness_texture)
					if m.normal_texture: sm.set_shader_parameter("normal_map",m.normal_texture)
					sm.set_shader_parameter("normal_depth",.12)
					sm.set_shader_parameter("coat",.26 if key=="Ivory_Enamel" else .07 if key=="Cherry_Enamel" else 0.0)
					materials[key]=sm
					print(key," color=",m.albedo_color," rough=",m.roughness," roughchannel=",m.roughness_texture_channel)
				node.set_surface_override_material(i,materials[key])
	for child in node.get_children(): collect(child)
