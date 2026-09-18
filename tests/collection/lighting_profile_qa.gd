extends SceneTree
class LightingHost extends Node3D:
	var env:=Environment.new()
func _initialize()->void:
	var host:=LightingHost.new();root.add_child(host);host.env.ambient_light_energy=.5;host.env.ssil_radius=1.
	for energy in [24.,34.,4.]:
		var l:=AreaLight3D.new();l.light_energy=energy;l.light_size=.65;host.add_child(l)
	var controller:RefCounted=load("res://collection/lighting.gd").new();controller.setup(host)
	var baseline:Dictionary=controller.baseline.duplicate(true);var checks:Array=[]
	controller.select("G");controller.tick(1.)
	checks.append({"name":"G_profile_applied","passed":is_equal_approx(host.env.ambient_light_energy,.4) and is_equal_approx(host.get_child(1).light_energy,22.)})
	controller.select("B");controller.tick(.1)
	var before:float=host.get_child(0).light_energy
	controller.select("G")
	checks.append({"name":"interrupted_blend_does_not_snap","passed":is_equal_approx(before,host.get_child(0).light_energy)})
	controller.tick(.07);controller.select("F");controller.tick(1.)
	checks.append({"name":"F_has_independent_light_balance","passed":is_equal_approx(host.env.ambient_light_energy,.35) and is_equal_approx(host.env.ssil_radius,.30) and is_equal_approx(host.get_child(1).light_energy,25.) and is_equal_approx(host.get_child(0).light_size,.35)})
	controller.select("G");controller.tick(1.);controller.select("B");controller.tick(1.)
	checks.append({"name":"B_round_trip_exact","passed":same(controller.current,baseline)})
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks}
	FileAccess.open("res://../review/F_complete/revision_20260911/lighting_profile_qa.json" if OS.get_cmdline_user_args().has("--revision") else "res://../review/G_optical_curator/lighting/profile_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print(JSON.stringify(report));host.free();quit(0 if report.passed else 2)
func same(a:Dictionary,b:Dictionary)->bool:
	if not is_equal_approx(a.ambient,b.ambient) or not is_equal_approx(a.ssil_radius,b.ssil_radius):return false
	for i in range(a.lights.size()):
		if not is_equal_approx(a.lights[i].energy,b.lights[i].energy) or not is_equal_approx(a.lights[i].size,b.lights[i].size):return false
	return true
