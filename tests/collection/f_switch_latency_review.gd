extends SceneTree
## Real-wall GPU transition trace. Requests models directly; never native input proof.
var host:Node3D
var service:Node3D
var out:String
var phases:Array=[]
var previous_state:=""
var previous_time:=0
var previous_frame:=0
var started:=0
var max_frame_ms:=0.
var samples:=0

func _initialize()->void:run.call_deferred()

func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):out=arg.trim_prefix("--out=")
	assert(not out.is_empty())
	DirAccess.make_dir_recursive_absolute(out)
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop");host.muted=true
	# Let startup prewarming complete through its normal path before requesting F.
	while host.collection==null:await process_frame
	service=host.collection
	for i in range(30):await process_frame
	var results:Array=[]
	for id in ["F","B"]:
		started=Time.get_ticks_usec();previous_time=started;previous_frame=started;previous_state="";phases=[];max_frame_ms=0.;samples=0
		service.request_model(id)
		while service.state!="idle" or service.active_id!=id:
			await process_frame
			var now:=Time.get_ticks_usec()
			max_frame_ms=maxf(max_frame_ms,(now-previous_frame)/1000.);previous_frame=now;samples+=1
			if previous_state!=service.state:
				if not previous_state.is_empty():phases.append({"state":previous_state,"wall_ms":(now-previous_time)/1000.})
				previous_state=service.state;previous_time=now
			if now-started>90000000:break
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(out.path_join(id+"_arrived.png"))
		if id=="F":
			service.pin_control_help(3)
			for i in range(3):await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(out.path_join("F_help.png"))
		var passed:bool=service.state=="idle" and service.active_id==id and service.diagnostics().base_instances==1
		if id=="F":passed=passed and service.load_metrics.get("warm_msaa",-1)==host.render_view.msaa_3d and service.load_metrics.get("warm_area_lights",0)>0 and not host.rotation_enabled and absf(host.angle)<.001
		results.append({"id":id,"passed":passed,"wall_ms":(Time.get_ticks_usec()-started)/1000.,"max_frame_ms":max_frame_ms,"samples":samples,"display_rotation":host.rotation_enabled,"display_angle":host.angle,"phases":phases.duplicate(true),"load_metrics":service.load_metrics.duplicate(true),"base_instances":service.diagnostics().base_instances})
		if not passed:break
	var passed:bool=results.size()==2 and results.all(func(x):return x.passed)
	var report:={"passed":passed,"results":results,"device":RenderingServer.get_video_adapter_name(),"engine":Engine.get_version_info().string,"scope":"Real-wall scripted GPU B/F/B transitions; pipeline cache is warm from prior work. Not OS pointer coverage, cold-cache speedup, or a performance acceptance result."}
	FileAccess.open(out.path_join("report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("F_SWITCH_LATENCY_REVIEW ",JSON.stringify(report))
	host=null;service=null;scene.queue_free();await process_frame;await process_frame;quit(0 if passed else 1)
