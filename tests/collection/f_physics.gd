extends SceneTree
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(label:String,passed:bool,detail:Variant="")->void:
	checks.append({"check":label,"passed":passed,"detail":str(detail)});print("F_PHYSICS ",label," ",passed," ",detail)
func make()->RefCounted:
	var solver:RefCounted=load("res://collection/f_dynamics.gd").new();solver.release();return solver
func advance(s:RefCounted,seconds:float,fps:float=60)->void:
	for i in range(int(seconds*fps)):s.advance(1.0/fps,0.0)
func run()->void:
	var s:=make();s.shaft_drag=0;s.air_drag=0
	var initial:float=s.energy();var drift:=0.0
	for i in range(1200):s.advance(1.0/60,0);drift=maxf(drift,absf(s.energy()-initial))
	check("unforced_energy_conservation",drift<.0005,drift)
	check("unit_length_pendulum_constraint",absf(s.direction.length()-1.0)<.000001)
	var low:=make();var high:=make();advance(low,8,30);advance(high,8,120)
	check("30_120_fps_same_dynamics",absf(low.theta-high.theta)<.00001 and low.direction.distance_to(high.direction)<.0001,[low.theta,high.theta])
	s=make();s.release(-.7);var before:float=s.energy();advance(s,8)
	check("drag_dissipates_energy",s.energy()<before,[before,s.energy()])
	s=make();s.trim=.75;advance(s,1);var moving:float=absf(s.omega);s.brake=1;advance(s,.5)
	check("friction_brake_catches",absf(s.omega)<.01 and s.heat>0,[moving,s.omega,s.heat])
	var held:float=s.theta;advance(s,1);check("static_brake_holds_torque",absf(s.theta-held)<.0001)
	s.brake=0;advance(s,.4);check("release_restores_gravity_response",absf(s.theta-held)>.01)
	s=make();s.release(-.55);s.direction=Vector3(.25,-1,.18).normalized();var down_before:float=s.direction.dot(Vector3.DOWN);advance(s,12)
	check("plumb_returns_towards_world_gravity",s.direction.dot(Vector3.DOWN)>down_before,[down_before,s.direction])
	s=make()
	for i in range(900):s.advance(1.0/60.0,i*.17/60.0)
	check("yaw_keeps_both_masses_under_world_gravity",s.direction.dot(Vector3.DOWN)>.995 and s.right_direction.dot(Vector3.DOWN)>.995,s.diagnostics())
	s=make();s.gravity=0;s.spring=0;s.shaft_drag=0;s.air_drag=0;var still:float=s.theta;advance(s,3)
	check("no_fake_swing_without_forces",absf(s.theta-still)<.000001 and s.direction_rate.length()<.000001)
	var crossings:Array=[]
	for scale in [1.0,1.2]:
		s=make();s.release(s.REST);s.length_scale=scale;s.brake=1;s.air_drag=0;s.direction=Vector3(.10,-1,0).normalized()
		var elapsed:=0.0
		while s.direction.x>0 and elapsed<1:
			s.advance(1.0/240,0);elapsed+=1.0/240
		crossings.append(elapsed)
	check("visible_length_has_correct_gravity_period",absf(crossings[1]/crossings[0]-sqrt(1.2))<.025,crossings)
	s=make();s.trim=1;advance(s,3);s.parking=true;s.brake=0;s.trim=0;s.polarity=0;advance(s,5)
	check("actuated_transport_can_capture",s.ready_to_transport(),s.diagnostics())
	var report:={"all_passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Reduced-coordinate point masses and massless rigid links; not a manufacturing or finite-element model."}
	FileAccess.open(ProjectSettings.globalize_path("res://../review/F_complete/physics.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	quit(0 if report.all_passed else 2)
