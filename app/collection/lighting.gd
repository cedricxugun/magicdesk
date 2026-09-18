extends RefCounted
## Per-device light balance, restoring the captured HELIOS calibration exactly.
var env:Environment
var lights:Array=[]
var baseline:Dictionary
var profiles:Dictionary
var active_id:="B"
var amount:=1.
var current:Dictionary
var start:Dictionary
var target:Dictionary
const ENV_FIELDS:=["ssao_radius","ssao_intensity","glow_enabled","glow_intensity","glow_strength","glow_bloom","glow_hdr_threshold","glow_hdr_scale","glow_blend_mode","glow_normalized"]
var panorama:PanoramaSkyMaterial
func setup(host:Node3D)->void:
	env=host.env
	for child in host.get_children():
		if child is AreaLight3D:lights.append(child)
	baseline={"ambient":env.ambient_light_energy,"ssil_radius":env.ssil_radius,"lights":[]}
	baseline["environment"]={};baseline["glow_levels"]=[]
	for field in ENV_FIELDS:baseline.environment[field]=env.get(field)
	for i in range(7):baseline.glow_levels.append(env.get_glow_level(i))
	panorama=env.sky.sky_material as PanoramaSkyMaterial if env.sky else null
	baseline["sky_energy"]=panorama.energy_multiplier if panorama else 1.
	for light in lights:baseline.lights.append({"energy":light.light_energy,"size":light.light_size})
	profiles=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/lighting_profiles.json")).profiles
	current=baseline.duplicate(true);start=current.duplicate(true);target=current.duplicate(true)
func select(id:String)->void:
	if id==active_id:return
	active_id=id;start=current.duplicate(true);target=baseline.duplicate(true);amount=0.
	if profiles.has(id):
		var p:Dictionary=profiles[id];target.ambient=p.ambient;target.ssil_radius=p.ssil_radius
		for i in range(lights.size()):target.lights[i]={"energy":p.light_energy[i],"size":p.light_size}
		for field in p.get("environment",{}):
			assert(field in ENV_FIELDS,"Unsupported lighting property "+field)
			target.environment[field]=p.environment[field]
		if p.has("glow_levels"):target.glow_levels=p.glow_levels.duplicate()
		if p.has("sky_energy"):target.sky_energy=p.sky_energy
func tick(delta:float)->void:
	if amount>=1.:return
	amount=minf(1.,amount+delta/.45);var t:=smoothstep(0.,1.,amount)
	current.ambient=lerpf(start.ambient,target.ambient,t);current.ssil_radius=lerpf(start.ssil_radius,target.ssil_radius,t)
	env.ambient_light_energy=current.ambient;env.ssil_radius=current.ssil_radius
	current.sky_energy=target.sky_energy if amount==1. else lerpf(start.sky_energy,target.sky_energy,t)
	if panorama:panorama.energy_multiplier=current.sky_energy
	for field in ENV_FIELDS:
		var a:Variant=start.environment[field];var b:Variant=target.environment[field]
		current.environment[field]=b if amount==1. else lerpf(float(a),float(b),t) if typeof(a)==TYPE_FLOAT else a
		# Enable before fading in; disable only after fading fully out.
		if field=="glow_enabled" and amount<1.:current.environment[field]=bool(a) or bool(b)
		if field in ["glow_blend_mode","glow_normalized"] and amount<1. and not start.environment.glow_enabled and target.environment.glow_enabled:
			current.environment[field]=b
		if field=="glow_intensity" and amount<1.:
			current.environment[field]=lerpf(float(a) if start.environment.glow_enabled else 0.,float(b) if target.environment.glow_enabled else 0.,t)
		env.set(field,current.environment[field])
	for i in range(7):
		current.glow_levels[i]=target.glow_levels[i] if amount==1. else lerpf(start.glow_levels[i],target.glow_levels[i],t)
		env.set_glow_level(i,current.glow_levels[i])
	for i in range(lights.size()):
		current.lights[i].energy=lerpf(start.lights[i].energy,target.lights[i].energy,t)
		current.lights[i].size=lerpf(start.lights[i].size,target.lights[i].size,t)
		lights[i].light_energy=current.lights[i].energy;lights[i].light_size=current.lights[i].size
