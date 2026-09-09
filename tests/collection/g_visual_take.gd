extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var samples:Array=[]
var checks:Array=[]
var output:="res://../review/G_complete"
var bake_only:=false
func _initialize()->void:run.call_deferred()
func vector(v:Vector3)->Array:return [v.x,v.y,v.z]
func transform(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();return {"p":vector(t.origin),"q":[q.x,q.y,q.z,q.w],"s":vector(t.basis.get_scale())}
func gesture(index:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=index;driver.active=driver.profile(index);driver._set_value(value,event)
	if driver.active.gesture!="hold" or event=="release":driver.index=-1;driver.active={}
func check(label:String,passed:bool,detail:Variant=null)->void:
	checks.append({"check":label,"passed":passed,"detail":detail});print("G_CHECK ",label," ",passed," ",detail)
func capture(label:String)->void:
	if bake_only:return
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(ProjectSettings.globalize_path(output.path_join(label+".png")))
func run()->void:
	bake_only=OS.get_cmdline_user_args().has("--bake-only")
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(8):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);service=host.collection
	if bake_only:Engine.max_fps=0
	host.power=1;host.power_target=1;host.rotation_enabled=false;host.angle=0;host.muted=true
	service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_complete.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_complete.glb"))
	service.current=module;service.active_id="G";service._build_controls();host.tooltip.hide();host.toast.hide()
	module.effect.g_visuals.force_warm=true;module.effect.tick(0)
	for i in range(8):await process_frame
	module.effect.g_visuals.force_warm=false
	var instrument:RefCounted=module.play.g_instrument;var paused_progress:=0.0;var peak_captured:=false
	var pose_names:Array=[]
	for item in data.g_mechanism.leaves:
		pose_names.append_array([item.writer,item.register])
		for support in item.supports:pose_names.append(support.node)
	for item in data.g_mechanism.get("covers",[]):
		for support in item.supports:pose_names.append(support.node)
	pose_names.append(data.g_mechanism.relief)
	for frame in range(1441):
		if frame==30:gesture(1,0,"begin")
		if frame==135:gesture(2,.95,"change")
		if frame==175:gesture(5,1,"begin")
		if frame==210:
			check("misregistration_blocks_writer",instrument.blocked and instrument.records[0]==0,instrument.alignment);gesture(5,0,"release");gesture(2,.5,"change")
		if frame==255:gesture(5,1,"begin")
		if frame==290:gesture(5,0,"release");paused_progress=instrument.records[0]
		if frame==340:
			check("release_preserves_partial_record",paused_progress>.05 and absf(paused_progress-instrument.records[0])<.00001,paused_progress);gesture(1,1,"change");gesture(2,.76,"change")
		if frame==380:gesture(1,0,"change");check("per_leaf_fold_recalled",module.play.number("fold")==.5)
		if frame==395:gesture(1,1,"change");check("other_leaf_fold_retained",absf(module.play.number("fold")-.76)<.0001);gesture(2,.5,"change")
		if frame==410:gesture(1,0,"change")
		if frame==445:gesture(5,1,"begin")
		if frame==565:gesture(5,0,"release")
		if frame==780:module.stow()
		if frame==940:check("rewind_clears_pins_head_projection_before_fold",module.openness<.001 and instrument.ready_to_fold());gesture(4,-.8,"change")
		if frame==952:gesture(4,0,"release")
		if frame==1060:check("full_service_extraction",module.explosion>.999);gesture(4,.8,"change")
		if frame==1072:gesture(4,0,"release")
		if frame==1180:check("exact_reassembly",module.explosion<.001 and module.openness<.001);gesture(1,3,"begin")
		if frame==1205:module.stow()
		if frame==1330:check("mid_open_reverse_returns_to_rest",module.settled())
		service.tick(1.0/30.0)
		var poses:Dictionary={}
		for item in module.controls:poses[str(item.node.name)]=transform(item.node.transform)
		for item in module.parts:poses[str(item.node.name)]=transform(item.node.transform)
		for name in pose_names:poses[name]=transform(module.named(name).transform)
		var widgets:Array=[]
		for c in service.custom_controls:widgets.append({"gesture":service.control_driver.profile(c.index).gesture,"pose":transform(c.node.global_transform),"moving":c.moving.map(func(m):return transform(m.node.transform))})
		var sample:={"frame":frame+1,"poses":poses,"widgets":widgets,"state":instrument.diagnostics(),"open":module.openness,"explosion":module.explosion}
		if frame%3==0:sample["fx"]=module.effect.g_visuals.state()
		samples.append(sample)
		if frame in [0,85,200,280,325,500,740,920,1050,1175,1440]:await capture("frame_%04d"%frame)
		if instrument.peak_time>2.0 and not peak_captured:
			peak_captured=true;check("earned_memory_relief",instrument.records[0]>.999 and instrument.alignment>.93);await capture("memory_relief")
		if bake_only:await process_frame
		else:await RenderingServer.frame_post_draw
	check("signature_visited",peak_captured)
	FileAccess.open(ProjectSettings.globalize_path(output.path_join("mechanical_take.json")),FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"samples":samples}))
	var passed:bool=checks.all(func(c):return c.passed)
	FileAccess.open(ProjectSettings.globalize_path(output.path_join("mechanism_qa.json")),FileAccess.WRITE).store_string(JSON.stringify({"all_passed":passed,"checks":checks,"offline_take_not_fps_benchmark":true},"  "))
	quit(0 if passed else 2)
