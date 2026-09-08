extends SceneTree

var world: Node3D
var view: SubViewport
var env: Environment
var materials := {}
var model: Node3D
var mode := "baseline"
var pose := "closed"
var turn_angle := 0.0
var output := "H:/model/output/helios_incubator/review/lighting_compare"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--mode="): mode=arg.trim_prefix("--mode=")
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
	view.scaling_3d_scale=1.20
	view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	world=Node3D.new(); view.add_child(world)
	model=load("res://assets/helios_model.glb").instantiate()
	world.add_child(model)
	collect(model)
	model.find_child("TURNTABLE",true,false).rotation.y=turn_angle
	if pose=="open":
		var meta=JSON.parse_string(FileAccess.get_file_as_string("res://assets/mechanism.json"))
		for c in meta.controls:
			var p=c.samples[100]
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
	for i in range(40): await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(output)
	var fname=mode+"_"+pose+("_"+str(turn_angle) if turn_angle!=0 else "")
	view.get_texture().get_image().save_png(output.path_join(fname+".png"))
	print("CAPTURED "+mode)
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
