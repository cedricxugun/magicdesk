extends SceneTree
var checks:Array=[]
var violations:Array=[]
var stages:Dictionary={}
var data:Dictionary
func _initialize()->void:run.call_deferred()
func make()->Node3D:
	var module:Node3D=load("res://collection/module.gd").new();module.data=data;module.power=1;module.open_target=1
	module.play=load("res://collection/play_state.gd").new();module.play.values={"leaf":0.0,"fold":.5,"imprint":0.0,"spin":1.0}
	module.play.g_instrument=load("res://collection/record_player.gd").new();module.play.g_instrument.setup(module);return module
func advance(module:Node3D,dt:float)->void:
	var p:RefCounted=module.play.g_instrument;p.tick(dt);stages[p.stage]=true
	var count:=0
	for owner in p.owners:
		if owner!="slot":count+=1
	if count>1:violations.append("multiple records removed")
	if absf(p.spin_velocity)>TAU/60+.000001:violations.append("excess display spin")
	if p.stage=="printing" and (p.tone_lift<.169 or absf(p.tone_angle)>.001 or p.wrist_virtual.distance_to(p.PARK)>.001 or p.owners[p.loaded_index]!="platter"):violations.append("printing without clear tonearm/gripper and original media")
	if p.stage=="reading" and (p.wrist_virtual.distance_to(p.PARK)>.001 or p.tone_lift>.001):violations.append("reading before gripper clears")
	var tcp:Vector3=p.wrist_virtual+Basis(p.wrist_q)*Vector3.UP*.27;var shoulder:Vector3=module.v3(data.record_player.shoulder);var reach:float=tcp.distance_to(shoulder)
	if reach>1.30001 or reach<.05999:violations.append("arm outside analytic reach")
func until(module:Node3D,wanted:Callable,timeout:float=22.0)->bool:
	var t:=0.0;var i:=0
	while t<timeout:
		var dt:float=[.013,.018,.0167,.022][i%4];advance(module,dt);t+=dt;i+=1
		if wanted.call():return true
	return false
func check(name:String,ok:bool,detail:Variant=null)->void:checks.append({"check":name,"passed":ok,"detail":detail});print("RECORD_QA ",name," ",ok," ",detail)
func run()->void:
	data=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_record_player.json"))
	var module:=make();var p:RefCounted=module.play.g_instrument
	for i in range(6):
		p.changed("leaf",0,float(i),"begin")
		check("record_%d_load_read_print"%(i+1),until(module,func():return p.stage=="playing" and p.loaded_index==i),p.stage)
		check("record_%d_only_its_slot_empty"%(i+1),p.owners[i]=="platter" and p.owners.count("slot")==5,p.owners.duplicate())
	var start:float=p.platter_angle
	for i in range(600):advance(module,1.0/60)
	check("sixty_second_turn_rate",absf((p.platter_angle-start)-TAU/6)<.002,p.platter_angle-start)
	p.pause_spin()
	for i in range(50):advance(module,1.0/60)
	start=p.platter_angle
	for i in range(60):advance(module,1.0/60)
	check("stop_remains_stopped",absf(p.platter_angle-start)<.000001)
	module.open_target=0;module.stowing=true
	check("sleep_returns_all_original_records",until(module,func():return p.ready_to_fold()),p.owners.duplicate());module.free()
	var targets:Array=stages.keys()
	for target in targets:
		if target in ["sleep","paused"]:continue
		module=make();p=module.play.g_instrument
		if str(target).begins_with("return_") or target in ["erasing","braking_record","parking_magazine"]:
			until(module,func():return p.stage=="playing");module.open_target=0;module.stowing=true
		var reached:=until(module,func():return p.stage==target,15)
		if reached:
			module.open_target=0;module.stowing=true
			check("safe_exit_from_"+str(target),until(module,func():return p.ready_to_fold(),12),p.stage)
		module.free()
	check("continuous_ownership_reach_and_print_gates",violations.is_empty(),violations.slice(0,12))
	var ok:bool=checks.all(func(c):return c.passed)
	FileAccess.open("res://../review/G_record_player/state_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"all_passed":ok,"checks":checks,"stages":stages.keys()},"  "));quit(0 if ok else 2)
