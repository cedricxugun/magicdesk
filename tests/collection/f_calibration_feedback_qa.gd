extends SceneTree
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(name:String,ok:bool,value:Variant=null)->void:checks.append({"name":name,"passed":ok,"detail":value})
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(8):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false)
	var service:Node3D=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	var f:RefCounted=module.play.instrument;module.play.input("trim",0.,"begin")
	for i in range(2400):
		module.tick(1./60.,1.)
		if f.charge>.45 and not f.peak_latched:break
	check("physical_stability_earns_progress",f.charge>.45 and f.charge<.9,f.charge)
	var before:float=f.charge;var peaks:int=f.peak_count
	service.control_driver.index=1;module.play.input("trim",0.,"begin")
	for i in range(18):module.tick(1./60.,1.)
	check("touch_without_movement_keeps_progress",f.charge>=before-.001,[before,f.charge])
	check("touch_does_not_trigger_calibration",f.peak_count==peaks)
	service.control_driver.index=-1;module.play.input("trim",0.,"release")
	for i in range(180):module.tick(1./60.,1.)
	check("release_continues_earned_calibration",f.peak_count==peaks+1)
	peaks=f.peak_count;module.play.input("trim",1.,"change")
	for i in range(30):module.tick(1./60.,1.)
	check("preload_in_transit_cannot_calibrate",f.peak_count==peaks and not f.calibration_ready,f.diagnostics())
	check("aborted_field_is_not_labelled_equilibrium",f.stage!="equilibrium")
	module.play.input("brake",1.,"begin")
	for i in range(180):module.tick(1./60.,1.)
	check("clamped_mechanism_not_mistaken_for_balance",f.peak_count==peaks and f.calibration_reason=="brake")
	module.play.input("brake",0.,"release");module.play.input("trim",0.,"change")
	for i in range(1800):module.tick(1./60.,1.)
	check("real_rebalance_can_calibrate_again",f.peak_count==peaks+1,f.peak_count)
	module.stow()
	for i in range(900):module.tick(1./60.,1.)
	check("still_parks_before_closing",module.settled())
	var result:={"passed":checks.all(func(c):return c.passed),"checks":checks,"physics_source_sha256":FileAccess.get_sha256("res://collection/f_dynamics.gd"),"scope":"Calibration eligibility/progress behavior; no force coefficients or model geometry changed. Visual console indicators pending."}
	FileAccess.open("res://../review/F_complete/revision_20260911/calibration_feedback.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_CALIBRATION_FEEDBACK ",JSON.stringify(result))
	f=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
