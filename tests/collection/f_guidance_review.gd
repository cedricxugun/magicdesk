extends SceneTree
const Guidance=preload("res://collection/f_guidance.gd")
var checks:Array=[]
var module:Node3D
func _initialize()->void:run.call_deferred()
func check(label:String,ok:bool,detail:Variant=null)->void:checks.append({"label":label,"passed":ok,"detail":detail})
func step(frames:int)->void:
	for i in range(frames):module.tick(1./60.,1.)
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false)
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	check("closed_instrument_explains_first_action",Guidance.next_step(module).code=="release")
	host.rotation_enabled=true;module.play.input("trim",0.,"begin")
	check("operating_F_pauses_display_rotation",not host.rotation_enabled)
	module.stow();step(1800)
	var routes:Array=[]
	for sign in [-1.,1.]:
		module.stow();step(1800)
		module.play.input("trim",sign,"begin");module.play.input("trim",sign,"release")
		module.play.input("polarity",sign,"begin");module.play.input("polarity",sign,"release")
		step(1500)
		var f:RefCounted=module.play.instrument;var peaks:int=f.peak_count;var route:Array=[]
		for attempt in range(35):
			var advice:Dictionary=Guidance.next_step(module);route.append({"code":advice.code,"theta":f.physics.theta,"trim":module.play.number("trim")})
			if advice.code in ["trim_up","trim_down"]:
				var value:float=clampf(module.play.number("trim")+(.08 if advice.code=="trim_up" else -.08),-1.,1.)
				module.play.input("trim",value,"begin");module.play.input("trim",value,"release")
			step(240)
			if f.peak_count>peaks:break
		check("guidance_reaches_real_balance_from_%s"%sign,f.peak_count>peaks,{"routes":route.size(),"peak_count":f.peak_count,"coherence":f.coherence})
		routes.append(route)
	module.play.input("brake",1.,"begin");step(240)
	check("held_brake_requests_release",Guidance.next_step(module).code=="release_brake")
	module.play.input("brake",0.,"release");module.activate(3);step(1800)
	check("exploded_instrument_requests_assembly",Guidance.next_step(module).code=="assemble")
	var result:={"passed":checks.all(func(c):return c.passed),"checks":checks,"routes":routes,"scope":"Guidance applied to actual solver from both biased extremes. No injected peak/charge; no native usability acceptance."}
	FileAccess.open("res://../review/F_complete/revision_20260911/guidance_qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_GUIDANCE_REVIEW ",JSON.stringify(result))
	module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
