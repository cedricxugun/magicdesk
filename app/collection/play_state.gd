extends RefCounted
## Device-specific, reversible control responses over the authored mechanism.
## This is an interaction prototype; the revised art is tracked independently.

var module:Node3D
var active:=false
var gain:=0.0
var instrument:RefCounted
var g_instrument:RefCounted
var values:Dictionary={}
var response:Dictionary={"angle":.22,"velocity":0.0,"balance":0.0,"pressure":0.0,"echo":0.0,"echo_delay":-1.0,"imprint":0.0,"growth":[.15,.15,.15],"ink":0.0,"feed_motion":0.0,"aim":Vector2.ZERO,"focus_quality":0.0,"capture_age":-1.0,"captured_floor":0.0,"rebuild":-1.0,"probe_target":0.0}

func setup(owner:Node3D)->void:
	module=owner
	var profiles:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/control_profiles.json")).models
	for item in profiles.get(str(module.data.id),[]):
		values[item.key]=Vector2(item.default[0],item.default[1]) if item.default is Array else float(item.default)
	if module.data.id=="F" and module.data.has("f_physics"):
		instrument=load("res://collection/f_instrument.gd").new();instrument.setup(module)
	if module.data.id=="G" and module.data.has("g_mechanism"):
		g_instrument=load("res://collection/g_instrument.gd").new();g_instrument.setup(module)

func value(key:String)->Variant:return values.get(key,0.0)
func number(key:String)->float:return float(values.get(key,0.0))

func input(key:String,requested:Variant,event:String)->void:
	var before:Variant=values.get(key,0.0)
	values[key]=requested
	if instrument:instrument.changed(key,before,requested,event)
	if g_instrument:g_instrument.changed(key,before,requested,event)
	if event=="cancel":return
	if key=="service":
		if event=="change" and float(requested)<-.55 and float(before)>=-.55:module.activate(3)
		elif event=="change" and float(requested)>.55 and float(before)<=.55:module.stow()
		return
	active=true
	if event=="begin":
		module.stowing=false;module.explode_target=0.0;module.host.power_target=1.0
		if module.data.id!="N":module.open_target=1.0;module.effect.resume()
	match str(module.data.id):
		"I":
			if key=="bellows" and event=="release":
				response.echo=maxf(.12,float(response.pressure));response.pressure=0.0;response.echo_delay=.4+number("throat")*.8
		"J":
			if key=="feed" and event=="change":
				var branch:=clampi(int(round(number("branch"))),0,2)
				response.growth[branch]=clampf(float(response.growth[branch])+maxf(0.0,float(requested)-float(before))*.65,0,1)
		"K":
			if key=="feed":
				response.feed_motion=absf(float(requested)-float(before))
				if number("stylus")>.5:response.ink=clampf(float(response.ink)+float(response.feed_motion)*2.0,0,1)
		"M":
			if key=="reseed" and event=="change":
				response.rebuild=maxf(0.0,float(response.rebuild))+absf(float(requested)-float(before))*1.8
				response.capture_age=-1.0;response.captured_floor=0.0;values.gravity=0.0
		"N":
			if key=="bridge":
				if float(requested)>.5:module.stowing=false;module.open_target=1.0;module.effect.resume()
				else:module.stow()

func tick(delta:float)->void:
	if g_instrument:
		g_instrument.tick(delta);gain=module.openness;response.imprint=g_instrument.records[g_instrument.selected];return
	if instrument:
		instrument.tick(delta)
		gain=move_toward(gain,1.0 if module.openness>.99 and not module.stowing else 0.0,delta*2.5)
		response.angle=instrument.physics.theta-instrument.physics.REST;response.velocity=instrument.physics.omega;response.balance=instrument.coherence
		return
	var ready:bool=active and not module.stowing and module.explode_target<.001 and module.explosion<.001 and module.open_target>.01
	gain=move_toward(gain,1.0 if ready else 0.0,delta*2.5)
	response.echo=maxf(0.0,float(response.echo)-delta*.55)
	response.feed_motion=move_toward(float(response.feed_motion),0.0,delta*.3)
	if not ready:return
	match str(module.data.id):
		"F":
			var angle:=float(response.angle);var velocity:=float(response.velocity)
			var target:=number("trim")*.55*number("polarity")
			velocity+=(target-angle)*delta*8.0
			velocity*=exp(-delta*(.85+number("brake")*18.0))
			angle=clampf(angle+velocity*delta,-.7,.7)
			response.angle=angle;response.velocity=velocity
			response.balance=(1.0-smoothstep(.035,.28,absf(angle)))*(1.0-smoothstep(.04,.5,absf(velocity)))
		"G":response.imprint=move_toward(float(response.imprint),number("imprint"),delta*1.4)
		"I":
			if number("bellows")>.5:response.pressure=minf(1.0,float(response.pressure)+delta*.45)
			if float(response.echo_delay)>=0:
				response.echo_delay-=delta
				if float(response.echo_delay)<0:response.echo=maxf(float(response.echo),1.0-absf(number("frequency")-.62)*1.5)
		"J":
			for i in range(3):response.growth[i]=move_toward(float(response.growth[i]),.05,delta*.008*(1.0-number("light")))
		"L":
			var steer:Vector2=values.aim
			response.aim=(response.aim as Vector2)+steer*delta*.35
			response.aim=Vector2(clampf(response.aim.x,-.38,.38),clampf(response.aim.y,-.24,.24))
			response.focus_quality=1.0-smoothstep(.035,.34,absf(number("focus")-.64))
		"M":
			if float(response.rebuild)>=0:
				if float(response.rebuild)>3.2:response.rebuild=-1.0
			else:
				var gravity:=number("gravity")
				if gravity>.35 and float(response.capture_age)<0:response.capture_age=0.0
				if float(response.capture_age)>=0:
					response.capture_age=clampf(float(response.capture_age)+delta*(gravity-.35)*2.8,float(response.captured_floor),7.2)
					for threshold in [3.1,4.8,6.5]:
						if float(response.capture_age)>=threshold:response.captured_floor=maxf(float(response.captured_floor),threshold)
		"N":
			var aligned:=1.0-smoothstep(.06,.30,absf(number("phase")-.5))
			response.focus_quality=aligned
			response.probe_target=minf(number("probe"),.14 if aligned<.8 else 1.0)

func pose_fraction(name:String,base:float)->float:
	if g_instrument:return base
	if instrument:return base
	if gain<=.001:return base
	var desired:=base
	match str(module.data.id):
		"F":desired=base*clampf(.65+.28*number("trim")+.10*float(response.angle),.25,1.0)
		"G":
			var leaf:=str(clampi(int(round(number("leaf"))),0,5))
			if name.begins_with("G_C_PageHinge"+leaf) or name.begins_with("G_C_PageSupport"+leaf):desired=base*(.70+.30*number("fold"))
		"I":
			if name=="I_C_Throat":desired=base*(.2+.8*number("throat"))
		"J":
			for i in range(3):
				if name.begins_with("J_C_BudPetal"+str(i)+"_"):desired=base*float(response.growth[i])
	return lerpf(base,desired,gain)

func motion_angle(name:String,fallback:float)->float:
	if instrument:return (instrument.coherence-.5)*1.45
	if gain<=.001:return fallback
	var target:=fallback
	if module.data.id=="F":target=float(response.angle) if name.contains("PearlSwing") else -number("trim")*.7
	elif module.data.id=="I":target=(number("frequency")-.5)*1.5
	elif module.data.id=="K":target=number("feed")*TAU*(-1 if name.ends_with("-1") else 1) if name.contains("Reel") else number("stylus")*.7
	return lerpf(fallback,target,gain)

func diagnostics()->Dictionary:
	if g_instrument:return {"active":active,"values":values.duplicate(),"gain":gain,"g_instrument":g_instrument.diagnostics()}
	if instrument:return {"active":active,"values":values.duplicate(),"response":response.duplicate(true),"gain":gain,"instrument":instrument.diagnostics()}
	return {"active":active,"values":values.duplicate(),"response":response.duplicate(true),"gain":gain,"art_status":"interaction prototype; revised geometry pending per-device art review"}

func gauge_value()->float:
	if g_instrument:return g_instrument.alignment
	match str(module.data.id):
		"F":return float(response.balance)
		"G":return float(response.imprint)
		"I":return maxf(float(response.pressure),float(response.echo))
		"J":return float(response.growth[clampi(int(number("branch")),0,2)])
		"K":return float(response.ink)
		"L","N":return float(response.focus_quality)
		"M":return 1.0-number("gravity")*.7
	return 0.0
