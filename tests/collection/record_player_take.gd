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
const OUT:="res://../review/G_record_player/"
const DT:=1.0/30.0
func _initialize()->void:run.call_deferred()
func pack(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale();return {"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
func capture(name:String)->void:
	if bake_only:return
	await RenderingServer.frame_post_draw
	var image:Image=host.render_view.get_texture().get_image();image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(ProjectSettings.globalize_path(OUT+name+".png"))
func step()->void:
	host.power=move_toward(host.power,host.power_target,DT*1.5);service.tick(DT);frame+=1
	var poses:Dictionary={}
	for p in module.parts:poses[str(p.node.name)]=pack(p.node.transform)
	for name in extras:poses[name]=pack(module.named(name).transform)
	var widgets:Array=[]
	for c in service.custom_controls:widgets.append({"gesture":service.control_driver.profile(c.index).gesture,"pose":pack(c.node.global_transform),"moving":c.moving.map(func(m):return pack(m.node.transform))})
	var sample:={"frame":frame,"poses":poses,"widgets":widgets,"state":player.diagnostics(),"power":host.power,"open":module.openness,"explosion":module.explosion}
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
	push_error("Record take timed out: "+player.stage);return false
func input(slot:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=slot;driver.active=driver.profile(slot);driver._set_value(value,event)
	if slot!=5 or event=="release":driver.index=-1;driver.active={}
func run()->void:
	bake_only=OS.get_cmdline_user_args().has("--bake-only");set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(8):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1;host.power_target=1;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	if bake_only:Engine.max_fps=0
	service._legacy_set_visible(false);service._set_base_frame("shared")
	data=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_record_player.json"))
	model_hash=FileAccess.get_sha256("res://assets/collection/models/G_record_player.glb")
	metadata_hash=FileAccess.get_sha256("res://assets/collection/models/G_record_player.json")
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_record_player.glb"));player=module.play.g_instrument;service.current=module;service.active_id="G";service._build_controls();host.tooltip.hide();host.toast.hide()
	var spec:Dictionary=data.record_player;extras=[spec.magazine,spec.upper_arm,spec.forearm,spec.wrist,spec.platter,spec.tonearm]
	extras.append_array(spec.cradles);extras.append_array(spec.records)
	for f in spec.fingers:extras.append_array([f.proximal,f.distal,f.pad])
	for c in data.g_archive.contents:
		extras.append(c.root)
		for r in c.rig:extras.append(r.name)
	module.effect.g_visuals.force_warm=true;module.effect.tick(0)
	for i in range(8):await process_frame
	module.effect.g_visuals.force_warm=false;module.apply_pose();module.effect.tick(0)
	await seconds(.4);await capture("00_six_records_rest")
	var visited:Array=[]
	for id in [1,0,2,3,4,5]:
		input(1,float(id),"begin")
		if id==1:
			await until(func():return player.stage=="lifting_record");await seconds(.22);await capture("01_actual_pick")
			await until(func():return player.stage=="placing_record");await seconds(.18);await capture("02_actual_place")
			await until(func():return player.stage=="reading");await seconds(.50);await capture("03_actual_read")
			await until(func():return player.stage=="printing");await seconds(.93);await capture("04_actual_print")
		var ok:=await until(func():return player.stage=="playing" and player.loaded_index==id)
		visited.append({"id":id,"played":ok});await capture("play_"+str(id+1))
		await seconds(.7);input(2,.72,"begin");input(5,1,"begin");await seconds(1.2);await capture("action_"+str(id+1));input(5,0,"release");await seconds(.8)
	input(3,1,"change");await seconds(2.0);input(3,0,"change");await seconds(.8)
	module.stow();await until(func():return module.settled(),16);await capture("05_all_returned")
	module.activate(3);await until(func():return module.explosion>.999,6);await capture("06_exploded")
	module.stow();await until(func():return module.explosion<.001,5);await capture("07_reassembled")
	input(1,2,"begin");await until(func():return player.stage=="lifting_record",5);module.stow();await until(func():return module.settled(),12);await capture("08_interrupted_return")
	FileAccess.open(OUT+"record_take.json",FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"model_sha256":model_hash,"metadata_sha256":metadata_hash,"samples":samples,"heights":module.effect.g_visuals.heights}))
	FileAccess.open(OUT+"take_report.json",FileAccess.WRITE).store_string(JSON.stringify({"frames":frame,"all_played":visited.all(func(x):return x.played),"visited":visited,"settled":module.settled(),"owners":player.owners},"  "))
	print("RECORD_TAKE_COMPLETE ",frame," frames");quit(0 if visited.all(func(x):return x.played) and module.settled() else 2)
