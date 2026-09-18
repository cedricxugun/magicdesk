extends SceneTree
var host:Node3D
var service:Node3D
var control:Node3D
var checks:Array=[]
var out:="res://../review/shared_rotation/contrast_r3/main_r2/"
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func check(label:String,passed:bool)->void:
	checks.append({"name":label,"passed":passed});print("ROTATION_MAIN ",label," ",passed)
	FileAccess.open(out+"progress.json",FileAccess.WRITE).store_string(JSON.stringify({"checks":checks,"service":service.diagnostics()},"  "))
func until(predicate:Callable,timeout:float=120.)->bool:
	var start:=Time.get_ticks_msec()
	while not predicate.call():
		if Time.get_ticks_msec()-start>timeout*1000.:return false
		await process_frame
	return true
func click(point:Vector2)->void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event.position=point
	assert(service.consume_input(event));await process_frame
	event=event.duplicate();event.pressed=false;assert(service.consume_input(event));await process_frame
func capture(label:String)->void:
	await RenderingServer.frame_post_draw;host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out)
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene;host=scene.get_node("Render/HeliosDesktop")
	await create_timer(2.).timeout;host.muted=true;service=host.collection;control=service.rotation_hologram
	control.review_pointer=Vector2(-10000,-10000);await create_timer(3.).timeout
	check("B_idle_glyph_complete",control.state().face_reveal==1. and control.state().face_gain>=.67)
	var initial:bool=host.rotation_enabled;await click(control.screen_center());check("B_release_toggles",host.rotation_enabled!=initial)
	var point:Vector2=control.screen_center();var down:=InputEventMouseButton.new();down.button_index=MOUSE_BUTTON_LEFT;down.position=point;down.pressed=true
	service.consume_input(down);root.focus_exited.emit();var before:bool=host.rotation_enabled;down=down.duplicate();down.pressed=false;service.consume_input(down)
	check("focus_cancel_does_not_toggle",not control.held and host.rotation_enabled==before)
	var saved_mac:bool=host.mac_desktop;var saved_focal:float=host.reference_focal_pixels;var saved_unit:float=host.desktop_unit_focal;var saved_fov:float=host.camera.fov
	host.mac_desktop=true;host.zoom=1.;host.DesktopScale.apply(host,true)
	var fovs:Array=[]
	for zoom in [.7,1.,1.1]:
		host.zoom=zoom;host.DesktopScale.apply(host);control.tick(.01)
		fovs.append(host.camera.fov)
		var points:Array[Vector2]=[];service._screen_points(host.buttons[6].mount,points);var rect:=Rect2(points[0],Vector2.ZERO)
		for p in points:rect=rect.expand(p)
		check("separate_shutdown_"+str(zoom),not Rect2(control.input_region()).intersects(rect.grow(6.*DisplayServer.screen_get_scale())))
		check("inside_canvas_"+str(zoom),Rect2(Vector2.ZERO,Vector2(host.canonical_size)).encloses(Rect2(control.input_region())))
	check("three_actual_projection_scales",fovs[0]>fovs[1] and fovs[1]>fovs[2])
	host.mac_desktop=saved_mac;host.zoom=1.;host.reference_focal_pixels=saved_focal;host.desktop_unit_focal=saved_unit;host.camera.fov=saved_fov
	service.request_model("I");check("I_loaded",await until(func():return service.active_id=="I" and service.state=="idle"))
	if service.active_id!="I":quit(2);return
	host.activate(1);check("I_music_started",await until(func():return service.current.assembly.music.transport.state=="playing"))
	var music:Node=service.current.assembly.music;var previous:float=music.transport.position_seconds()
	before=host.rotation_enabled;await click(control.screen_center());await create_timer(.5).timeout
	check("I_display_rotation_keeps_music",host.rotation_enabled!=before and music.transport.state=="playing" and music.transport.position_seconds()>previous)
	await capture("I_shared_control")
	service.toggle_selector();check("selector_unavailable",not control.available() and not control.held)
	check("selector_opened_after_stow",await until(func():return service.selector_amount>.999))
	check("no_holo_hit_over_selector",not control.contains(control.screen_center()))
	service.toggle_selector();await until(func():return service.selector_amount<.001)
	service.request_model("G");check("G_loaded",await until(func():return service.active_id=="G" and service.state=="idle"))
	if service.active_id!="G":quit(2);return
	var spindle:bool=service.current.play.g_instrument.spin_enabled
	before=host.rotation_enabled;await click(control.screen_center())
	check("G_display_does_not_toggle_spindle",host.rotation_enabled!=before and service.current.play.g_instrument.spin_enabled==spindle)
	host.rotation_enabled=true;service.dispatch(3)
	check("G_spindle_does_not_stop_display",host.rotation_enabled and service.current.play.g_instrument.spin_enabled!=spindle)
	service.current.play.input("spin",1. if spindle else 0.,"change")
	check("G_physical_spin_keeps_display",host.rotation_enabled and service.current.play.g_instrument.spin_enabled==spindle)
	await capture("G_shared_control")
	service.request_model("B");check("B_return",await until(func():return service.active_id=="B" and service.state=="idle"))
	check("single_control_and_base",control==service.rotation_hologram and service.diagnostics().base_instances==1)
	FileAccess.open(out+"report.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Actual main B/I/G, shared control routing, menu and dedicated spin intents, three scales and focus cancellation. Synthetic events, Dummy audio; no OS click or art acceptance."},"  "))
	for a in host.find_children("*","AudioStreamPlayer",true,false):a.stop()
	for a in host.find_children("*","AudioStreamPlayer3D",true,false):a.stop()
	await create_timer(.3).timeout;quit(0 if checks.all(func(c):return c.passed) else 2)
