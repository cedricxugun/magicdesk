extends SceneTree

var host:Node3D
var effect:CompositorEffect
var output:="H:/model/output/helios_incubator/review/steam_compute"
var frames:Array=[]
var scale:=.5
var mode:="compute"
var pressure:Node3D
var checks:=false

func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		if arg.begins_with("--volume-scale="):scale=float(arg.trim_prefix("--volume-scale="))
		if arg.begins_with("--steam-mode="):mode=arg.trim_prefix("--steam-mode=")
		if arg=="--checks":checks=true
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32)
	call_deferred("run")

func update_snapshot()->void:
	var m:ShaderMaterial=pressure.material
	var mn:Vector3=m.get_shader_parameter("bounds_lower")
	var mx:Vector3=m.get_shader_parameter("bounds_upper")
	var snapshot:Dictionary={
		"active":pressure.active_volume_count>0,"frame_a":m.get_shader_parameter("density_frame_a"),"frame_b":m.get_shader_parameter("density_frame_b"),
		"mix":m.get_shader_parameter("physical_mix"),"gain":m.get_shader_parameter("physical_gain"),
		"bounds_min":pressure.physics_bounds.position,"bounds_max":pressure.physics_bounds.end,"world_bounds":AABB(mn,mx-mn),
		"cache_to_world":host.named("TURNTABLE").global_transform,"density_scale":m.get_shader_parameter("physical_density_scale"),
		"step":m.get_shader_parameter("physical_step"),"max_steps":m.get_shader_parameter("max_march_steps"),"resolution_scale":scale,
		"core_position":m.get_shader_parameter("core_light_position"),"core_color":m.get_shader_parameter("core_light_color"),
		"core_energy":m.get_shader_parameter("core_light_energy"),"core_range":m.get_shader_parameter("core_light_range"),"core_shadow_steps":3}
	if bool(m.get_shader_parameter("physical_occupancy_enabled")):
		snapshot.occupancy=m.get_shader_parameter("physical_occupancy")
		snapshot.occupancy_size=m.get_shader_parameter("physical_occupancy_size")
	effect.configure(snapshot)

func run()->void:
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop")
	await physics_frame;await process_frame
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);root.unfocusable=true
	host.set_process(false);host.rotation_enabled=false;host.angle=0.0
	host.power=1.0;host.power_target=1.0;host.toast_timer=0.0;host.muted=true
	pressure=host.effects.pressure
	assert(pressure.load_physics_manifest("res://assets/pressure_physics_ground128/manifest.json"))
	pressure.set_quality("balanced")
	effect=load("res://steam_compositor.gd").new()
	var compositor:=Compositor.new();compositor.compositor_effects=[effect]
	host.camera.compositor=compositor
	pressure.volume.visible=mode!="compute"
	effect.enabled=mode=="compute"
	RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	for i in range(30):host._process(1.0/30.0)
	update_snapshot()
	for i in range(10):await process_frame
	host.activate(1)
	for i in range(1,151):
		host._process(1.0/30.0);update_snapshot()
		await process_frame;await RenderingServer.frame_post_draw
		frames.append({"frame":i,"gpu_ms":RenderingServer.viewport_get_measured_render_time_gpu(host.render_view.get_viewport_rid()),"cpu_ms":RenderingServer.viewport_get_measured_render_time_cpu(host.render_view.get_viewport_rid())})
		if i in [15,21,33,45,66,90,120]:
			host.render_view.get_texture().get_image().save_png(output.path_join("frame_%03d.png"%i))
		if i==45 and checks:await extra_checks()
	var report:Dictionary={"mode":mode,"scale":scale,"effect":effect.get_diagnostics(),"frames":frames}
	FileAccess.open(output.path_join("timing.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("STEAM_COMPUTE_PROBE ",report.effect)
	quit()

func stable_capture(label:String)->void:
	for k in range(3):await process_frame
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join(label+".png"))

func extra_checks()->void:
	await stable_capture("steady_a")
	await stable_capture("steady_b")
	var saved_color:Color=pressure.material.get_shader_parameter("core_light_color")
	var saved_energy:float=pressure.material.get_shader_parameter("core_light_energy")
	pressure.material.set_shader_parameter("core_light_energy",0.0);update_snapshot()
	await stable_capture("core_off")
	pressure.material.set_shader_parameter("core_light_energy",saved_energy)
	pressure.material.set_shader_parameter("core_light_color",Color(.08,.35,1.0));update_snapshot()
	await stable_capture("core_blue")
	pressure.material.set_shader_parameter("core_light_color",saved_color);update_snapshot()
	var camera:Camera3D=host.camera;var camera_home:=camera.global_transform
	var focus:=Vector3(0,1.92,0)
	camera.position=focus+Basis(Vector3.UP,PI/6.0)*(camera.position-focus);camera.look_at(focus)
	await stable_capture("camera_30")
	camera.global_transform=camera_home
	var original_size:Vector2i=host.render_view.size
	host.render_view.size=Vector2i(1280,960)
	await stable_capture("resized_1280")
	host.render_view.size=original_size
	await stable_capture("resized_restored")
	var saved_gain:float=pressure.material.get_shader_parameter("physical_gain")
	pressure.material.set_shader_parameter("physical_gain",0.0);update_snapshot()
	await stable_capture("gain_zero")
	pressure.material.set_shader_parameter("physical_gain",saved_gain);update_snapshot()
	await stable_capture("gain_restored")
