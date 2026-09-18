extends SceneTree
class Host extends Node3D:
	var env:=Environment.new()
func _initialize()->void:
	var host:=Host.new();root.add_child(host)
	host.env.sky=Sky.new();host.env.sky.sky_material=PanoramaSkyMaterial.new();host.env.sky.sky_material.energy_multiplier=.32
	host.env.ambient_light_energy=.5;host.env.ssil_radius=1.;host.env.ssao_radius=.12;host.env.ssao_intensity=1.4;host.env.glow_enabled=false
	for energy in [24.,34.,4.]:
		var light:=AreaLight3D.new();host.add_child(light);light.light_energy=energy;light.light_size=.65
	var driver:RefCounted=load("res://collection/lighting.gd").new();driver.setup(host)
	driver.profiles["I"]=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/desktop_optics_r60/lighting_candidate.json"))
	var baseline:Dictionary=driver.baseline.duplicate(true);var checks:Array=[]
	var actual_profile:Dictionary=driver.profiles["I"].duplicate(true)
	driver.profiles["I"].environment.glow_enabled=true
	driver.select("I");driver.tick(.001)
	assert(host.env.glow_enabled and host.env.glow_blend_mode==Environment.GLOW_BLEND_MODE_ADDITIVE,"Glow mode must be set while fading in, not jump at the end")
	driver.select("B");driver.tick(1.)
	driver.profiles["I"]=actual_profile
	for target in ["I","B","F","I","G","B"]:
		driver.select(target);driver.tick(.12)
		var before:Dictionary=driver.current.duplicate(true)
		driver.select("I" if target!="I" else "B")
		assert(driver.current==before,"Interrupted selection changed light immediately")
		driver.tick(.07);driver.select(target);driver.tick(1.)
		if target=="B":assert(driver.current==baseline)
		if target=="I":assert(host.env.glow_enabled==actual_profile.environment.glow_enabled and host.env.glow_blend_mode==Environment.GLOW_BLEND_MODE_ADDITIVE and is_equal_approx(host.env.ssao_intensity,.55) and is_equal_approx(host.env.sky.sky_material.energy_multiplier,.30))
		checks.append({"target":target,"state":driver.current.duplicate(true)})
	var end:RefCounted=load("res://collection/lighting.gd").new();end.setup(host)
	assert(end.baseline==baseline,"Actual environment/light properties did not restore")
	FileAccess.open("res://../review/I_refinement/nautilus_r1/desktop_optics_r60/lighting_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"checks":checks,"scope":"I/B/F/G interrupted blending and exact recapture of Environment, panorama energy and three area light energies/sizes."},"  "))
	print("I_LIGHTING_RESTORE true");host.free();quit()
