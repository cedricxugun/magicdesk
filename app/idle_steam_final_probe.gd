extends SceneTree
var host:Node3D
var idle:Node3D
var records:Array=[]
var output:="H:/model/output/helios_incubator/review/idle_steam_final"

func _initialize()->void:
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32)
	call_deferred("run")

func frame(delta:float)->void:
	host._process(delta)
	await process_frame;await RenderingServer.frame_post_draw
	var angles:PackedFloat32Array=idle.get_birth_angles()
	records.append({"time":idle.clock,"yaw":host.angle,"birth_0":angles[0],"birth_2":angles[20],"birth_4":angles[40],"gain":idle.gain,"source_off_elapsed":idle.source_off_elapsed,"idle_active":idle.idle_active,"burst":host.effects.pressure.is_burst_active(),"gpu_ms":RenderingServer.viewport_get_measured_render_time_gpu(host.render_view.get_viewport_rid())})

func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join(label+".png"))

func run()->void:
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop")
	await physics_frame;await process_frame
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);root.unfocusable=true
	host.set_process(false);host.rotation_enabled=false;host.angle=0.0
	host.power=1.0;host.power_target=1.0;host.toast_timer=0.0;host.muted=true
	host.activation_time=-1.0;host.activation_display_time=-1.0
	var pressure:Node3D=host.effects.pressure
	pressure.physics_playing=false;pressure.burst_active=false;pressure.burst_latched=false;pressure.physics_fade=0.0;pressure.physics_time=-1.0;pressure.physics_pending=""
	idle=pressure.idle_controller
	assert(idle!=null and idle.physics_frames.size()==18)
	RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	for i in range(60):await frame(1.0/30.0)
	await capture("00_idle")
	for i in range(90):
		host.angle+=.6/30.0;await frame(1.0/30.0)
	await capture("01_rotate")
	for i in range(60):await frame(1.0/30.0)
	await capture("02_pause")
	for i in range(90):
		host.angle-=.6/30.0;await frame(1.0/30.0)
	await capture("03_reverse")
	host.power_target=0.0
	for i in range(1,28):
		await frame(1.0/30.0)
		if i in [1,3,9,18,27]:await capture("off_%02d"%i)
	var report:Dictionary={"idle":idle.get_diagnostics(),"records":records}
	FileAccess.open(output.path_join("report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("IDLE_FINAL_GPU_DONE ",idle.get_diagnostics())
	quit()
