extends SceneTree
var host:Node3D
var output:="H:/model/output/helios_incubator/review/steam_prewarm"
var samples:Array=[]
func _initialize()->void:
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);root.unfocusable=true
	call_deferred("run")
func run()->void:
	DirAccess.make_dir_recursive_absolute(output)
	var t0:=Time.get_ticks_usec()
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop")
	await physics_frame;await process_frame
	host.set_process(false);host.rotation_enabled=false;host.angle=0.0;host.power=0;host.power_target=0;host.muted=true
	var p:Node3D=host.effects.pressure
	RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	for i in range(35):host._process(1.0/60.0);await process_frame
	await RenderingServer.frame_post_draw
	var pre_burst:Dictionary=p.compute_effect.get_diagnostics();var pre_idle:Dictionary=p.idle_controller.compositor.get_diagnostics()
	host.render_view.get_texture().get_image().save_png(output.path_join("prewarm_invisible.png"))
	p.compute_effect.enabled=false;p.idle_controller.compositor.enabled=false
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join("no_compositor.png"))
	p.compute_effect.enabled=true;p.idle_controller.compositor.enabled=true
	host.power=1;host.power_target=1;host.activate(1)
	for i in range(150):
		var started:=Time.get_ticks_usec()
		host._process(1.0/60.0);await process_frame;await RenderingServer.frame_post_draw
		samples.append({"frame":i,"wall_ms":(Time.get_ticks_usec()-started)/1000.0,"gpu_ms":RenderingServer.viewport_get_measured_render_time_gpu(host.render_view.get_viewport_rid()),"burst":p.burst_active})
	var after:Dictionary=p.compute_effect.get_diagnostics()
	var report:Dictionary={"startup_total_ms":(Time.get_ticks_usec()-t0)/1000.0,"before_first_button":{"burst":pre_burst,"idle":pre_idle},"after_first_button":{"burst":after,"idle":p.idle_controller.compositor.get_diagnostics()},"no_allocation_on_button":after.allocation_count==pre_burst.allocation_count,"no_visible_prewarm_writes":pre_burst.warmup_visible_writes==0 and pre_idle.warmup_visible_writes==0,"samples":samples}
	FileAccess.open(output.path_join("timing.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("STEAM_PREWARM_PROBE_DONE ",report.no_allocation_on_button," ",report.no_visible_prewarm_writes);quit()
