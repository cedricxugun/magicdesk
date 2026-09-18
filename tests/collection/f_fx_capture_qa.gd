extends SceneTree
func _initialize()->void:run.call_deferred()
func difference(a:Transform3D,b:Transform3D)->float:
	var value:float=a.origin.distance_to(b.origin)
	for i in range(3):value=maxf(value,a.basis[i].distance_to(b.basis[i]))
	return value
func run()->void:
	assert(RenderingServer.get_rendering_device()!=null,"This check needs the real renderer, not dummy MultiMesh getters")
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(14):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	module.play.input("trim",0.,"begin")
	for i in range(1800):
		service.tick(1./30.)
		if i%20==0:await RenderingServer.frame_post_draw
		if module.play.instrument.peak_time>=1.45:break
	await RenderingServer.frame_post_draw
	var fx:Node3D=module.effect.f_visuals;var pose_error:=0.;var value_error:=0.;var unique:Dictionary={};var count:=0
	for i in range(112):
		var node:MultiMeshInstance3D=fx.ticks if i<28 else fx.foil
		pose_error=maxf(pose_error,difference(node.multimesh.get_instance_transform(i),fx.captured_shards[i].transform))
		value_error=maxf(value_error,absf(node.multimesh.get_instance_custom_data(i).r-float(fx.captured_shards[i].gain)))
		pose_error=maxf(pose_error,difference(fx.glints.multimesh.get_instance_transform(i),fx.captured_glints[i].transform))
		value_error=maxf(value_error,absf(fx.glints.multimesh.get_instance_custom_data(i).r-float(fx.captured_glints[i].gain)))
		if i<28:unique[str(fx.captured_shards[i].transform.origin)]=true
		count+=2
	for j in range(3):
		for i in range(28):
			pose_error=maxf(pose_error,difference(fx.ribbons[j].multimesh.get_instance_transform(i),fx.captured_ribbons[j][i].transform))
			value_error=maxf(value_error,absf(fx.ribbons[j].multimesh.get_instance_custom_data(i).r-float(fx.captured_ribbons[j][i].gain)));count+=1
	var passed:bool=pose_error<.00001 and value_error<.00001 and unique.size()==28 and float(fx.captured_shards[0].gain)>.05
	var report:={"passed":passed,"instances":count,"pose_error":pose_error,"gain_error":value_error,"distinct_vernier_positions":unique.size(),"renderer":RenderingServer.get_video_adapter_name(),"capture_script_sha256":FileAccess.get_sha256("res://collection/f_visuals.gd"),"scope":"CPU recording buffers compared to real Metal MultiMesh getters at an earned calibration peak. Dummy renderer getters are not valid capture evidence."}
	FileAccess.open("res://../review/F_complete/revision_20260911/full_take/gpu_capture_parity.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("F_FX_CAPTURE_PARITY ",JSON.stringify(report))
	fx=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if passed else 1)
