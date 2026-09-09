extends SceneTree

var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(name:String,passed:bool,detail:Variant="")->void:
	checks.append({"check":name,"passed":passed,"detail":str(detail)});print("GESTURE_CHECK ",name," ",passed)
func simulate(module:Node3D,seconds:float)->void:
	for i in range(int(seconds*60)):module.tick(1.0/60.0,1.0)

func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(5):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false)
	check("collection_available_on_this_platform",host.collection!=null)
	var registry:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/registry.json"))
	for definition in registry.models:
		if definition.id=="B":continue
		var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(definition.metadata))
		var module:Node3D=load("res://collection/module.gd").new();host.add_child(module)
		module.setup(host,data,load(definition.scene))
		if definition.id!="F":module.openness=1.0;module.open_target=1.0
		var play:RefCounted=module.play
		match str(definition.id):
			"F":
				var gear_before:Transform3D=module.named("F2_MainGear").transform
				var carriage_before:Vector3=module.named("F2_TrimCarriage").position
				play.input("trim",.8,"begin");simulate(module,4.0)
				check("F_authored_gear_driven",not module.named("F2_MainGear").transform.is_equal_approx(gear_before))
				check("F_carriage_moves_on_authored_rail",module.named("F2_TrimCarriage").position.distance_to(carriage_before)>.1)
				var jaw_before:float=module.named("F2_BrakePad-1").position.x
				play.input("brake",1.0,"begin");simulate(module,.35)
				check("F_caliper_closes_without_overshoot",module.named("F2_BrakePad-1").position.x>jaw_before and module.named("F2_BrakePad-1").position.x-jaw_before<.015)
				check("F_friction_brake_holds_linkage",absf(float(play.response.velocity))<.006,play.response)
				var positive:float=play.instrument.physics.theta
				play.input("brake",0.0,"release");check("F_release_brake",play.number("brake")==0.0)
				play.input("trim",-.8,"change");simulate(module,4.0)
				check("F_preload_changes_physical_equilibrium",play.instrument.physics.theta<positive)
				play.input("service",-.8,"change");simulate(module,9.0)
				check("F_service_explodes_refined_parts",module.explosion>.999 and module.parts.size()==18)
				play.input("service",.8,"change");simulate(module,9.0)
				check("F_service_returns_every_part_home",module.settled() and module.parts.all(func(p):return p.node.transform.is_equal_approx(p.home)))
			"G":
				play.input("leaf",2.0,"begin");play.input("fold",0.0,"change");simulate(module,.5)
				check("G_selected_leaf_angle_changes",play.pose_fraction("G_C_PageHinge2",1.0)<play.pose_fraction("G_C_PageHinge1",1.0))
				play.input("imprint",1.0,"begin");simulate(module,.5);check("G_hold_imprints",float(play.response.imprint)>.5)
				play.input("imprint",0.0,"release");simulate(module,.6);check("G_release_stops_imprint",float(play.response.imprint)<.1)
			"I":
				play.input("bellows",1.0,"begin");simulate(module,1.0);check("I_hold_builds_pressure",float(play.response.pressure)>.4)
				play.input("bellows",0.0,"release");check("I_release_emits_echo",float(play.response.echo)>.4 and float(play.response.pressure)==0.0)
			"J":
				play.input("branch",2.0,"begin");play.input("feed",1.0,"change");simulate(module,.5)
				check("J_pump_routes_to_selected_bud",float(play.response.growth[2])>float(play.response.growth[0])+.4)
			"K":
				play.input("feed",.25,"begin");check("K_feed_without_contact_no_ink",float(play.response.ink)==0.0)
				play.input("stylus",1.0,"begin");play.input("feed",.50,"change");simulate(module,.5)
				check("K_crank_with_contact_writes",float(play.response.ink)>.4)
				play.input("stylus",1.0,"release");play.input("feed",.6,"change");check("K_latched_needle_allows_one_pointer_crank",float(play.response.ink)>.6)
				play.input("stylus",0.0,"change");var ink:float=play.response.ink;play.input("feed",.75,"change")
				check("K_raise_needle_stops_writing",is_equal_approx(ink,float(play.response.ink)))
			"L":
				play.input("focus",.64,"begin");play.input("aim",Vector2(.5,.5),"change");simulate(module,1.0)
				check("L_two_axis_aim_changes_target",(play.response.aim as Vector2).length()>.15)
				check("L_focus_converges",float(play.response.focus_quality)>.95)
			"M":
				play.input("orbit",1.8,"begin");play.input("gravity",1.0,"change");simulate(module,2.0)
				check("M_orbit_wheel_controls_rate",is_equal_approx(module.effect.orbit_speed,1.8))
				check("M_gravity_drives_infall",float(play.response.capture_age)>2.0 and module.effect.worlds.size()==3)
				play.input("reseed",1.0,"change");simulate(module,.2);check("M_crank_reconstructs_same_worlds",module.effect.reseed_age>0 and module.effect.worlds.size()==3)
			"N":
				play.input("bridge",1.0,"begin");play.input("probe",.8,"change");simulate(module,.5)
				check("N_unaligned_probe_meets_stop",float(play.response.probe_target)<=.14)
				play.input("phase",.5,"change");simulate(module,1.0)
				check("N_aligned_probe_follows_slider",module.effect.probe_t>.7)
		module.queue_free();await process_frame
	var report:={"all_passed":checks.all(func(c):return c.passed),"checks":checks,"visual_acceptance":false}
	var output:=ProjectSettings.globalize_path("res://../tests/collection/gesture_logic_report.json")
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	scene.queue_free();await process_frame;await process_frame
	quit(0 if report.all_passed else 2)
