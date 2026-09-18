extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.rotation_enabled=false;host.angle=0
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var rows:Array=[]
	for entry in service.registry:
		if entry.id=="B":continue
		var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(entry.metadata))
		var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load(entry.scene))
		for size in [1.0,1.10]:
			host._set_desktop_zoom(size)
			for state in [Vector2(0,0),Vector2(.5,0),Vector2(1,0),Vector2(0,.5),Vector2(0,1)]:
				module.openness=state.x;module.explosion=state.y;module.apply_pose()
				var points:Array[Vector2]=[];service._screen_points(module.asset,points);service._screen_points(host.fixed_base,points)
				var bounds:=Rect2(points[0],Vector2.ZERO)
				for point in points:bounds=bounds.expand(point)
				rows.append({"id":entry.id,"zoom":size,"open":state.x,"explode":state.y,"bounds":str(bounds),"inside":Rect2(Vector2.ZERO,Vector2(host.canonical_size)).encloses(bounds)})
		module.queue_free();await process_frame;await process_frame
	var report:={"passed":rows.all(func(r):return r.inside),"samples":rows,"scope":"Authored shell/open/exploded pose bounds at 100 and 110 percent, fixed common camera; not full dynamics/VFX, G curiosity extrema or native input"}
	FileAccess.open("res://../review/desktop_scale/all_model_bounds.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("DESKTOP_ALL_BOUNDS ",JSON.stringify({"passed":report.passed,"samples":rows.size(),"outside":rows.filter(func(r):return not r.inside)}))
	service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 1)
