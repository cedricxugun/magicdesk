extends SceneTree
var OUT:="res://../review/G_optical_curator/butterfly_r2/runtime/"
var host:Node3D
var module:Node3D
var service:Node3D
var player:RefCounted
var cue:Node3D
var checks:Array=[]
var bake_only:=false
var maximum_error:=0.0
var minimum_cup_up:=1.0
var seen:Dictionary={}
var capture_frames:Dictionary={}
func _initialize()->void:run.call_deferred()
func step(count:int)->void:
	for i in range(count):
		service.tick(1./30.)
		if bake_only:await process_frame
		else:await RenderingServer.frame_post_draw
		if player and player.butterfly_drive:
			for rig in player.butterfly_drive.rigs:
				var r:Dictionary=rig.source;var a:Vector3=rig.crank.to_global(Vector3(r.side*.025,0,0));var b:Vector3=rig.wing.to_global(Vector3(r.side*.022,r.link_height,0))
				maximum_error=maxf(maximum_error,maxf(a.distance_to(rig.rod.global_position),b.distance_to(rig.rod.to_global(Vector3(0,.060,0)))))
				minimum_cup_up=minf(minimum_cup_up,(rig.rod.global_basis*Vector3.FORWARD).normalized().dot(Vector3.UP))
			seen[player.stage]=true

func input(slot:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=slot;driver.active=driver.profile(slot);driver._set_value(value,event)
	if slot!=5 or event=="release":driver.index=-1;driver.active={}
func capture(label:String)->void:
	if bake_only:return
	if not OS.get_cmdline_user_args().has("--movie"):await RenderingServer.frame_post_draw
	capture_frames[label]=Engine.get_frames_drawn()
	var image:Image=host.render_view.get_texture().get_image();image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(OUT+label+".png")
func run()->void:
	bake_only=OS.get_cmdline_user_args().has("--bake-only")
	if bake_only:Engine.max_fps=0;set_meta("collection_no_audio",true)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):OUT=arg.trim_prefix("--output=")+"/"
	var baseline:=OS.get_cmdline_user_args().has("--baseline")
	if baseline:set_meta("observatory_material_baseline",true)
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	var stem:="G_optical_curator" if OS.get_cmdline_user_args().has("--main") else "G_optical_curator_butterfly_candidate"
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/"+stem+".json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/"+stem+".glb"));player=module.play.g_instrument;cue=module.effect.g_visuals.observatory_performance;service.current=module;service.active_id="G";service._build_controls()
	if not player.butterfly_drive:scene.queue_free();await process_frame;quit(2);return
	var target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.52
	host.camera.global_position=target+Vector3(.16,.40,2.0);host.camera.look_at(target);host.camera.fov=43
	input(1,1.,"begin")
	var captured:Dictionary={}
	for i in range(650):
		await step(1)
		if player.stage=="printing":
			for level in [.20,.55,.70,.85]:
				if player.print_amount>=level and not captured.has(level):
					await capture("build_"+str(roundi(level*100)));captured[level]=true
		if player.stage=="playing" and player.butterfly_drive.aperture>.79:break
	checks.append({"name":"opens_after_formation","passed":player.stage=="playing" and player.butterfly_drive.aperture>.79})
	input(3,0.,"change");await step(12);await capture("open")
	input(5,1.,"begin");await step(36);await capture("wingbeat")
	checks.append({"name":"hold_charges_butterfly","passed":player.action_energy>.99})
	input(5,0.,"release");await step(48)
	checks.append({"name":"release_settles","passed":player.action_energy<.001})
	module.stow()
	var folded_before_erase:=false
	for i in range(600):
		await step(1)
		if player.stage=="erasing" and not captured.has("erase"):
			if player.print_amount<.65:
				folded_before_erase=player.butterfly_drive.aperture<.001;await capture("return");captured["erase"]=true
		if module.settled():break
	checks.append({"name":"folds_before_erasing","passed":seen.has("folding_butterfly") and folded_before_erase})
	checks.append({"name":"original_disc_back_in_slot","passed":module.settled() and player.owners.all(func(o):return o=="slot")})
	checks.append({"name":"both_rod_endpoints_connected","passed":maximum_error<.00001,"max_error":maximum_error})
	checks.append({"name":"cup_roll_stays_vertical","passed":minimum_cup_up>.9999,"minimum_dot":minimum_cup_up})
	checks.append({"name":"fabrication_strokes_clear_after_stow","passed":module.effect.g_visuals.butterfly_fabrication.strokes.all(func(s):return not s.node.visible)})
	input(1,1.,"begin")
	for i in range(550):
		await step(1)
		if player.stage=="printing" and player.print_amount>.45:break
	checks.append({"name":"partial_print_wings_stay_folded","passed":player.stage=="printing" and player.butterfly_drive.aperture<.001})
	module.stow()
	for i in range(600):
		await step(1)
		if module.settled():break
	checks.append({"name":"partial_print_cancel_returns_original_disc","passed":module.settled() and player.owners.all(func(o):return o=="slot")})
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"resource_stem":stem,"stages":seen.keys(),"scope":"Headless scene/control-driver replay; no native input or rendered visual acceptance" if bake_only else "Isolated candidate in actual scene/control-driver replay; close-up camera, not native App or full visual acceptance"}
	FileAccess.open(OUT+"capture_frames.json",FileAccess.WRITE).store_string(JSON.stringify(capture_frames,"  "))
	FileAccess.open(OUT+"candidate_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("BUTTERFLY_CANDIDATE_QA ",JSON.stringify(report))
	player=null;cue=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 2)
