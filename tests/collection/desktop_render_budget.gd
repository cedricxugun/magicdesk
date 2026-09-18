extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(60):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.rotation_enabled=false;host._set_desktop_zoom(1.0);host.toast.hide()
	var rows:Array=[]
	for mode in [Viewport.MSAA_4X,Viewport.MSAA_2X]:
		host.render_view.msaa_3d=mode
		for i in range(45):await RenderingServer.frame_post_draw
		var elapsed:Array[float]=[];var last:=Time.get_ticks_usec()
		for i in range(180):
			await RenderingServer.frame_post_draw
			var now:=Time.get_ticks_usec();elapsed.append((now-last)/1000.0);last=now
		elapsed.sort()
		rows.append({"msaa":4 if mode==Viewport.MSAA_4X else 2,"frames":elapsed.size(),"median_ms":elapsed[90],"p95_ms":elapsed[170],"canvas":str(host.canonical_size)})
		host.render_view.get_texture().get_image().save_png("res://../review/desktop_scale/msaa_%d.png"%(4 if mode==Viewport.MSAA_4X else 2))
	FileAccess.open("res://../review/desktop_scale/render_budget.json",FileAccess.WRITE).store_string(JSON.stringify({"runs":rows,"scope":"Actual GPU B idle, 180 wall-time frame intervals per mode after warmup, editor executable, not native exported bundle or all-model benchmark"},"  "))
	print("DESKTOP_RENDER_BUDGET ",JSON.stringify(rows))
	host=null;scene.queue_free();await process_frame;await process_frame;quit()
