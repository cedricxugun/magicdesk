extends SceneTree

var world: Node3D
var view: SubViewport
var env: Environment
var materials := {}
var model: Node3D
var mode := "final"
var pose := "closed"
var turn_angle := 0.0
var output := "H:/model/output/helios_incubator/review/pressure_probe"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
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
	view.size=Vector2i(1920,1400)
	if pose=="open":view.size.x=2200
	view.transparent_bg=true
	view.own_world_3d=true
	view.msaa_3d=Viewport.MSAA_4X
	view.use_taa=false
	view.scaling_3d_scale=1.20
	view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	world=PressureHost.new(); view.add_child(world)
	model=load("res://assets/helios_model.glb").instantiate()
	world.add_child(model)
	world.model=model
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
	camera.fov=rad_to_deg(2.0*atan(1400.0/(2.0*1540.0)))
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

	Engine.max_fps=0
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	DirAccess.make_dir_recursive_absolute(output)
	var pressure=load("res://pressure_vfx.gd").new();world.add_child(pressure);pressure.setup(world)
	for i in range(45):await process_frame
	var baseline_start:=Time.get_ticks_usec()
	for i in range(45):await process_frame
	var baseline_ms:float=(Time.get_ticks_usec()-baseline_start)/45000.0
	var meta=JSON.parse_string(FileAccess.get_file_as_string("res://assets/mechanism.json"))
	pressure.trigger("open")
	var milestone:=[6,14,21,30,45,84,114]
	var samples: Array=[]
	for frame in range(1,125):
		var started:=Time.get_ticks_usec()
		var t:=frame/30.0
		world.openness=0.0 if t<.32 else lerpf(0.0,.035,smoothstep(.32,.70,t)) if t<.70 else lerpf(.035,.84,smoothstep(.70,1.5,t)) if t<1.5 else lerpf(.84,1.0,smoothstep(1.5,2.2,t))
		for c in meta.controls:
			var v:float=world.openness
			if int(c.petal)>=0:v=smoothstep(0.0,1.0,(v-float(c.petal)*.045)/.775)
			var pos:=clampf(v*100,0,100);var lo:=int(pos)
			var a=c.samples[lo];var b=c.samples[mini(100,lo+1)]
			var aa=Transform3D(Basis(Quaternion(a.q[0],a.q[1],a.q[2],a.q[3])).scaled(Vector3(a.s[0],a.s[1],a.s[2])),Vector3(a.p[0],a.p[1],a.p[2]))
			var bb=Transform3D(Basis(Quaternion(b.q[0],b.q[1],b.q[2],b.q[3])).scaled(Vector3(b.s[0],b.s[1],b.s[2])),Vector3(b.p[0],b.p[1],b.p[2]))
			world.named(c.name).transform=aa.interpolate_with(bb,pos-lo)
		model.find_child(meta.gyro.outer,true,false).rotation.y=.65+t*.2
		model.find_child(meta.gyro.middle,true,false).rotation.x=1.05
		model.find_child(meta.gyro.inner,true,false).rotation.y=1.2+t*.3
		pressure.tick(1.0/30.0)
		await process_frame
		await RenderingServer.frame_post_draw
		var ms:float=(Time.get_ticks_usec()-started)/1000.0
		samples.append({"time":t,"frame_ms":ms,"volumes":pressure.active_volume_count})
		if milestone.has(frame):
			view.get_texture().get_image().save_png(output.path_join("pressure_%03d.png"%frame))
			print("PRESSURE_CAPTURE ",frame," volumes=",pressure.active_volume_count," ms=",ms)
	FileAccess.open(output.path_join("performance.json"),FileAccess.WRITE).store_string(JSON.stringify({"viewport":[1920,1400],"baseline_frame_ms":baseline_ms,"peak_volumes":pressure.peak_active_volumes,"frames":samples},"  "))
	var settled_clean:bool=pressure.active_volume_count==0 and pressure.events.is_empty()
	pressure.trigger("open")
	for i in range(55):pressure.tick(.01)
	var before:Dictionary={}
	for p in pressure.particles:
		if p.life>0:before[p.node.name]={"position":p.node.position,"scale":p.node.scale}
	pressure.trigger("close");pressure.tick(.001)
	var maximum_shift:=0.0;var maximum_scale_change:=0.0
	for p in pressure.particles:
		if before.has(p.node.name):
			maximum_shift=maxf(maximum_shift,p.node.position.distance_to(before[p.node.name].position))
			maximum_scale_change=maxf(maximum_scale_change,p.node.scale.distance_to(before[p.node.name].scale))
	for i in range(12):
		pressure.trigger(["open","close","overload","shutdown","explode"][i%5]);pressure.tick(.13)
	for i in range(500):pressure.tick(.01)
	FileAccess.open(output.path_join("state_tests.json"),FileAccess.WRITE).store_string(JSON.stringify({"settles_after_3_8s":settled_clean,"cancel_position_step":maximum_shift,"cancel_scale_step":maximum_scale_change,"pool_bounded":pressure.peak_active_volumes<=84,"clean_after_interrupts":pressure.active_volume_count==0 and pressure.events.is_empty()},"  "))
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

class PressureHost extends Node3D:
	var model: Node3D
	var openness:=0.0
	var power:=1.0
	var explosion:=0.0
	var shutdown_time:=-1.0
	func named(n: String) -> Node3D:return model.find_child(n,true,false) as Node3D
