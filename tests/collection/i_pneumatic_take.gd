extends SceneTree
func _initialize()->void:
	var a:RefCounted=load("res://collection/i_acoustics.gd").new()
	var samples:Array=[];var opening:=0.
	for frame in range(361):
		var t:=frame/30.
		if frame==8:a.set_controls(.72,.8);a.start()
		if frame==45:a.set_pressed(true)
		if frame==90:a.set_pressed(false)
		if frame==150:a.set_pressed(true)
		if frame==180:a.set_pressed(false)
		if frame==185:a.quiet()
		if frame==240:a.set_controls(.2,0.);a.start()
		if frame==255:a.set_pressed(true)
		if frame==285:a.set_pressed(false)
		if frame==306:a.quiet()
		a.tick(1./30.)
		var target:float=1. if a.listening else 0. if a.ready_to_close() else opening
		opening=move_toward(opening,target,2./30.)
		samples.append({"frame":frame+1,"time":t,"opening":opening,"state":a.state(),"events":a.drain_events()})
	var out:="res://../review/I_refinement/r2/pneumatic_take.json"
	DirAccess.make_dir_recursive_absolute(out.get_base_dir())
	FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"samples":samples,"scope":"Normalized pressure model driving proposed geometry; visual diaphragm displacement uses declared amplification. No runtime integration or audio yet."},""))
	print("I_PNEUMATIC_TAKE ",samples.size());quit()
