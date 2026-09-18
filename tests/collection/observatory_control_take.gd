extends SceneTree
var OUT:="res://../review/G_optical_curator/observatory_controls/"
var host:Node3D
var module:Node3D
var service:Node3D
var player:RefCounted
var cue:Node3D
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func step(count:int)->void:
	for i in range(count):service.tick(1./30.);await RenderingServer.frame_post_draw
func input(slot:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=slot;driver.active=driver.profile(slot);driver._set_value(value,event)
	if slot!=5 or event=="release":driver.index=-1;driver.active={}
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	var image:Image=host.render_view.get_texture().get_image();image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(OUT+label+".png")
func run()->void:
	var desktop:=OS.get_cmdline_user_args().has("--desktop")
	if desktop:OUT+="desktop/"
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator.glb"));player=module.play.g_instrument;cue=module.effect.g_visuals.observatory_performance;service.current=module;service.active_id="G";service._build_controls()
	input(1,0.,"begin")
	for i in range(600):
		await step(1)
		if player.stage=="playing":break
	assert(player.stage=="playing")
	await step(2)
	var point:=Vector2.ZERO
	for c in service.custom_controls:
		if c.index==2:point=host.camera.unproject_position(c.node.to_global(Vector3(0,0,.08)))
	checks.append({"name":"time_control_center_hit","passed":service.hit_control(point)==2})
	var initial:float=player.parameters[0]
	var wheel:=InputEventMouseButton.new();wheel.position=point;wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true
	service.control_driver.consume(wheel);await step(3)
	checks.append({"name":"wheel_one_minute","passed":absf((player.parameters[0]-initial)*60.-1.)<.001})
	wheel.shift_pressed=true;service.control_driver.consume(wheel);await step(3)
	checks.append({"name":"shift_wheel_twelve_seconds","passed":absf((player.parameters[0]-initial)*60.-1.2)<.001})
	var down:=InputEventMouseButton.new();down.position=point;down.button_index=MOUSE_BUTTON_LEFT;down.pressed=true
	service.control_driver.consume(down)
	var move:=InputEventMouseMotion.new();move.position=point+Vector2(18,0);move.relative=Vector2(18,0);service.control_driver.consume(move)
	down.position=move.position;down.pressed=false;service.control_driver.consume(down);await step(12)
	checks.append({"name":"drag_eighteen_pixels_twelve_minutes","passed":absf((player.parameters[0]-initial)*60.-13.2)<.001})
	await capture("time_offset")
	var console:Dictionary=service.record_console.observatory.state()
	checks.append({"name":"physical_readout_matches_parameter","passed":console.visible and console.text=="+13.2分","readout":console})
	for c in service.custom_controls:
		if c.index==5:point=host.camera.unproject_position(c.node.to_global(Vector3(0,0,.075)))
	down.position=point;down.pressed=true;service.control_driver.consume(down);await step(30)
	checks.append({"name":"physical_hold_reaches_charge","passed":player.action_energy>.99})
	service.control_driver.cancel();await step(42)
	checks.append({"name":"capture_cancel_releases_charge","passed":player.action_energy<.001})
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Actual scene screen-ray and InputEvent gesture replay; independent of native OS input"}
	FileAccess.open(OUT+"gesture_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("OBSERVATORY_GESTURES ",JSON.stringify(report))
	player=null;cue=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 2)
