extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var samples:Array=[]
var checks:Array=[]
var bake_only:=false
var ordering_failures:Array=[]
const OUT:="res://../review/G_archive/"
func _initialize()->void:run.call_deferred()
func pack(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale();return {"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
func check(label:String,ok:bool,detail:Variant=null)->void:checks.append({"check":label,"passed":ok,"detail":detail});print("G_ARCHIVE ",label," ",ok," ",detail)
func input(index:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=index;driver.active=driver.profile(index);driver._set_value(value,event)
	if index!=5 or event=="release":driver.index=-1;driver.active={}
func capture(name:String)->void:
	if bake_only:return
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(ProjectSettings.globalize_path(OUT+name+".png"))
func run()->void:
	bake_only=OS.get_cmdline_user_args().has("--bake-only")
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(8):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);service=host.collection;host.power=1;host.power_target=1;host.rotation_enabled=false;host.angle=0;host.muted=true
	if bake_only:Engine.max_fps=0
	service._legacy_set_visible(false);service._set_base_frame("shared")
	var model:="G_archive"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--model="):model=arg.trim_prefix("--model=")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/"+model+".json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/"+model+".glb"));service.current=module;service.active_id="G";service._build_controls();host.tooltip.hide();host.toast.hide()
	var g:RefCounted=module.play.g_instrument
	var extras:Array=[data.g_archive.lift,data.g_archive.slide]
	for l in data.g_archive.locks:extras.append(l.name)
	for leaf in data.g_mechanism.leaves:
		extras.append_array([leaf.writer,leaf.register])
		for s in leaf.supports:extras.append(s.node)
	for cover in data.g_mechanism.covers:
		for s in cover.supports:extras.append(s.node)
	for c in data.g_archive.contents:
		extras.append(c.root)
		for r in c.rig:extras.append(r.name)
	module.effect.g_visuals.force_warm=true;module.effect.tick(0)
	for i in range(8):await process_frame
	module.effect.g_visuals.force_warm=false
	var last_display:=0.0;var last_open:=0.0
	for frame in range(2351):
		if frame==30:input(1,0,"begin")
		for i in range(6):
			var start:int=210+i*240
			if frame==start:input(1,float(i),"begin")
			if frame==start+135:
				check("page_%d_auto_reads_own_specimen"%(i+1),g.loaded_index==i and g.display_amount>.99 and g.stage=="playing",g.diagnostics());input(2,.2 if i%2==0 else .8,"begin")
			if frame==start+160:input(5,1,"begin")
			if frame==start+190:check("page_%d_own_action_responds"%(i+1),g.action_energy>.99 and g.writing);await capture("specimen_"+str(i+1))
			if frame==start+210:input(5,0,"release")
		if frame==1690:module.stow()
		if frame==1840:check("sleep_is_fully_closed_and_platen_retracted",module.openness<.001 and g.platform_amount<.001 and g.loaded_index==-1);await capture("closed_case")
		if frame==1850:module.activate(3)
		if frame==1940:check("complete_service_disassembly",module.explosion>.999 and module.parts.size()==int(data.part_count));await capture("exploded_case")
		if frame==1970:module.stow()
		if frame==2070:input(1,1,"begin")
		if frame==2090:module.stow()
		if frame==2280:check("interrupted_opening_returns_to_sealed_sleep",module.settled() and g.stage=="sleep")
		service.tick(1.0/30)
		if g.stage=="reading" and not (module.openness>.995 and g.platform_amount>.99 and g.pages_settled()):ordering_failures.append({"frame":frame,"error":"reading before book/page/platen ready"})
		if last_display<.001 and g.display_amount>.001 and not (g.read_progress>=1 and g.loaded_index==g.selected and g.pages_settled()):ordering_failures.append({"frame":frame,"error":"specimen appeared before reading completion"})
		if module.openness<last_open-.0001 and not g.ready_to_fold():ordering_failures.append({"frame":frame,"error":"book closed before mechanisms cleared"})
		last_display=g.display_amount;last_open=module.openness
		var poses:Dictionary={}
		for c in module.controls:poses[str(c.node.name)]=pack(c.node.transform)
		for p in module.parts:poses[str(p.node.name)]=pack(p.node.transform)
		for name in extras:poses[name]=pack(module.named(name).transform)
		var widgets:Array=[]
		for c in service.custom_controls:widgets.append({"gesture":service.control_driver.profile(c.index).gesture,"pose":pack(c.node.global_transform),"moving":c.moving.map(func(m):return pack(m.node.transform))})
		var sample:={"frame":frame+1,"poses":poses,"widgets":widgets,"state":g.diagnostics(),"open":module.openness,"explosion":module.explosion}
		if frame%3==0:sample.fx=module.effect.g_visuals.state()
		samples.append(sample)
		if frame==0:await capture("initial_closed")
		if bake_only:await process_frame
		else:await RenderingServer.frame_post_draw
	check("read_reconstruct_and_closure_order",ordering_failures.is_empty(),ordering_failures)
	var ok:bool=checks.all(func(c):return c.passed)
	FileAccess.open(OUT+"archive_take.json",FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"samples":samples}))
	FileAccess.open(OUT+"mechanism_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"all_passed":ok,"checks":checks},"  "))
	quit(0 if ok else 2)
