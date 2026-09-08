extends SceneTree

var host:Node3D
var frames:Array=[]
var output:="H:/model/output/helios_incubator/review/pressure_integrated_continuous"
var recording:=false
var ended:=false
var physics_manifest:=""
var quality_profile:="balanced"
var no_tail_fade:=false
var light_checks:=false

func _initialize()->void:
	for a in OS.get_cmdline_user_args():
		if a=="--record-frames":recording=true
		if a.begins_with("--physics-manifest="):physics_manifest=a.trim_prefix("--physics-manifest=")
		if a.begins_with("--output="):output=a.trim_prefix("--output=")
		if a.begins_with("--quality="):quality_profile=a.trim_prefix("--quality=")
		if a=="--no-tail-fade":no_tail_fade=true
		if a=="--light-checks":light_checks=true
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32)
	call_deferred("run")

func run()->void:
	var scene:Node=load("res://main.tscn").instantiate()
	root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop")
	await physics_frame
	await process_frame
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);root.unfocusable=true
	host.set_process(false)
	if not physics_manifest.is_empty():assert(host.effects.pressure.load_physics_manifest(physics_manifest))
	host.effects.pressure.set_quality(quality_profile)
	if no_tail_fade:host.effects.pressure.physics_tail_fade=0.0
	RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	host.rotation_enabled=false;host.angle=0.0;host.power=1.0;host.power_target=1.0
	host.toast_timer=0.0;host.muted=true
	DirAccess.make_dir_recursive_absolute(output)
	if recording:DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	for i in range(120):host._process(1.0/30.0)
	for i in range(5):await process_frame
	await capture("00_ceramic_closed")
	if recording:
		for i in range(30):
			host._process(1.0/30.0);await process_frame;await RenderingServer.frame_post_draw
			host.render_view.get_texture().get_image().save_png(output.path_join("frames/%04d.png"%i))
	host.activate(1)
	for i in range(1,151):
		var start:=Time.get_ticks_usec()
		host._process(1.0/30.0)
		await process_frame
		await RenderingServer.frame_post_draw
		frames.append({"frame":i,"open":host.openness,"pressure_volumes":host.effects.pressure.active_volume_count,"frame_ms":(Time.get_ticks_usec()-start)/1000.0,"gpu_ms":RenderingServer.viewport_get_measured_render_time_gpu(host.render_view.get_viewport_rid()),"cpu_render_ms":RenderingServer.viewport_get_measured_render_time_cpu(host.render_view.get_viewport_rid())})
		if i in [9,15,21,33,45,66,75,90,105,120,150]:await capture("activation_%03d"%i)
		if recording:host.render_view.get_texture().get_image().save_png(output.path_join("frames/%04d.png"%(i+29)))
	FileAccess.open(output.path_join("timing.json"),FileAccess.WRITE).store_string(JSON.stringify(frames,"  "))
	print("PRESSURE_INTEGRATED_COMPARISON_READY")
	quit()

func capture(name_string:String)->void:
	await process_frame
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join(name_string+".png"))
	if light_checks and name_string=="activation_033":
		var old_power:float=host.power
		var old_color:Color=host.effects.core.bounce.light_color
		var before_time:float=host.effects.pressure.physics_time
		host.power=0.0;host.effects.core.tick(0.0);host.effects.pressure.tick(0.0)
		await process_frame;await RenderingServer.frame_post_draw
		host.render_view.get_texture().get_image().save_png(output.path_join("same_density_core_off.png"))
		var off_energy:float=host.effects.pressure.material.get_shader_parameter("core_light_energy")
		host.power=old_power;host.effects.core.tick(0.0)
		host.effects.core.bounce.light_color=Color(.07,.34,1.0);host.effects.pressure.tick(0.0)
		await process_frame;await RenderingServer.frame_post_draw
		host.render_view.get_texture().get_image().save_png(output.path_join("same_density_blue_light.png"))
		FileAccess.open(output.path_join("core_light_checks.json"),FileAccess.WRITE).store_string(JSON.stringify({"core_off_scatter_energy":off_energy,"cache_time_unchanged":is_equal_approx(before_time,host.effects.pressure.physics_time),"blue_light_color":str(host.effects.pressure.material.get_shader_parameter("core_light_color"))},"  "))
		host.effects.core.bounce.light_color=old_color;host.effects.core.tick(0.0);host.effects.pressure.tick(0.0)
		await process_frame;await RenderingServer.frame_post_draw
	if name_string in ["activation_021","activation_045"]:
		var camera:Camera3D=host.camera;var home:=camera.global_transform
		var focus:=Vector3(0,1.92,0)
		camera.position=focus+Basis(Vector3.UP,PI/6.0)*(camera.position-focus);camera.look_at(focus)
		await process_frame;await RenderingServer.frame_post_draw
		host.render_view.get_texture().get_image().save_png(output.path_join(name_string+"_camera30.png"))
		camera.global_transform=home
		await process_frame;await RenderingServer.frame_post_draw
