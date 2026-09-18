extends SceneTree
var OUT:="res://../review/G_optical_curator/observatory_interaction/"
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
	input(3,0.,"change");await step(15)
	var target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.58
	if not desktop:
		host.camera.global_position=target+Vector3(.22,.45,2.1);host.camera.look_at(target);host.camera.fov=43
	await step(3);await capture("01_idle")
	var previous:float=player.observatory_parameter
	input(2,.85,"begin")
	checks.append({"name":"parameter_event_does_not_jump_pose","passed":is_equal_approx(player.observatory_parameter,previous)})
	await step(1);checks.append({"name":"parameter_first_step_bounded","passed":absf(player.observatory_parameter-previous)<.04})
	await step(4);await capture("02_set_time")
	var lit:Image=host.render_view.get_texture().get_image()
	cue.trace.hide();await RenderingServer.frame_post_draw
	var unlit:Image=host.render_view.get_texture().get_image();cue.trace.show()
	var box:=Rect2(host.camera.unproject_position(cue.trace.to_global(Vector3(-.18,-.18,0))),Vector2.ZERO)
	for point in [Vector3(-.18,.18,0),Vector3(.18,-.18,0),Vector3(.18,.18,0)]:box=box.expand(host.camera.unproject_position(cue.trace.to_global(point)))
	var region:=Rect2i(box).intersection(Rect2i(Vector2i.ZERO,lit.get_size()));var visible_pixels:=0
	for y in range(region.position.y,region.end.y):
		for x in range(region.position.x,region.end.x):
			var a:Color=lit.get_pixel(x,y);var b:Color=unlit.get_pixel(x,y)
			if a.r-b.r>.12 and a.g-b.g>.05 and a.r>a.b*1.15:visible_pixels+=1
	checks.append({"name":"scale_trace_changes_visible_pixels","passed":visible_pixels>=10,"pixels":visible_pixels})
	if OS.get_cmdline_user_args().has("--trace-debug"):
		print("TRACE_DEBUG ",{"visible_tree":cue.trace.is_visible_in_tree(),"transform":str(cue.trace.global_transform),"size":str(cue.trace.mesh.size),"gain":cue.gain,"center":str(cue.trace.material_override.get_shader_parameter("mask_center")),"texture_size":str(cue.trace.material_override.get_shader_parameter("pattern").get_size())})
		var material:Material=cue.trace.material_override
		var debug:=StandardMaterial3D.new();debug.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;debug.albedo_color=Color(1,0,0,.7);debug.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;debug.cull_mode=BaseMaterial3D.CULL_DISABLED;cue.trace.material_override=debug
		await capture("debug_quad")
		cue.trace.material_override=material;cue.trace.position.z+=.15;await capture("debug_forward_trace");cue.trace.position.z-=.15
		for mesh in module.meshes:mesh.hide()
		host.fixed_base.hide();service.custom_panel.hide();cue.trace.material_override.set_shader_parameter("gain",3.0);await capture("debug_trace_only")
		for mesh in module.meshes:mesh.show()
		host.fixed_base.show();service.custom_panel.show();cue.trace.material_override.set_shader_parameter("gain",cue.gain)
		for depth in [.008,.020,.040]:
			cue.trace.position.z=depth;cue.trace.material_override.set_shader_parameter("gain",3.0);await capture("debug_depth_"+str(roundi(depth*1000)))
		cue.trace.position.z=.008;cue.trace.material_override.set_shader_parameter("gain",cue.gain)
	checks.append({"name":"adjustment_lights_real_scale","passed":cue.trace.visible and cue.gain>.1})
	await step(30);checks.append({"name":"parameter_reaches_requested_value","passed":absf(player.observatory_parameter-.85)<.001})
	input(5,1.,"begin");await step(6);await capture("03_charge")
	checks.append({"name":"hold_has_charge_before_peak","passed":player.action_energy>.1 and player.action_energy<.4})
	await step(27);await capture("04_resonate")
	checks.append({"name":"hold_reaches_peak","passed":player.action_energy>.99 and cue.lamp.light_energy>.02})
	input(5,0.,"release");await step(8);await capture("05_release")
	checks.append({"name":"release_coasts_instead_of_snapping","passed":player.action_energy>.5 and player.action_energy<.99})
	await step(45);await capture("06_quiet")
	checks.append({"name":"release_cleans_interaction_effects","passed":player.action_energy<.001 and not cue.trace.visible and is_zero_approx(cue.lamp.light_energy)})
	input(5,1.,"begin");await step(12);module.stow();await step(1)
	checks.append({"name":"stow_immediately_clears_interaction_overlay","passed":not cue.trace.visible and is_zero_approx(cue.lamp.light_energy)})
	for i in range(480):
		await step(1)
		if module.settled():break
	checks.append({"name":"stow_returns_original_record","passed":module.settled() and player.owners.all(func(o):return o=="slot")})
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Actual scene/control-driver replay; normal camera" if desktop else "Actual scene and control-driver replay; close-up camera for review, not native mouse acceptance"}
	FileAccess.open(OUT+"interaction_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("OBSERVATORY_INTERACTION ",JSON.stringify(report));player=null;cue=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 2)
