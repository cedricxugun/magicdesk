extends SceneTree
## Tests the actual scene and captures its real transparent desktop viewport.
var host:Node3D
var service:Node3D
var checks:Array=[]
var output:=""
var initial_window:Rect2i
var initial_camera:Transform3D
var initial_fov:float
var initial_base:Transform3D
var model_filter:=PackedStringArray()
var measuring:=""
var performance:Dictionary={}

func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:
	if not measuring.is_empty():performance[measuring].append(delta*1000.)
	return false
func check(label:String,passed:bool,detail:Variant="")->void:
	checks.append({"check":label,"passed":passed,"detail":str(detail)})
	print("COLLECTION_QA ",label," ",passed," ",detail)
func until(predicate:Callable,timeout:float=18.0)->bool:
	var started:=Time.get_ticks_msec()
	while not predicate.call():
		if Time.get_ticks_msec()-started>timeout*1000:return false
		await process_frame
	return true
func pause(seconds:float)->void:await create_timer(seconds).timeout
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	var img:=root.get_texture().get_image()
	img.save_png(output.path_join(label+".png"))
	var used:=img.get_used_rect()
	check(label+"_visible",used.size.x>100 and used.size.y>100,used)
	check(label+"_transparent",img.get_pixel(0,0).a<.01)
	check(label+"_stable",Rect2i(root.position,root.size)==initial_window and host.camera.global_transform.is_equal_approx(initial_camera) and is_equal_approx(host.camera.fov,initial_fov) and host.fixed_base.global_transform.is_equal_approx(initial_base))
	check(label+"_one_base",service.diagnostics().base_instances==1)
	FileAccess.open(output.path_join(label+".json"),FileAccess.WRITE).store_string(JSON.stringify(service.diagnostics(),"  "))
	if service.active_id=="L":
		var poses:Dictionary={}
		for item in service.current.parts+service.current.controls+service.current.motions:
			var transform:Transform3D=item.node.global_transform
			poses[str(item.node.name)]={"p":[transform.origin.x,transform.origin.y,transform.origin.z],"basis":[[transform.basis.x.x,transform.basis.x.y,transform.basis.x.z],[transform.basis.y.x,transform.basis.y.y,transform.basis.y.z],[transform.basis.z.x,transform.basis.z.y,transform.basis.z.z]]}
		FileAccess.open(output.path_join(label+"_rig.json"),FileAccess.WRITE).store_string(JSON.stringify(poses))
func check_home(id:String,module:Node3D)->void:
	var error:=0.0
	for part in module.parts:
		error=maxf(error,part.node.transform.origin.distance_to(part.home.origin))
		for axis in range(3):error=maxf(error,part.node.basis[axis].distance_to(part.home.basis[axis]))
	for control in module.controls:
		error=maxf(error,control.node.position.distance_to(control.samples[0].origin))
	check(id+"_exact_reassembly",error<.00001,error)
func run()->void:
	set_meta("collection_skip_intro",true)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="):output=arg.trim_prefix("--capture=")
		if arg.begins_with("--models="):model_filter=arg.trim_prefix("--models=").split(",")
	if output.is_empty():quit(2);return
	DirAccess.make_dir_recursive_absolute(output)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene
	host=scene.get_node("Render/HeliosDesktop")
	await pause(2.5);service=host.collection
	check("collection_loaded",service!=null)
	if service==null:quit(2);return
	host.rotation_enabled=false;host.angle=0
	await process_frame
	initial_window=Rect2i(root.position,root.size);initial_camera=host.camera.global_transform;initial_fov=host.camera.fov;initial_base=host.fixed_base.global_transform
	await capture("B_closed")
	service.toggle_selector();await until(func():return service.selector_amount>.999)
	await capture("B_selector")
	service.toggle_selector();await until(func():return service.selector_amount<.001)
	for id in ["F","G","I","J","K","L","M","N"]:
		if not model_filter.is_empty() and id not in model_filter:continue
		service.request_model(id)
		var loaded:=await until(func():return service.state=="idle" and service.active_id==id,60)
		check(id+"_switch",loaded,service.state)
		if not loaded:continue
		await pause(.35);await capture(id+"_closed")
		var model:Node3D=service.current
		host.activate(2 if id=="M" else 1)
		check(id+"_opened",await until(func():return model.openness>.999 and model.explosion<.001))
		await pause(.2);await capture(id+"_open")
		await process_frame;await process_frame
		host.activate(2)
		performance[id]=[];measuring=id
		await pause(2.0);measuring="";await capture(id+"_action")
		if id in ["M","N"]:await pause(3.5);await capture(id+"_action_late")
		host.activate(3)
		check(id+"_explode",await until(func():return model.explosion>.999 and model.openness<.001))
		await capture(id+"_exploded")
		host.activate(4)
		check(id+"_assemble",await until(func():return model.explosion<.001 and model.openness<.001))
		check_home(id,model)
		if id!="M":
			host.activate(1);await pause(.55);host.activate(4)
			check(id+"_interrupt_open",await until(func():return model.openness<.001 and model.explosion<.001))
		host.activate(3);await pause(.9);host.activate(4)
		check(id+"_interrupt_explode",await until(func():return model.explosion<.001 and model.openness<.001))
		check_home(id,model)
		service.toggle_selector();await until(func():return service.selector_amount>.999)
		await capture(id+"_selector")
		service.toggle_selector();await until(func():return service.selector_amount<.001)
	service.request_model("B")
	check("return_B",await until(func():return service.active_id=="B" and service.state=="idle"))
	await capture("B_returned")
	var timing:Dictionary={}
	for id in performance:
		var values:Array=performance[id];values.sort()
		if not values.is_empty():timing[id]={"frames":values.size(),"median_ms":values[values.size()/2],"p95_ms":values[int(values.size()*.95)],"max_ms":values[-1],"includes_first_action_compilation":true}
	var report:={"all_passed":checks.all(func(item):return item.passed),"checks":checks,"performance":timing,"engine":Engine.get_version_info().string,"device":RenderingServer.get_video_adapter_name(),"is_art_acceptance":false}
	FileAccess.open(output.path_join("runtime_report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("COLLECTION_QA_RESULT ",report.all_passed," output=",output)
	quit(0 if report.all_passed else 2)
