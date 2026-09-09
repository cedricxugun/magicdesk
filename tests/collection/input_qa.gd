extends SceneTree
var host:Node3D
var service:Node3D
var checks:Array=[]
var output:=""
func _initialize()->void:run.call_deferred()
func check(label:String,passed:bool,detail:Variant="")->void:
	checks.append({"check":label,"passed":passed,"detail":str(detail)});print("INPUT_QA ",label," ",passed," ",detail)
func pause(seconds:float)->void:await create_timer(seconds).timeout
func until(predicate:Callable,timeout:float=20.0)->bool:
	var started:=Time.get_ticks_msec()
	while not predicate.call():
		if Time.get_ticks_msec()-started>timeout*1000:return false
		await process_frame
	return true
func click(point:Vector2)->void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=point;event.pressed=true
	Input.parse_input_event(event);await process_frame
	event=event.duplicate();event.pressed=false;Input.parse_input_event(event);await process_frame
func run()->void:
	set_meta("collection_skip_intro",true)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="):output=arg.trim_prefix("--capture=")
	if output.is_empty():output=get_script().resource_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene;host=scene.get_node("Render/HeliosDesktop")
	await pause(2.5);service=host.collection;host.rotation_enabled=false;host.angle=0
	await physics_frame;await physics_frame
	var entry:=Vector3(-.728,.640,1.095)
	var screen:Vector2=host.camera.unproject_position(entry)
	var hit:Dictionary=service._selector_ray(screen)
	var samples:=0;var reachable:=0
	for radius in [1.295,1.315,1.340]:
		for angle in [-131,-127,-123,-119,-115]:
			samples+=1
			var a:=deg_to_rad(float(angle));var point:=Vector3(radius*cos(a),.640,-radius*sin(a))
			var target:Vector2=host.camera.unproject_position(point);var result:Dictionary=service._selector_ray(target)
			if not result.is_empty() and result.collider.has_meta("entry"):reachable+=1;screen=target
	check("entry_real_surface",reachable>0,{"reachable":reachable,"samples":samples})
	await click(screen);check("entry_click_opens",await until(func():return service.selector_amount>.999,3))
	for i in range(service.card_nodes.size()):
		var card:Dictionary=service.card_nodes[i]
		var point:Vector2=host.camera.unproject_position(card.node.to_global(Vector3(0,.21,.02)))
		var actual:Dictionary=service._selector_ray(point)
		check("card_"+str(i)+"_hit",not actual.is_empty() and actual.collider.get_meta("card_slot",-1)==i)
	var before:int=service.browse_start
	var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_DOWN;wheel.pressed=true;wheel.position=screen
	Input.parse_input_event(wheel);await pause(.7)
	check("wheel_advances_index",service.browse_start==posmod(before+1,service.registry.size()))
	if "--entry-only" in OS.get_cmdline_user_args():
		var report:={"all_passed":checks.all(func(x):return x.passed),"checks":checks}
		FileAccess.open(output.path_join("entry_report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "));quit(0 if report.all_passed else 2);return
	var card:Dictionary=service.card_nodes[0]
	await click(host.camera.unproject_position(card.node.to_global(Vector3(0,.21,.02))))
	check("card_click_selects_F",await until(func():return service.state=="idle" and service.active_id=="F"))
	for definition in service.registry:
		if definition.id=="B":continue
		service.request_model(definition.id);await until(func():return service.state=="idle" and service.active_id==definition.id)
		await pause(.1)
		for i in range(7):
			var target:Vector3=service.action_anchor(i)
			if i in [0,6]:target=host.buttons[i].cap.to_global(Vector3(0,.008,0))
			else:target+=Vector3(target.x,0,target.z).normalized()*.070
			var point:Vector2=host.camera.unproject_position(target)
			check(str(definition.id)+"_control_"+str(i),host.hit_button(point)==i,host.hit_button(point))
	var old:String=service.active_id
	service.request_model("NOT_REGISTERED");await process_frame
	check("unknown_id_keeps_current",service.active_id==old and service.state=="idle")
	service.request_model("F")
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;service.consume_input(escape)
	await pause(.5);check("cancel_keeps_current",service.active_id==old and service.state=="idle")
	var result:={"all_passed":checks.all(func(x):return x.passed),"checks":checks}
	FileAccess.open(output.path_join("input_report.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
	print("INPUT_QA_RESULT ",result.all_passed);quit(0 if result.all_passed else 2)
