extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(60):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.rotation_enabled=false;host._set_desktop_zoom(1.0);host.toast.hide()
	var rows:Array=[]
	var lights:Array=host.find_children("*","Light3D",true,false)
	var shadows:Array=[]
	for light in lights:shadows.append(light.shadow_enabled)
	var ssil:bool=host.env.ssil_enabled;var ssao:bool=host.env.ssao_enabled
	for mode in ["baseline","ssil_off","ssao_off","volume_off","shadows_off","baseline_repeat"]:
		host.render_view.msaa_3d=Viewport.MSAA_4X
		host.env.ssil_enabled=ssil and mode!="ssil_off";host.env.ssao_enabled=ssao and mode!="ssao_off"
		for i in range(lights.size()):lights[i].shadow_enabled=shadows[i] and mode!="shadows_off"
		if host.camera.compositor:
			for effect in host.camera.compositor.compositor_effects:effect.enabled=mode!="volume_off"
		for i in range(45):await RenderingServer.frame_post_draw
		var elapsed:Array[float]=[];var last:=Time.get_ticks_usec()
		for i in range(120):
			await RenderingServer.frame_post_draw
			var now:=Time.get_ticks_usec();elapsed.append((now-last)/1000.0);last=now
		elapsed.sort()
		rows.append({"variant":mode,"frames":elapsed.size(),"median_ms":elapsed[60],"p95_ms":elapsed[113],"canvas":str(host.canonical_size)})
		host.render_view.get_texture().get_image().save_png("res://../review/desktop_scale/budget_%s.png"%mode)
	FileAccess.open("res://../review/desktop_scale/render_ablation.json",FileAccess.WRITE).store_string(JSON.stringify({"runs":rows,"scope":"Actual GPU B idle, 120 wall-time frame intervals per mode after warmup, editor executable, not native exported bundle or all-model benchmark"},"  "))
	print("DESKTOP_RENDER_ABLATION ",JSON.stringify(rows))
	host=null;scene.queue_free();await process_frame;await process_frame;quit()
