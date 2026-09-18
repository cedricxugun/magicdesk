extends RefCounted
## Normalized reservoir and sonification events, not a full acoustic simulation.
var listening:=false
var pressed:=false
var compression:=0.
var velocity:=0.
var air_mass:=1.
var pressure:=1.
var iris:=0.
var frequency:=.25
var throat:=.7
var gain:=0.
var clock:=0.
var outflow:=0.
var exhaust:=0.
var resonance:=0.
var diaphragm:=0.
var diaphragm_velocity:=0.
var outgoing_count:=0
var echo_count:=0
var stage:="rest"
var _pending_release:=false
var _release_energy:=0.
var _last_outgoing:=-10.
var _last_echo:=-10.
var _echoes:Array=[]
var _events:Array=[]
var _measured_aperture:Array=[]
var _driven_opening:float=-1.
var return_delay_override:float=-1.

func set_driven_opening(opening:float)->void:
	_driven_opening=clampf(opening,0.,1.)

func bind_measured_aperture(profile:Dictionary,component_sha256:String)->void:
	assert(profile.get("component_sha256","")==component_sha256,"Aperture belongs to a different component")
	var samples:Array=profile.get("samples",[])
	assert(samples.size()>=2,"Missing measured aperture samples")
	var previous:=-1.
	for sample in samples:
		assert(float(sample.opening)>previous and float(sample.clear_fraction)>=0. and float(sample.clear_fraction)<=1.)
		previous=float(sample.opening)
	assert(is_zero_approx(float(samples.front().opening)) and is_equal_approx(float(samples.back().opening),1.))
	_measured_aperture=samples.duplicate(true)

func effective_aperture_area(opening:float)->float:
	if _measured_aperture.is_empty():return aperture_area(opening)
	opening=clampf(opening,0.,1.)
	for index in range(1,_measured_aperture.size()):
		var a:Dictionary=_measured_aperture[index-1];var b:Dictionary=_measured_aperture[index]
		if opening<=float(b.opening):
			return lerpf(float(a.clear_fraction),float(b.clear_fraction),(opening-float(a.opening))/(float(b.opening)-float(a.opening)))
	return float(_measured_aperture.back().clear_fraction)

func start()->void:listening=true
func set_controls(tuning:float,opening:float)->void:
	frequency=clampf(tuning,0.,1.);throat=clampf(opening,0.,1.)
func set_pressed(value:bool)->void:
	if value==pressed:return
	if value:
		start();_pending_release=false
	elif listening and pressure>1.006:
		_pending_release=true;_release_energy=maxf(0.,pressure-1.)*compression
	pressed=value
func quiet()->void:
	listening=false;pressed=false;_pending_release=false;_echoes.clear()

static func aperture_area(opening:float)->float:
	# Six-leaf clear hexagon less the fixed center piston.
	var apothem:float=.6*cos(1.05*(1.-clampf(opening,0.,1.)))-.24
	return clampf((2.*sqrt(3.)*apothem*apothem-PI*.095*.095)/(2.*sqrt(3.)*.36*.36-PI*.095*.095),0.,1.)

func tick(delta:float)->void:
	var remaining:float=maxf(0.,delta)
	while remaining>0.0000001:
		var h:float=minf(remaining,1./240.);remaining-=h;_step(h)
	stage="recover" if not listening and not ready_to_close() else "rest" if not listening else "charge" if pressed else "release" if clock-_last_outgoing<.45 else "echo" if clock-_last_echo<.55 else "settling" if absf(velocity)>.02 or absf(pressure-1.)>.02 else "listen"

func _step(h:float)->void:
	clock+=h
	gain=move_toward(gain,1. if listening else 0.,h*2.5)
	var target:float=1. if pressed and listening else 0.
	var acceleration:float=85.*(target-compression)-14.*velocity-1.8*(pressure-1.)
	velocity+=acceleration*h;compression+=velocity*h
	if compression<0.:compression=0.;velocity=maxf(0.,velocity)
	if compression>1.:compression=1.;velocity=minf(0.,velocity)
	var volume:float=1.-.30*compression
	pressure=air_mass/volume
	iris=_driven_opening if _driven_opening>=0. else move_toward(iris,0. if pressed or not listening else throat,h*3.5)
	var area:float=effective_aperture_area(iris)
	var conductance:float=4.*area if listening and not pressed else 0.
	outflow=maxf(0.,pressure-1.)*conductance
	exhaust=maxf(0.,pressure-1.)*12. if not listening else 0.
	var inlet:float=maxf(0.,1.-pressure)*14.
	var leakage:float=(pressure-1.)*.015
	air_mass=maxf(.4,air_mass+(inlet-outflow-exhaust-leakage)*h)
	pressure=air_mass/volume
	var target_frequency:float=.22+.60*sqrt(effective_aperture_area(throat))
	resonance=exp(-pow((frequency-target_frequency)/.16,2.))
	# Slow visible displacement follows delivered flow; audible pitch is sonification.
	diaphragm_velocity+=(outflow*.12-120.*diaphragm-13.*diaphragm_velocity)*h
	diaphragm=clampf(diaphragm+diaphragm_velocity*h,-.012,.012)
	if listening and _pending_release and not pressed and outflow>.02:
		var strength:float=clampf(sqrt(_release_energy/.43),0.,1.)
		_events.append({"kind":"outgoing","time":clock,"gain":strength,"frequency_hz":130.*pow(2.,3.*frequency)})
		outgoing_count+=1;_last_outgoing=clock;_pending_release=false
		var delay:float=return_delay_override if return_delay_override>0. else .45+.55*(1.-throat)
		_echoes.append({"due":clock+delay,"gain":strength*(.12+.40*resonance),"frequency_hz":130.*pow(2.,3.*frequency)})
	if _pending_release and pressure<=1.002:_pending_release=false
	for echo in _echoes.duplicate():
		if listening and clock>=echo.due:
			_events.append({"kind":"return","time":clock,"gain":echo.gain,"frequency_hz":echo.frequency_hz})
			diaphragm_velocity+=float(echo.gain)*.0015
			echo_count+=1;_last_echo=clock;_echoes.erase(echo)

func drain_events()->Array:
	var events:=_events;_events=[];return events
func return_schedule()->Array:
	# Read-only snapshots let the optical packet arrive with the acoustic event.
	return _echoes.duplicate(true)
func ready_to_close()->bool:
	return not listening and gain<.001 and compression<.01 and absf(velocity)<.04 and absf(pressure-1.)<.01 and _echoes.is_empty() and absf(diaphragm)<.00001 and absf(diaphragm_velocity)<.0001
func state()->Dictionary:
	return {"stage":stage,"pressure":pressure,"compression":compression,"velocity":velocity,"iris":iris,"outflow":outflow,"exhaust":exhaust,"resonance":resonance,"diaphragm":diaphragm,"gain":gain,"outgoing":outgoing_count,"returns":echo_count,"pending_returns":_echoes.size(),"ready_to_close":ready_to_close()}
