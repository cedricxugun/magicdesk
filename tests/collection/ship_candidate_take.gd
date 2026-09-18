extends SceneTree
var OUT:="res://../review/G_optical_curator/ship_r2/drive/"
var host:Node3D
var service:Node3D
var module:Node3D
var player:RefCounted
var drive:RefCounted
var checks:Array=[]
var headless:=false
var stages:Dictionary={}
var rope_error:=0.0
var cam_error:=0.0
var link_error:=0.0
var wave_extrema:Array=[[INF,-INF],[INF,-INF],[INF,-INF]]
var largest_phase_step:=0.0
var captured:Dictionary={}
var peak_edge_gain:=0.0
func _initialize()->void:run.call_deferred()
func step(count:int)->void:
	for i in range(count):
		var phase:float=drive.cam_phase
		service.tick(1./30.)
		if headless:await process_frame
		else:await RenderingServer.frame_post_draw
		stages[player.stage]=true
		if not headless and player.loaded_index==2 and player.stage=="printing":
			for mark in [.18,.42,.58,.78,.94]:
				var label:="formation_%02d"%roundi(mark*100)
				if player.print_amount>=mark and not captured.has(label):
					captured[label]=true;await capture(label)
		if player.loaded_index==2 and player.stage=="playing":largest_phase_step=maxf(largest_phase_step,absf(drive.cam_phase-phase))
		if not headless and player.loaded_index==2 and player.stage=="erasing":
			for mark in [.94,.78,.58,.42,.18]:
				var label:="recovery_%02d"%roundi(mark*100)
				if player.print_amount<=mark and not captured.has(label):
					captured[label]=true;await capture(label)
		if player.loaded_index==2 and player.stage in ["printing","erasing"]:
			for item in module.effect.g_visuals.ship_fabrication.surfaces:peak_edge_gain=maxf(peak_edge_gain,float(item.mat.get_shader_parameter("build_gain")))
		cam_error=maxf(cam_error,drive.contact_error)
		link_error=maxf(link_error,drive.link_error)
		if player.loaded_index==2 and player.stage=="playing":
			for j in range(3):
				wave_extrema[j][0]=minf(wave_extrema[j][0],drive.waves[j].position.y)
				wave_extrema[j][1]=maxf(wave_extrema[j][1],drive.waves[j].position.y)
		for sheet in drive.sheets:
			var s:Dictionary=sheet.source;var tip:=Vector3(s.side*(s.length+.020),.028,0)
			var end:=Vector3(s.winch_x+.008,.189+s.winch_lift,-s.winch_y)
			rope_error=maxf(rope_error,sheet.draw.to_global(sheet.points[0]).distance_to(sheet.sail.to_global(tip)))
			rope_error=maxf(rope_error,sheet.draw.to_global(sheet.points[33]).distance_to(drive.carrier.to_global(end)))
func input(slot:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=slot;driver.active=driver.profile(slot);driver._set_value(value,event)
	if slot!=5 or event=="release":driver.index=-1;driver.active={}
func check(name:String,passed:bool,detail:Variant=null)->void:checks.append({"name":name,"passed":passed,"detail":detail})
func capture(label:String)->void:
	if headless:return
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(OUT+label+".png")
func run()->void:
	if OS.get_cmdline_user_args().has("--r3"):OUT="res://../review/G_optical_curator/ship_r3/drive/"
	headless=OS.get_cmdline_user_args().has("--bake-only")
	if headless:Engine.max_fps=0
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.rotation_enabled=false;host.angle=0;host.power=1.;host.power_target=1.;host.muted=true;service=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared");host.toast.hide();host.tooltip.hide()
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator_ship_candidate.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator_ship_candidate.glb"));service.current=module;service.active_id="G";service._build_controls()
	player=module.play.g_instrument;drive=player.ship_drive
	var desktop_camera:Transform3D=host.camera.global_transform;var desktop_fov:float=host.camera.fov
	var early_target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.53
	host.camera.global_position=early_target+Vector3(.22,.45,2.1);host.camera.look_at(early_target);host.camera.fov=43
	input(1,2.,"begin")
	for i in range(720):
		await step(1)
		if player.stage=="playing":break
	check("reads_original_disc_before_showing",player.loaded_index==2 and player.stage=="playing" and player.owners[2]=="platter")
	input(3,0.,"change");await step(30);await capture("00_ready_close")
	host.camera.global_transform=desktop_camera;host.camera.fov=desktop_fov;await capture("01_desktop")
	var target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.53
	host.camera.global_position=target+Vector3(.22,.45,2.1);host.camera.look_at(target);host.camera.fov=43
	input(2,1.,"begin");await step(2)
	check("sail_trim_moves_with_speed_limit",drive.trim_angle<deg_to_rad(20.0))
	await step(35);check("trim_reaches_authored_limit",absf(drive.trim_angle-deg_to_rad(20.))<.0001);await capture("02_trimmed")
	input(5,1.,"begin");await step(45)
	check("hold_builds_tide_gradually",player.action_energy>.99);await capture("03_tide")
	if not headless and OS.get_cmdline_user_args().has("--motion-review"):await record_motion()
	input(5,0.,"release");await step(50)
	check("release_levels_hull",player.action_energy<.001 and drive.pitch.basis.is_equal_approx(Basis.IDENTITY) and drive.carrier.basis.is_equal_approx(Basis.IDENTITY));await capture("04_released")
	input(5,1.,"begin");await step(45);input(5,0.,"release");module.stow();await step(1)
	check("settles_before_erasing",player.stage=="settling_ship" and player.print_amount>.999)
	for i in range(100):
		await step(1)
		if player.stage=="erasing":break
	check("neutral_before_material_recovery",player.stage=="erasing" and drive.neutral());await capture("05_recovery")
	for i in range(600):
		await step(1)
		if module.settled():break
	check("original_disc_returns_to_own_slot",module.settled() and player.owners.all(func(o):return o=="slot"))
	input(1,2.,"begin")
	for i in range(720):
		await step(1)
		if player.stage=="printing" and player.print_amount>.35:break
	check("partial_build_stays_at_rest",player.stage=="printing" and absf(drive.trim_angle)<.001 and player.action_energy<.001)
	module.stow()
	for i in range(600):
		await step(1)
		if module.settled():break
	check("partial_cancel_returns_disc",module.settled() and player.owners.all(func(o):return o=="slot"))
	check("winch_ropes_stay_attached",rope_error<.00001,rope_error)
	check("cam_followers_stay_in_contact",cam_error<.00001,cam_error)
	check("fabrication_strokes_clear_after_return",module.effect.g_visuals.ship_fabrication.strokes.all(func(s):return not s.node.visible))
	check("ship_edge_gain_remains_bounded",peak_edge_gain<=.301,peak_edge_gain)
	check("cam_phase_does_not_jump_with_force",largest_phase_step<=(1.8 if drive.wave_drive_version==3 else 1.25)/30.+.00001,largest_phase_step)
	if drive.wave_drive_version==3:
		check("rocker_links_stay_attached",link_error<.00001,link_error)
		check("all_wave_carriages_use_full_travel",wave_extrema.all(func(r):return r[1]-r[0]>.031),wave_extrema)
	var result:={"passed":checks.all(func(c):return c.passed),"checks":checks,"stages":stages.keys(),"scope":"Headless mechanism/driver checks; no visual acceptance" if headless else "Actual GPU mechanism/driver/first fabrication checks; visual acceptance, complete source bake and native input still pending"}
	FileAccess.open(OUT+("headless_qa.json" if headless else "gpu_qa.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("SHIP_CANDIDATE_QA ",JSON.stringify(result))
	drive=null;player=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)

func record_motion()->void:
	var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
	var target:Vector3=module.named(module.data.record_player.print_root).global_position+Vector3.UP*.19
	host.camera.global_position=target+Vector3(.16,.22,1.35);host.camera.look_at(target);host.camera.fov=43
	DirAccess.make_dir_recursive_absolute(OUT+"motion")
	for i in range(120):
		await step(1)
		var frame_image:Image=host.render_view.get_texture().get_image()
		var center:Vector2=host.camera.unproject_position(target)
		var box:=Rect2i(Vector2i(center)-Vector2i(700,450),Vector2i(1400,900)).intersection(Rect2i(Vector2i.ZERO,frame_image.get_size()))
		var crop:=frame_image.get_region(box);crop.resize(1120,720,Image.INTERPOLATE_LANCZOS);crop.save_png(OUT+"motion/frame_%04d.png"%i)
	host.camera.global_transform=home;host.camera.fov=fov
