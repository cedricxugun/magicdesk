extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	var fx:Node3D=module.effect.f_visuals
	var timings:Array=[]
	for pass_index in range(5):
		var begin:=Time.get_ticks_usec()
		for i in range(300):fx.tick(1./60.,1.)
		timings.append((Time.get_ticks_usec()-begin)/300000.)
	var idle_clear:bool=not fx.foil.visible and not fx.ticks.visible and not fx.glints.visible and not fx.filament.visible and fx.ribbons.all(func(n):return not n.visible) and fx.lights.all(func(l):return l.light_energy==0.)
	module.play.input("trim",.4,"begin")
	for i in range(300):service.tick(1./60.)
	var resumed:bool=module.openness>.99 and fx.foil.visible and fx.captured_shards.all(func(s):return s.transform.origin.is_finite())
	module.stow()
	for i in range(900):service.tick(1./60.)
	var cleared:bool=module.settled() and not fx.foil.visible and fx.draw_gain<.0001
	var report:={"passed":idle_clear and resumed and cleared,"idle_clear":idle_clear,"resumes_finitely":resumed,"clears_after_stow":cleared,"milliseconds_per_idle_fx_tick":timings,"scope":"Isolated CPU effect-update timings in dummy renderer, 5x300 calls; not native FPS or whole-frame performance."}
	var path:="res://../review/F_complete/revision_20260911/idle_effect_qa.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):path=arg.trim_prefix("--out=")
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("F_IDLE_EFFECT_QA ",JSON.stringify(report))
	fx=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 1)
