extends RefCounted
## Operational state and earned resonance, driven by the physical mechanism.
var module:Node3D
var physics:RefCounted
var preload_value:=0.0
var coherence:=0.0
var charge:=0.0
var peak_time:=-1.0
var peak_latched:=false
var release_time:=-1.0
var braking_heat:=0.0
var previous_heat:=0.0
var stage:="rest"
var peak_count:=0
var travel_latch:=1.0
var aborting:=false
var abort_gain:=1.0
var disruption:=0.0

func setup(owner:Node3D)->void:
	module=owner;physics=load("res://collection/f_dynamics.gd").new();physics.transport(0,0,10)
	physics.length_scale=float(module.data.get("display_calibration",{}).get("scale",1.0))

func changed(key:String,before:Variant,value:Variant,event:String)->void:
	if event in ["begin","change","release"] and key in ["trim","polarity","brake"]:
		if event=="begin":peak_latched=false;charge=0
		if absf(float(value)-float(before))>.000001:
			peak_latched=false;charge=0
			if peak_time>=0:aborting=true

func tick(delta:float)->void:
	var parking:bool=module.stowing or module.open_target<.001
	preload_value=move_toward(preload_value,0.0 if parking else module.play.number("trim"),delta*.85)
	physics.trim=preload_value;physics.brake=0.0 if parking else module.play.number("brake")
	physics.polarity=0.0 if parking else module.play.number("polarity")
	physics.parking=parking
	if module.openness>.999 and module.explosion<.001:
		if not physics.free:
			physics.release(physics.theta,module.rotation.y);release_time=0;peak_latched=false;charge=0
		physics.advance(delta,module.rotation.y)
	else:
		physics.transport(module.openness,module.rotation.y,delta,parking)
		charge=move_toward(charge,0,delta*2)
		if module.openness<.02:peak_time=-1;release_time=-1;peak_latched=false
	travel_latch=move_toward(travel_latch,1.0 if parking or module.openness<.999 else 0.0,delta*3.5)
	braking_heat=maxf(0,braking_heat-delta*.65)+maxf(0,physics.heat-previous_heat)*4.0
	previous_heat=physics.heat
	braking_heat=minf(braking_heat,1.0)
	if release_time>=0:release_time+=delta
	if peak_time>=0:
		peak_time+=delta
		if peak_time>5.5:peak_time=-1
	abort_gain=move_toward(abort_gain,0.0 if aborting else 1.0,delta*2.3)
	var angle_error:float=absf(physics.theta-physics.REST)
	var speed:float=maxf(physics.direction_rate.length(),physics.right_rate.length())
	var vertical:float=minf(physics.direction.dot(Vector3.DOWN),physics.right_direction.dot(Vector3.DOWN))
	coherence=(1.0-smoothstep(.020,.075,angle_error))*(1.0-smoothstep(.06,.25,absf(physics.omega)))
	coherence*=(1.0-smoothstep(.12,.50,speed))*smoothstep(.982,.997,vertical)
	coherence*=1.0-physics.brake
	if parking or module.openness<.999 or module.explosion>.001:coherence=0
	var manipulating:bool=module.host.collection!=null and module.host.collection.current==module and module.host.collection.control_driver.index>=0
	if coherence>.70 and not peak_latched and not manipulating:charge=minf(1,charge+delta*coherence/1.45)
	else:charge=move_toward(charge,0,delta*1.5)
	if charge>=1.0 and not peak_latched:
		peak_latched=true;peak_time=0;peak_count+=1
		aborting=false;abort_gain=1.0;disruption=0
	if parking:
		charge=0
		if peak_time>=0:aborting=true
	if peak_time>=0:
		disruption=disruption+delta if coherence<.35 else 0.0
		if disruption>.20:aborting=true
	stage="recover" if parking and module.openness>.01 else "rest" if module.openness<.01 else "release" if module.openness<.999 or release_time<1.0 else "equilibrium" if peak_time>=0 else "brake" if physics.brake>.5 else "bias" if coherence<.7 else "settling"

func ready_to_fold()->bool:
	return not physics.free or physics.ready_to_transport()

func peak()->float:
	if peak_time<0:return 0
	return smoothstep(0.0,.85,peak_time)*(1.0-smoothstep(3.0,5.5,peak_time))*abort_gain

func crest()->float:
	if peak_time<0:return 0
	return exp(-pow((peak_time-1.55)/.50,2.0))*abort_gain

func release_flash()->float:
	return exp(-pow((release_time-.3)/.36,2.0)) if release_time>=0 and release_time<1.5 else 0.0

func diagnostics()->Dictionary:
	return {"stage":stage,"coherence":coherence,"charge":charge,"peak_time":peak_time,"peak_count":peak_count,"heat":braking_heat,"preload_value":preload_value,"physics":physics.diagnostics()}
