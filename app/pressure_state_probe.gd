extends SceneTree
var host:Node3D
var checks:Array=[]
var output:="H:/model/output/helios_incubator/review/steam_state_gate"
func _initialize()->void:
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);root.unfocusable=true
	call_deferred("run")
func advance(frames:int)->void:
	for i in range(frames):
		host._process(1.0/30.0);await process_frame
func record(name:String,passed:bool)->void:
	checks.append({"name":name,"passed":passed});print(name," ",passed)
func shot(name:String)->void:
	await process_frame;await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join(name+".png"))
func run()->void:
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop");await physics_frame;await process_frame
	root.position=Vector2i(-32000,-32000);host.set_process(false)
	host.rotation_enabled=false;host.angle=0.0;host.power=1.0;host.power_target=1.0;host.muted=true
	var p:Node3D=host.effects.pressure
	await advance(75)
	record("startup_never_starts_ground_steam",not p.physics_playing and not p.burst_active)
	await shot("startup_no_ground_steam")
	host.activate(2);await advance(45)
	record("closed_overload_never_starts_ground_steam",not p.physics_playing and not p.burst_active)
	host.overload=0.0;host.change_pose(0.0,0.0,.25);host.effects.trigger("close");await advance(15)
	host.activate(1)
	for i in range(1,241):
		host._process(1.0/30.0);await process_frame
		if i in [21,45,90,120,180,240]:await shot("open_%03d"%i)
		if i==45:
			var before:float=p.physics_time
			p.trigger("open");record("duplicate_open_does_not_restart_cache",is_equal_approx(p.physics_time,before))
			p.trigger("overload");record("active_overload_does_not_restart_cache",is_equal_approx(p.physics_time,before))
	record("natural_tail_finishes",not p.physics_playing and not p.burst_active)
	host.activate(2);await advance(30)
	record("spent_open_overload_does_not_restart",not p.physics_playing)
	host.overload=0.0;host.activate(1);await advance(110)
	record("close_does_not_create_new_steam",not p.physics_playing)
	p.trigger("shutdown");await advance(10)
	record("inactive_shutdown_does_not_create_steam",not p.physics_playing)
	await shot("closed_no_retrigger")
	FileAccess.open(output.path_join("checks.json"),FileAccess.WRITE).store_string(JSON.stringify({"tests":checks,"all_passed":checks.all(func(c):return c.passed),"compute":p.compute_effect.get_diagnostics()},"  "))
	quit()
