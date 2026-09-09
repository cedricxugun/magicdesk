extends SceneTree
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(name:String,passed:bool,detail:Variant="")->void:
	checks.append({"check":name,"passed":passed,"detail":str(detail)});print("F_INSTRUMENT ",name," ",passed," ",detail)
func simulate(m:Node3D,t:float)->void:
	for i in range(roundi(t*60)):m.tick(1.0/60,1)
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(6):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.collection.set_process(false)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var m:Node3D=load("res://collection/module.gd").new();host.collection.add_child(m);m.setup(host,data,load("res://assets/collection/models/F_complete.glb"))
	host.collection._legacy_set_visible(false);host.collection._set_base_frame("shared");host.collection.current=m;host.collection.active_id="F";host.collection._build_controls()
	check("single_authoritative_base",host.collection.diagnostics().base_instances==1)
	var f:RefCounted=m.play.instrument
	m.play.input("trim",.4,"begin")
	var length_error:=0.0
	for i in range(600):
		m.tick(1.0/60,1)
		for link in [["UpperFourBar",.82],["LowerFourBar",1.01],["Coupler",.50],["CounterArm",.66]]:
			var a:Node3D=m.named("F_C_"+str(link[0])+"_end0");var b:Node3D=m.named("F_C_"+str(link[0])+"_end1")
			length_error=maxf(length_error,absf(a.position.distance_to(b.position)-float(link[1])))
	check("four_bar_has_constant_link_lengths",length_error<.00001,length_error)
	check("lower_ground_pin_is_at_frame_foot",absf(m.named("F_C_LowerFourBar_end0").position.y-.934)<.000001)
	var plumb:Node3D=m.named(data.f_physics.plumb_pivot);var prism:Node3D=m.named(data.f_physics.prism_pivot)
	check("both_suspensions_follow_physics",(plumb.global_basis*Vector3.DOWN).normalized().distance_to(f.physics.direction)<.00001 and (prism.global_basis*Vector3.DOWN).normalized().distance_to(f.physics.right_direction)<.00001)
	m.play.input("brake",1.0,"begin");simulate(m,.8)
	check("brake_stops_beam_not_forced_mass_pose",absf(f.physics.omega)<.006 and f.physics.direction.is_finite())
	m.play.input("brake",0.0,"release");m.play.input("trim",0.0,"change")
	var got_peak:=false;var peak_was_stable:=false
	for i in range(1800):
		m.tick(1.0/60,1)
		if f.peak_time>=0:
			got_peak=true
			if f.peak_time<.10:peak_was_stable=f.coherence>.70
	check("earned_equilibrium_effect_occurs",got_peak,f.diagnostics())
	check("climax_requires_physical_stability",peak_was_stable)
	var peaks_before:int=f.peak_count
	m.play.input("trim",.001,"change");host.collection.control_driver.index=1;simulate(m,3)
	check("held_control_defers_calibration",f.peak_count==peaks_before and f.charge<.01)
	host.collection.control_driver.index=-1;simulate(m,3)
	check("slow_small_adjustment_rearms_calibration",f.peak_count>peaks_before)
	var intensity:float=f.peak();m.play.input("trim",.30,"change");simulate(m,.10)
	check("interruption_fades_instead_of_flashing",f.peak()>0 and f.peak()<intensity,[intensity,f.peak()])
	simulate(m,.5);check("lost_balance_releases_the_field",f.peak()<.01)
	m.stow();simulate(m,12)
	check("settles_and_parks_before_fold",m.settled(),f.diagnostics())
	check("rest_has_no_floating_effects",not m.effect.f_visuals.foil.visible and not m.effect.f_visuals.filament.visible)
	m.play.input("service",-.8,"change");simulate(m,8)
	check("complete_18_part_disassembly",m.explosion>.999 and m.parts.size()==18)
	m.play.input("service",.8,"change");simulate(m,8)
	check("all_parts_reassemble_exactly",m.settled() and m.parts.all(func(p):return p.node.transform.is_equal_approx(p.home)))
	var report:={"all_passed":checks.all(func(c):return c.passed),"checks":checks}
	FileAccess.open(ProjectSettings.globalize_path("res://../review/F_complete/instrument_qa.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	quit(0 if report.all_passed else 2)
