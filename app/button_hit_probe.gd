extends SceneTree

func _initialize()->void:call_deferred("run")

func run()->void:
	var scene=load("res://main.tscn").instantiate()
	root.add_child(scene)
	for i in range(8):await process_frame
	var host=scene.get_node("Render/HeliosDesktop")
	host.set_process(false)
	var failures:Array=[]
	var checks:=0
	for pose in [0.0,.5,1.0]:
		host.openness=pose;host.explosion=0.0;host._apply_mechanism()
		for i in range(host.buttons.size()):
			var cap:Node3D=host.buttons[i].cap
			for local in [Vector3(0,.008,0),Vector3(.075,.008,0),Vector3(-.075,.008,0),Vector3(0,.008,.075),Vector3(0,.008,-.075)]:
				var pixel:Vector2=host.camera.unproject_position(cap.to_global(local))
				var hit:int=host.hit_button(pixel)
				checks+=1
				if hit!=i:failures.append({"pose":pose,"button":i,"local":str(local),"hit":hit})
		var quit_cap:Node3D=host.buttons[6].cap
		for angle in range(16):
			var a:=angle*TAU/16.0
			var pixel:Vector2=host.camera.unproject_position(quit_cap.to_global(Vector3(cos(a)*.140,.008,sin(a)*.140)))
			checks+=1
			if host.hit_button(pixel)==6:failures.append({"pose":pose,"invisible_close_margin":angle})
	var last:=0.0
	for sample in range(351):
		var value:float=host.opening_fraction(float(sample)/100.0)
		if value<last-.000001 or value<0.0 or value>1.000001:failures.append({"non_monotonic_opening":sample})
		last=value
	var speed_at_old_stop:float=(host.opening_fraction(2.801)-host.opening_fraction(2.799))/.002
	if speed_at_old_stop<.2:failures.append({"opening_pauses_at_old_handoff":speed_at_old_stop})
	var report:={"checks":checks,"all_passed":failures.is_empty(),"failures":failures,"opening_speed_at_2_8s":speed_at_old_stop,"opening_finishes_at_3_5s":absf(host.opening_fraction(3.5)-1.0)<.000001}
	var path:=ProjectSettings.globalize_path("res://../tests/button_hit_validation.json")
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("BUTTON_HIT_CHECK ",JSON.stringify(report))
	scene.queue_free()
	await process_frame
	await process_frame
	quit(0 if failures.is_empty() else 2)
