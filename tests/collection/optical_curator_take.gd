extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var player:RefCounted
var data:Dictionary
var samples:Array=[]
var extras:Array=[]
var frame:=0
var bake_only:=false
var model_hash:=""
var metadata_hash:=""
var wait_errors:=0
var operating_review:=false
var recording:=false
var model_stem:="res://assets/collection/models/G_optical_curator"
var OUT:="res://../review/G_optical_curator/"
const DT:=1.0/30.0
func _initialize()->void:run.call_deferred()
func pack(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale();return {"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
func capture(name:String)->void:
	if bake_only:return
	await RenderingServer.frame_post_draw
	var image:Image=host.render_view.get_texture().get_image();image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(ProjectSettings.globalize_path(OUT+name+".png"))
	if operating_review and not recording and name in ["03_actual_read","04a_structure_weave","04_actual_print","04b_seal_peak","play_1","05a_recovery_upper","05b_recovery_lower"]:
		var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
		var target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.55
		host.camera.global_position=target+Vector3(.25,.50,2.1);host.camera.look_at(target);host.camera.fov=45
		module.effect.g_visuals.tick(0,0)
		await RenderingServer.frame_post_draw
		host.render_view.get_texture().get_image().save_png(OUT+name+"_detail.png")
		host.camera.global_transform=home;host.camera.fov=fov
		module.effect.g_visuals.tick(0,0)
func step()->void:
	host.power=move_toward(host.power,host.power_target,DT*1.5);service.tick(DT);frame+=1
	var poses:Dictionary={}
	for p in module.parts:poses[str(p.node.name)]=pack(p.node.transform)
	for name in extras:poses[name]=pack(module.named(name).transform)
	var widgets:Array=[]
	for c in service.custom_controls:widgets.append({"name":str(c.node.name),"gesture":service.control_driver.profile(c.index).gesture,"pose":pack(c.node.global_transform),"moving_names":c.moving.map(func(m):return str(m.node.name)),"moving":c.moving.map(func(m):return pack(m.node.transform))})
	var sample:={"frame":frame,"poses":poses,"widgets":widgets,"state":player.diagnostics(),"power":host.power,"open":module.openness,"explosion":module.explosion}
	if player.ship_drive:
		sample.ship_ropes={};sample.ship_springs={}
		for sheet in player.ship_drive.sheets:
			sample.ship_ropes[sheet.source.node]={"pose":pack(sheet.draw.transform),"points":Array(sheet.points).map(func(p):return [p.x,p.y,p.z])}
		for spring in player.ship_drive.springs:
			sample.ship_springs[spring.source.node]={"pose":pack(spring.draw.transform),"points":Array(spring.points).map(func(p):return [p.x,p.y,p.z])}
	if service.record_console:sample.console_lamps=service.record_console.levels.duplicate()
	if frame%3==0:sample.fx=module.effect.g_visuals.state()
	samples.append(sample)
	if bake_only:await process_frame
	else:await RenderingServer.frame_post_draw
func seconds(duration:float)->void:
	for i in range(ceili(duration/DT)):await step()
func until(fn:Callable,limit:float=20.0)->bool:
	for i in range(ceili(limit/DT)):
		await step()
		if fn.call():return true
	wait_errors+=1;push_error("Record take timed out: "+player.stage);return false
func input(slot:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=slot;driver.active=driver.profile(slot);driver._set_value(value,event)
	if slot!=5 or event=="release":driver.index=-1;driver.active={}
func run()->void:
	bake_only=OS.get_cmdline_user_args().has("--bake-only");set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	operating_review=OS.get_cmdline_user_args().has("--operating-review")
	recording=OS.get_cmdline_args().has("--write-movie")
	if operating_review:OUT="res://../review/G_optical_curator/operating/"
	if OS.get_cmdline_user_args().has("--observatory-candidate"):
		model_stem+="_observatory_candidate";OUT="res://../review/G_optical_curator/observatory_r2/app/";operating_review=true
	if OS.get_cmdline_user_args().has("--butterfly-candidate"):
		model_stem="res://assets/collection/models/G_optical_curator_butterfly_candidate";OUT="res://../review/G_optical_curator/butterfly_r2/full_take/"
	if OS.get_cmdline_user_args().has("--ship-candidate"):
		model_stem="res://assets/collection/models/G_optical_curator_ship_candidate";OUT="res://../review/G_optical_curator/ship_r3/full_take/" if OS.get_cmdline_user_args().has("--r3") else "res://../review/G_optical_curator/ship_r2/full_take/"
	set_meta("collection_no_audio",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(8):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1;host.power_target=1;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	if bake_only:Engine.max_fps=0;root.position=Vector2i(-32000,-32000);root.unfocusable=true
	service._legacy_set_visible(false);service._set_base_frame("shared")
	data=JSON.parse_string(FileAccess.get_file_as_string(model_stem+".json"))
	model_hash=FileAccess.get_sha256(model_stem+".glb")
	metadata_hash=FileAccess.get_sha256(model_stem+".json")
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load(model_stem+".glb"));player=module.play.g_instrument;service.current=module;service.active_id="G";service._build_controls();host.tooltip.hide();host.toast.hide()
	var spec:Dictionary=data.record_player;extras=[spec.magazine,spec.upper_arm,spec.forearm,spec.wrist,spec.platter,spec.tonearm]
	extras.append_array(spec.cradles);extras.append_array(spec.records)
	var ai:Dictionary=data.optical_curator;extras.append_array([ai.face,ai.carrier,ai.projector,ai.iris,ai.shoulder_fork,ai.wrist_yoke]);extras.append_array(ai.eyes)
	for leaf in ai.leaves:extras.append(leaf.name)
	if ai.has("head_service"):
		extras.append_array([ai.head_service.cam,ai.head_service.pinion])
		for item in ai.head_service.followers:extras.append(item.link)
	for f in spec.fingers:extras.append_array([f.proximal,f.distal,f.pad])
	for c in data.g_archive.contents:
		extras.append(c.root)
		for r in c.rig:extras.append(r.name)
	module.effect.g_visuals.force_warm=true;module.effect.tick(0)
	for i in range(8):await process_frame
	module.effect.g_visuals.force_warm=false;module.apply_pose();module.effect.tick(0)
	await seconds(.4);await capture("00_six_records_rest")
	var visited:Array=[]
	for id in ([0] if OS.get_cmdline_user_args().has("--quick") else [0,1,2,3,4,5]):
		input(1,float(id),"begin")
		if id==0:
			await until(func():return player.stage=="lifting_record");await seconds(.22);await capture("01_actual_pick")
			await until(func():return player.stage=="placing_record");await seconds(.18);await capture("02_actual_place")
			if operating_review:
				await until(func():return player.stage=="releasing_field" and player.grip<.65);await capture("02b_field_retract")
			await until(func():return player.stage=="reading");await seconds(.50);await capture("03_actual_read")
			await until(func():return player.stage=="printing" and player.print_amount>=.25);await capture("04a_structure_weave")
			await until(func():return player.print_amount>=.55);await capture("04_actual_print")
			await until(func():return player.print_amount>=.77);await capture("04b_seal_peak")
		var ok:=await until(func():return player.stage=="playing" and player.loaded_index==id)
		visited.append({"id":id,"played":ok});await capture("play_"+str(id+1))
		await seconds(.7);input(2,.72,"begin");input(5,1,"begin");await seconds(1.2);await capture("action_"+str(id+1));input(5,0,"release");await seconds(.8)
	input(3,1,"change");await seconds(2.0);input(3,0,"change");await seconds(.8)
	module.stow();await until(func():return player.stage=="erasing",3);await seconds(.42);await capture("05a_recovery_upper")
	await seconds(.48);await capture("05b_recovery_lower")
	await until(func():return module.settled(),16);await capture("05_all_returned")
	module.activate(3);await until(func():return module.explosion>.999,6);await capture("06_exploded")
	module.stow();await until(func():return module.explosion<.001,5);await capture("07_reassembled")
	input(1,2,"begin");await until(func():return player.stage=="lifting_record",5);module.stow();await until(func():return module.settled(),12);await capture("08_interrupted_return")
	FileAccess.open(OUT+"curator_take.json",FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"model_sha256":model_hash,"metadata_sha256":metadata_hash,"samples":samples,"heights":module.effect.g_visuals.heights}))
	FileAccess.open(OUT+"take_report.json",FileAccess.WRITE).store_string(JSON.stringify({"frames":frame,"all_played":visited.all(func(x):return x.played),"visited":visited,"settled":module.settled(),"owners":player.owners,"wait_errors":wait_errors,"model_sha256":model_hash,"metadata_sha256":metadata_hash},"  "))
	print("CURATOR_TAKE_COMPLETE ",frame," frames")
	var exit_code:=0 if wait_errors==0 and visited.all(func(x):return x.played) and module.settled() else 2
	player=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(exit_code)
