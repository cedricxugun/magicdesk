extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	module.play.input("trim",0.,"begin");var f:RefCounted=module.play.instrument
	for i in range(1800):
		service.tick(1./60.)
		if f.peak_time>=.08:break
	assert(f.peak_time>=.08)
	var gpu:bool=RenderingServer.get_rendering_device()!=null
	if gpu:
		await RenderingServer.frame_post_draw
		host.render_view.get_texture().get_image().save_png("res://../review/F_complete/revision_20260911/cancel_before.png")
	var before_draw:float=module.effect.f_visuals.draw_gain
	var before:float=f.peak();var before_crest:float=f.crest();var samples:Array=[];var previous:=before;var rises:=0
	module.stow()
	for i in range(60):
		service.tick(1./60.);var value:float=f.peak()
		if value>previous+.000001:rises+=1
		samples.append({"t":(i+1)/60.,"peak":value,"crest":f.crest(),"draw_gain":module.effect.f_visuals.draw_gain});previous=value
		if gpu and i in [5,29,59]:
			await RenderingServer.frame_post_draw
			host.render_view.get_texture().get_image().save_png("res://../review/F_complete/revision_20260911/cancel_%02d.png"%(i+1))
	for i in range(720):service.tick(1./60.)
	var smooth_first_frame:bool=float(samples[0].draw_gain)>=before_draw*.80 and float(samples[0].draw_gain)<=before_draw+.0001
	var result:={"passed":rises==0 and module.settled() and smooth_first_frame,"first_frame_fade_bounded":smooth_first_frame,"before_draw_gain":before_draw,"gpu":gpu,"before_peak":before,"before_crest":before_crest,"brightening_frames_after_cancel":rises,"settled":module.settled(),"samples":samples,"scope":"Cancel a genuinely earned calibration while its optical envelope is still rising; no manual peak state injection."}
	var path:="res://../review/F_complete/revision_20260911/cancel_rise_qa.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):path=arg.trim_prefix("--out=")
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_CANCEL_RISE ",JSON.stringify({"passed":result.passed,"before":before,"rises":rises,"max_after":samples.map(func(s):return s.peak).max()}))
	f=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
