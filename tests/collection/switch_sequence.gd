extends SceneTree
var host:Node3D
var service:Node3D
var output:=""
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func pause(seconds:float)->void:await create_timer(seconds).timeout
func check(label:String,value:bool,detail:Variant="")->void:
	checks.append({"check":label,"passed":value,"detail":str(detail)});print("SWITCH_SEQUENCE ",label," ",value," ",detail)
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(label+".png"))
func click(point:Vector2)->void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=point;event.pressed=true
	Input.parse_input_event(event);await process_frame;event=event.duplicate();event.pressed=false;Input.parse_input_event(event);await process_frame
func until(predicate:Callable,seconds:float=25)->bool:
	var start:=Time.get_ticks_msec()
	while not predicate.call():
		if Time.get_ticks_msec()-start>seconds*1000:return false
		await process_frame
	return true
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="):output=arg.trim_prefix("--capture=")
	if output.is_empty():quit(2);return
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene;host=scene.get_node("Render/HeliosDesktop")
	await pause(2);host.rotation_enabled=false;host.angle=0;service=host.collection
	await physics_frame;await physics_frame
	var window_before:=Rect2i(root.position,root.size);var camera_before:Transform3D=host.camera.global_transform
	await capture("01_cowl_closed")
	var radians:=deg_to_rad(-132.0);var world:=Vector3(1.521*cos(radians),.65,-1.521*sin(radians))
	var point:Vector2=host.camera.unproject_position(world);var hit:Dictionary=service._selector_ray(point)
	check("visible_porcelain_cowl_is_entry",not hit.is_empty() and hit.collider.has_meta("entry"),hit.get("position","no hit"))
	await click(point);await pause(.5);check("cowl_opening_has_intermediate_pose",service.selector_amount>.05 and service.selector_amount<.8,service.selector_amount);await capture("02_cowl_unlatching")
	await pause(.7);await capture("03_rail_extending")
	check("plaque_deployment",await until(func():return service.selector_amount>.999,5));await capture("04_plaques_deployed");await pause(.5)
	var card:Dictionary=service.card_nodes[2]
	point=host.camera.unproject_position(card.node.to_global(Vector3(0,.21,.02)))
	await click(point);await pause(.30);await capture("05_plaque_reading")
	check("archive_started",await until(func():return service.state=="archiving"));await pause(.65);await capture("06_archive_wire_scan")
	check("recast_started",await until(func():return service.state=="revealing"));await pause(.8);await capture("07_recast_wire_scan")
	check("switch_to_G",await until(func():return service.state=="idle" and service.active_id=="G"));await capture("08_G_arrived")
	service.toggle_selector();check("reopen_archive",await until(func():return service.selector_amount>.999));await pause(.4)
	service.toggle_selector();await pause(.7);check("retraction_has_intermediate_pose",service.selector_amount>.1 and service.selector_amount<.9,service.selector_amount);await capture("09_plaques_retracting")
	check("retraction_finishes",await until(func():return service.selector_amount<.001));await capture("10_cowl_resealed")
	check("base_and_camera_fixed",Rect2i(root.position,root.size)==window_before and host.camera.global_transform.is_equal_approx(camera_before))
	check("single_base",service.diagnostics().base_instances==1)
	var report:={"all_passed":checks.all(func(x):return x.passed),"checks":checks,"rendered_sequence":true,"not_a_performance_benchmark":OS.get_cmdline_args().has("--write-movie")}
	FileAccess.open(output.path_join("report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	await pause(.8);quit(0 if report.all_passed else 2)
