extends SceneTree
var host:Node3D
var service:Node3D
var checks:Array=[]
var out:="res://../review/I_refinement/nautilus_r1/main_adapter_r59/main_r4/"
var registry:="res://../review/I_refinement/nautilus_r1/main_adapter_r59/registry.json"
func _process(delta:float)->bool:
	# The renderer-worker window lives offscreen; still render real viewports.
	RenderingServer.force_draw(false,delta)
	return false
func _initialize()->void:run.call_deferred()
func check(label:String,value:bool)->void:
	checks.append({"check":label,"passed":value});print("I_MAIN_QA ",label," ",value)
	FileAccess.open(out+"progress.json",FileAccess.WRITE).store_string(JSON.stringify({"checks":checks,"service":service.diagnostics()},"  "))
func until(predicate:Callable,seconds:float=45.)->bool:
	var started:=Time.get_ticks_msec()
	while not predicate.call():
		if Time.get_ticks_msec()-started>seconds*1000.:return false
		await process_frame
	return true
func capture(name:String)->void:
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(out+name+".png")
	FileAccess.open(out+name+".json",FileAccess.WRITE).store_string(JSON.stringify(service.diagnostics(),"  "))
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):out=arg.trim_prefix("--out=").trim_suffix("/")+"/"
		if arg.begins_with("--registry="):registry=arg.trim_prefix("--registry=")
	RenderingServer.set_render_loop_enabled(false)
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	set_meta("collection_registry",registry)
	DirAccess.make_dir_recursive_absolute(out)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene;host=scene.get_node("Render/HeliosDesktop")
	await create_timer(2.).timeout;service=host.collection;host.rotation_enabled=false;host.angle=0.
	var base_transform:Transform3D=host.fixed_base.global_transform
	var camera_transform:Transform3D=host.camera.global_transform
	var light_before:Dictionary=service.lighting.current.duplicate(true)
	await capture("01_B_before")
	service.request_model("I")
	check("reveal_started",await until(func():return service.state=="revealing",90.))
	await create_timer(.7).timeout;await capture("02_I_revealing")
	check("current_I_arrived",await until(func():return service.state=="idle" and service.active_id=="I"))
	if service.active_id!="I":quit(2);return
	await capture("03_I_closed")
	check("current_rig_not_old_I",service.current.data.get("runtime","")=="nautilus_r59")
	check("reviewed_materials_restored",not service.current.archive.active)
	check("optical_attachments_survive_transfer",is_instance_valid(service.current.assembly.echo.light) and is_instance_valid(service.current.assembly.music.staff.optics) and service.current.assembly.music.staff.scanner_caps.all(func(c):return is_instance_valid(c)))
	check("music_control_profile",service.control_driver.profile(1).key=="music")
	host.activate(1)
	check("music_starts_after_unfolding",await until(func():return service.current.assembly.music.transport.state=="playing"))
	await create_timer(8.).timeout;await capture("04_I_music")
	service.current.play.input("bellows",1.,"begin");await create_timer(.2).timeout;service.current.play.input("bellows",0.,"cancel")
	check("cancel_pressure",not service.current.charge_pending and not service.current.assembly.rig.user_pressed)
	service.current.stow();await create_timer(.8).timeout;service.current.set_open(true)
	check("reverse_close",await until(func():return service.current.assembly.sequence.shell_open>.999))
	host.activate(1);check("music_restarts",await until(func():return service.current.assembly.music.transport.state=="playing"))
	service.request_model("B")
	check("music_stows_before_archive",await until(func():return service.state=="archiving"))
	check("outgoing_audio_stopped",service.current.assembly.music.transport.state=="stopped" and service.current.settled())
	await create_timer(.65).timeout;await capture("05_I_archiving")
	check("returned_B",await until(func():return service.active_id=="B" and service.state=="idle"))
	await capture("06_B_returned")
	check("same_base_and_camera",service.diagnostics().base_instances==1 and host.fixed_base.global_transform==base_transform and host.camera.global_transform==camera_transform)
	check("B_light_restored",service.lighting.current==light_before)
	# Cancel the real asynchronous preparation; the existing B must remain.
	service.request_model("I");check("warming_for_cancel",await until(func():return service.state=="warming",90.))
	var cancel:=InputEventKey.new();cancel.keycode=KEY_ESCAPE;cancel.pressed=true;service.consume_input(cancel)
	await create_timer(2.).timeout
	check("cancel_preserves_B",service.active_id=="B" and service.state=="idle" and service.prepared==null and service.warm_view==null)
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Actual main scene/service, existing selector transition, real renderer, synthetic dispatch and explicit cancellation; Dummy audio. No native pointer or final visual acceptance."}
	FileAccess.open(out+"report.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("I_MAIN_QA_RESULT ",report.passed)
	# This test exits directly rather than exercising the host shutdown UI.
	for audio in host.find_children("*","AudioStreamPlayer",true,false):audio.stop()
	for audio in host.find_children("*","AudioStreamPlayer3D",true,false):audio.stop()
	await create_timer(.3).timeout;quit(0 if report.passed else 2)
