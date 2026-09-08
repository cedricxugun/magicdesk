extends SceneTree
var host:Node3D
var markings:Node3D
var managed:=false
var output:="H:/model/output/helios_incubator/review/shell_marking"
var report:Dictionary={"poses":{},"frames":[]}

func _initialize()->void:
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);call_deferred("run")

func advance(delta:float)->void:
	host._process(delta)
	if not managed:markings.tick(delta)
	await process_frame;await RenderingServer.frame_post_draw
	report.frames.append(RenderingServer.viewport_get_measured_render_time_gpu(host.render_view.get_viewport_rid()))

func capture(label:String)->void:
	await process_frame;await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join(label+".png"))
	var position_error:=0.0;var offset_error:=0.0
	var parents:=true
	for m in markings.markings:
		parents=parents and m.node.get_parent()==m.source
		position_error=maxf(position_error,m.node.global_transform.origin.distance_to(m.source.global_transform.origin))
		var source_arrays:Array=m.source.mesh.surface_get_arrays(m.surface)
		var overlay_arrays:Array=m.node.mesh.surface_get_arrays(0)
		var old:PackedVector3Array=source_arrays[Mesh.ARRAY_VERTEX]
		var new:PackedVector3Array=overlay_arrays[Mesh.ARRAY_VERTEX]
		for i in range(old.size()):offset_error=maxf(offset_error,absf(old[i].distance_to(new[i])-.00045))
	report.poses[label]={"parents_correct":parents,"transform_origin_error":position_error,"normal_offset_max_error":offset_error,"module":markings.get_diagnostics()}

func run()->void:
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop")
	await physics_frame;await process_frame
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32);root.unfocusable=true
	host.set_process(false);host.rotation_enabled=false;host.angle=0.0;host.power=1.0;host.power_target=1.0;host.muted=true;host.toast_timer=0.0
	host.activation_time=-1.0;host.activation_display_time=-1.0
	if host.effects.pressure.compute_effect:host.effects.pressure.compute_effect.enabled=false
	if host.effects.pressure.idle_controller:host.effects.pressure.idle_controller.compositor.enabled=false
	for node in host.find_children("*","Node3D",true,false):
		var script:Script=node.get_script()
		if script!=null and script.resource_path=="res://shell_marking_vfx.gd":markings=node;managed=true;break
	if markings==null:
		markings=load("res://shell_marking_vfx.gd").new();host.add_child(markings);markings.setup(host)
	RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	markings.trigger("ignition")
	for i in range(1,46):
		await advance(1.0/30.0)
		if i==9:await capture("01_ignition_latch")
		if i==21:await capture("02_ignition_crown")
	await capture("03_steady_closed")
	host.openness=1.0;markings.trigger("open")
	for i in range(21):await advance(1.0/30.0)
	await capture("04_open_peak")
	markings.trigger("overload");host.overload=5.0
	for i in range(20):await advance(1.0/30.0)
	await capture("05_overload")
	host.overload=0.0;markings.trigger("shutdown")
	for i in range(1,38):
		await advance(1.0/30.0)
		if i==12:await capture("06_shutdown_reverse")
	await capture("07_shutdown_off")
	var all_off:=true
	for m in markings.markings:all_off=all_off and float(m.material.get_shader_parameter("energy"))==0.0 and float(m.material.get_shader_parameter("scan_energy"))==0.0
	report.shutdown_all_off=all_off
	host.explosion=1.0;host.openness=0.0;markings.trigger("explode")
	for i in range(4):await advance(1.0/30.0)
	await capture("08_exploded_alignment")
	report.module=markings.get_diagnostics()
	FileAccess.open(output.path_join("report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("SHELL_MARKING_COMPLETE ",report.module," shutdown=",all_off)
	quit()
