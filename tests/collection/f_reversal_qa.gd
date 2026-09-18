extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var f:RefCounted
var checks:Array=[]
var mixed_states:=0
var max_step:=0.
var link_error:=0.
var previous:Dictionary={}
var cases:Array=[]
func _initialize()->void:run.call_deferred()
func check(name:String,ok:bool,detail:Variant=null)->void:checks.append({"name":name,"passed":ok,"detail":detail})
func gesture(slot:int,value:float,event:String)->void:
	var d:RefCounted=service.control_driver;d.index=slot;d.active=d.profile(slot);d._set_value(value,event)
	if d.active.gesture!="hold" or event=="release":d.index=-1;d.active={}
func step(seconds:float)->void:
	for i in range(roundi(seconds*60.)):
		service.tick(1./60.)
		if module.explosion>.001 and module.openness>.001:mixed_states+=1
		for pair in [["UpperFourBar",.82],["LowerFourBar",1.01],["Coupler",.50],["CounterArm",.66]]:
			var a:Node3D=module.named("F_C_"+pair[0]+"_end0");var b:Node3D=module.named("F_C_"+pair[0]+"_end1")
			link_error=maxf(link_error,absf(a.position.distance_to(b.position)-float(pair[1])))
		for name in [module.data.f_physics.plumb_pivot,module.data.f_physics.prism_pivot,module.data.f_physics.receiver_lift]:
			var node:Node3D=module.named(name);var p:Vector3=node.global_position
			assert(p.is_finite())
			if previous.has(name):max_step=maxf(max_step,p.distance_to(previous[name]))
			previous[name]=p
func reset()->void:
	service.control_driver.cancel();gesture(1,0.,"change");gesture(5,0.,"change");module.stow();step(15.)
	check("case_cleanup_%d"%cases.size(),module.settled(),f.diagnostics())
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false
	service=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls();f=module.play.instrument
	gesture(1,.7,"begin");step(.8);check("opening_is_partial",module.openness>.1 and module.openness<.8)
	module.stow();step(.2);gesture(1,.2,"begin");step(8.)
	check("reopen_during_opening_cancel",module.openness>.999 and module.explosion<.001 and f.physics.free);cases.append("partial_open_stow_reopen");reset()
	gesture(1,.8,"begin");step(6.);gesture(2,1.,"begin");step(.7);module.stow();step(.2)
	gesture(2,0.,"release");gesture(1,0.,"begin");step(10.)
	check("reopen_after_held_brake_stow",module.openness>.999 and f.physics.brake==0. and service.control_driver.index<0);cases.append("brake_stow_release_reopen");reset()
	gesture(4,-.8,"change");step(.8);check("disassembly_is_partial",module.explosion>.1 and module.explosion<.8)
	gesture(4,.8,"change");step(.2);gesture(1,0.,"begin");step(10.)
	check("reverse_partial_disassembly_then_open",module.explosion<.001 and module.openness>.999);cases.append("partial_disassembly_assemble_open");reset()
	gesture(1,0.,"begin");step(5.);gesture(4,-.8,"change");step(8.)
	check("service_from_free_motion_folds_first",module.explosion>.999 and module.openness<.001 and not f.physics.free)
	gesture(4,.8,"change");step(8.);check("complete_service_returns_exact_homes",module.settled() and module.parts.all(func(p):return p.node.transform.is_equal_approx(p.home)));cases.append("open_service_assemble")
	check("no_open_and_exploded_mixture",mixed_states==0,mixed_states);check("constant_closed_link_lengths",link_error<.00001,link_error);check("no_large_tracked_support_teleport",max_step<.07,max_step)
	var result:={"passed":checks.all(func(c):return c.passed),"checks":checks,"cases":cases,"scope":"Actual controller driver inputs and fixed-step mechanism simulation for four reversal sequences. Tracks three support origins, local link lengths and assembly ordering; not all vertex sweeps or native mouse acceptance."}
	FileAccess.open("res://../review/F_complete/revision_20260911/reversal_qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_REVERSAL_QA ",JSON.stringify(result))
	f=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
