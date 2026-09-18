extends SceneTree
var host:Node3D
var service:Node3D
var control:Node3D
var checks:Array=[]
var headless:=false
var OUT:="res://../review/shared_rotation/"
func _initialize()->void:run.call_deferred()
func step(n:int)->void:
	for i in range(n):
		service.tick(1./30.)
		if headless:await process_frame
		else:await RenderingServer.frame_post_draw
func check(label:String,passed:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":passed,"detail":detail})
func capture(label:String)->void:
	if headless:return
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(OUT+label+".png")
	if OS.get_cmdline_user_args().has("--backdrops") and label in ["00_dormant","01_reveal","04_paused"]:
		var bg:=ColorRect.new();bg.size=Vector2(root.size);bg.mouse_filter=Control.MOUSE_FILTER_IGNORE;bg.z_index=-100;root.add_child(bg)
		for pair in [["white",Color.WHITE],["dark",Color(.025,.028,.032)]]:
			bg.color=pair[1]
			for i in range(3):await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(OUT+label+"_"+pair[0]+".png")
		bg.queue_free();await process_frame
func mouse(pressed:bool,point:Vector2)->bool:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;event.position=point
	return service.consume_input(event)
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):OUT=arg.trim_prefix("--out=")
	headless=OS.get_cmdline_user_args().has("--bake-only");Engine.max_fps=0 if headless else 60
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
	service=host.collection;control=service.rotation_hologram;control.review_pointer=Vector2(-10000,-10000)
	var base_box:AABB=service.base_display.mesh.get_aabb()
	await step(90);check("recedes_to_hidden_slit",absf(control.amount-control.IDLE_AMOUNT)<.001,control.amount);await capture("00_dormant")
	var point:Vector2=control.screen_center();control.review_pointer=point;await step(15)
	check("approach_reveals_button",control.amount>.99);await capture("01_reveal")
	var initial:bool=host.rotation_enabled
	check("captures_pointer_press",mouse(true,point));await step(3);await capture("02_compress")
	check("release_toggles_once",mouse(false,point) and host.rotation_enabled!=initial);await step(5);await capture("03_echo")
	await step(30);await capture("04_paused")
	mouse(true,point);mouse(false,point);await step(25);check("resume_restores_rotation",host.rotation_enabled==initial);await capture("05_running")
	var layouts:Array=[]
	for zoom in [.7,1.0,1.1]:
		host.zoom=zoom;host.DesktopScale.apply(host)
		var points:Array[Vector2]=[];service._screen_points(host.buttons[6].mount,points)
		var bounds:=Rect2(points[0],Vector2.ZERO)
		for p in points:bounds=bounds.expand(p)
		var hit:Rect2i=control.input_region();var separation:bool=not Rect2(hit).intersects(bounds.grow(6.*DisplayServer.screen_get_scale()))
		layouts.append({"zoom":zoom,"holo":str(hit),"close":str(bounds),"separate":separation})
		check("clear_of_shutdown_at_%d"%roundi(zoom*100),separation)
		check("inside_canvas_at_%d"%roundi(zoom*100),Rect2(Vector2.ZERO,Vector2(host.canonical_size)).encloses(Rect2(hit)))
	host.zoom=1.0;host.DesktopScale.apply(host)
	service.selector_amount=1.;service.selector_target=1.;control.tick(.1)
	check("hidden_during_model_selection",not control.contains(control.screen_center()) and not control.held)
	service.selector_amount=0.;service.selector_target=0.
	service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator_ship_candidate.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator_ship_candidate.glb"));service.current=module;service.active_id="G";service._build_controls()
	await step(8);var spindle:bool=module.play.g_instrument.spin_enabled
	point=control.screen_center();control.review_pointer=point;var display:bool=host.rotation_enabled
	mouse(true,point);mouse(false,point);await step(20)
	check("G_rotates_display_independently",host.rotation_enabled!=display and module.play.g_instrument.spin_enabled==spindle)
	check("one_shared_control",control==service.rotation_hologram)
	await capture("06_G_shared_control")
	if not headless:
		var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
		var target:=Vector3(1.57,.18,.27)
		host.camera.global_position=target+Vector3(.35,.24,1.6);host.camera.look_at(target);host.camera.fov=34
		control.review_pointer=control.screen_center();await step(20);await capture("07_port_detail")
		host.camera.global_transform=home;host.camera.fov=fov
	check("base_dimensions_preserved",is_equal_approx(base_box.size.x,service.base_display.mesh.get_aabb().size.x) and is_equal_approx(base_box.size.y,service.base_display.mesh.get_aabb().size.y))
	var result:={"passed":checks.all(func(c):return c.passed),"checks":checks,"layouts":layouts,"scope":"Shared renderer/input harness. Native pointer pass-through and visual acceptance are separate."}
	FileAccess.open(OUT+("headless_qa.json" if headless else "gpu_qa.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("SHARED_ROTATION_QA ",JSON.stringify(result))
	control=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
