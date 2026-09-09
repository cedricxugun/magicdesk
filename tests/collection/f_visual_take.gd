extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var samples:Array=[]
var captured:Dictionary={}
var output:="res://../review/F_complete"
var bake_only:=false
func _initialize()->void:run.call_deferred()
func vector(v:Vector3)->Array:return [snappedf(v.x,.000001),snappedf(v.y,.000001),snappedf(v.z,.000001)]
func transform(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();return {"p":vector(t.origin),"q":[q.x,q.y,q.z,q.w],"s":vector(t.basis.get_scale())}
func gesture(index:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver
	driver.index=index;driver.active=driver.profile(index);driver._set_value(value,event)
	if driver.active.gesture!="hold" or event=="release":driver.index=-1;driver.active={}
func capture(label:String)->void:
	if bake_only:return
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(ProjectSettings.globalize_path(output.path_join(label+".png")))
	print("F_VISUAL_CAPTURE ",label)
func run()->void:
	bake_only=OS.get_cmdline_user_args().has("--bake-only")
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(8):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);service=host.collection
	if bake_only:Engine.max_fps=0
	host.power=1;host.power_target=1;host.rotation_enabled=false;host.angle=0
	host.muted=true
	service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"))
	service.current=module;service.active_id="F";service._build_controls();host.tooltip.hide();host.toast.hide()
	module.effect.f_visuals.force_warm=true;module.effect.tick(0)
	for i in range(8):
		if bake_only:await process_frame
		else:await RenderingServer.frame_post_draw
	module.effect.f_visuals.force_warm=false
	var last_stage:="";var peak_capture:=false
	for frame in range(1321):
		var t:=frame/30.0
		if frame==30:gesture(1,.50,"begin")
		if frame==140:gesture(1,.85,"change")
		if frame==174:gesture(2,1.0,"begin")
		if frame==198:gesture(2,0.0,"release");gesture(1,0.0,"change")
		if frame==840:module.stow()
		if frame==1020:gesture(4,-.8,"change")
		if frame==1032:gesture(4,0.0,"release")
		if frame==1155:gesture(4,.8,"change")
		if frame==1167:gesture(4,0.0,"release")
		service.tick(1.0/30.0)
		var instrument:RefCounted=module.play.instrument
		if instrument.stage!=last_stage:print("F_STAGE ",t," ",instrument.stage);last_stage=instrument.stage
		var poses:Dictionary={}
		for item in module.controls:poses[str(item.node.name)]=transform(item.node.transform)
		for item in module.motions:poses[str(item.node.name)]=transform(item.node.transform)
		for item in module.parts:poses[str(item.node.name)]=transform(item.node.transform)
		for item in module.interactive_rig:poses[str(item.node.name)]=transform(item.node.transform)
		for item in [data.f_physics.plumb_pivot,data.f_physics.prism_pivot,data.f_physics.spring_preload,data.f_physics.receiver_lift,data.f_physics.receiver_slide,data.f_physics.brake_rotor]:poses[item]=transform(module.named(item).transform)
		for item in data.f_physics.transport_guides:poses[item.name]=transform(module.named(item.name).transform)
		var widgets:Array=[]
		for c in service.custom_controls:
			widgets.append({"gesture":service.control_driver.profile(c.index).gesture,"pose":transform(c.node.global_transform),"moving":c.moving.map(func(m):return transform(m.node.transform))})
		var sample:={"frame":frame+1,"time":t,"poses":poses,"widgets":widgets,"state":instrument.diagnostics(),"open":module.openness,"explosion":module.explosion}
		if frame%3==0:sample["fx"]=module.effect.f_visuals.state()
		samples.append(sample)
		if frame in [0,95,168,188,835,950,1130,1320]:await capture("frame_%04d"%frame)
		if instrument.peak_time>1.4 and instrument.peak_time<1.6 and not peak_capture:peak_capture=true;await capture("equilibrium_peak")
		if bake_only:await process_frame
		else:await RenderingServer.frame_post_draw
	FileAccess.open(ProjectSettings.globalize_path(output.path_join("physical_take.json")),FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"samples":samples},""))
	FileAccess.open(ProjectSettings.globalize_path(output.path_join("visual_take_report.json")),FileAccess.WRITE).store_string(JSON.stringify({"frames":samples.size(),"peak_captured":peak_capture,"physics_driven":true,"offline_take_not_fps_benchmark":true},"  "))
	quit(0 if peak_capture else 2)
